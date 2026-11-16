"""Generate the usage table: one row per customer per day, customer_since to window_end."""

import numpy as np
import pandas as pd

from .constants import (
    BOOKINGS_CREATED_TYPE_FACTOR,
    CHAMPION_LOSS_ACTIVE_USERS_AFTER,
    CHAMPION_LOSS_METRIC_FACTOR,
    CHAMPION_LOSS_TRANSITION_DAYS,
    LOW_ADOPTION_BOOKINGS_FACTOR,
    LOW_ADOPTION_SHIFTS_ZERO_SHARE,
    LOW_ENGAGEMENT_DECLINE_FLOOR,
    POS_TRANSACTIONS_RANGE_BY_SIZE,
    PRE_GOLIVE_USAGE_FACTOR,
    SEASON_FACTOR_BY_MONTH,
    SHIFTS_PLANNED_THURSDAY_MEAN_BY_SIZE,
    USAGE_BASELINE_BY_SIZE,
    WEEKEND_FACTOR,
)


def _season_and_weekday_factors(dates: pd.DatetimeIndex, monday_closed: bool):
    season = np.array([SEASON_FACTOR_BY_MONTH[m] for m in dates.month])
    dow = dates.dayofweek.to_numpy()
    weekday_factor = np.where((dow == 4) | (dow == 5), WEEKEND_FACTOR, 1.0)
    if monday_closed:
        weekday_factor = weekday_factor.copy()
        weekday_factor[dow == 0] = 0.0
    return season, weekday_factor, dow


def _golive_factor(dates: pd.DatetimeIndex, go_live_date) -> np.ndarray:
    if go_live_date is None or pd.isna(go_live_date):
        return np.full(len(dates), PRE_GOLIVE_USAGE_FACTOR)
    return np.where(dates < pd.Timestamp(go_live_date), PRE_GOLIVE_USAGE_FACTOR, 1.0)


def _story_factor(dates: pd.DatetimeIndex, story: str, window_end, champion_loss_event_date, low_engagement_decline_start) -> np.ndarray:
    """Factor applied to logins, bookings_created, and shifts_planned (not pos_transactions)."""
    n = len(dates)
    if story == "low_engagement" and low_engagement_decline_start is not None:
        decline_start = low_engagement_decline_start
        total = (window_end - decline_start).total_seconds()
        progress = np.clip((dates - decline_start).total_seconds() / total, 0.0, 1.0) if total > 0 else np.zeros(n)
        progress = np.where(dates < decline_start, 0.0, progress)
        return 1.0 - (1.0 - LOW_ENGAGEMENT_DECLINE_FLOOR) * progress
    if story == "champion_loss" and champion_loss_event_date is not None:
        transition_end = champion_loss_event_date + pd.Timedelta(days=CHAMPION_LOSS_TRANSITION_DAYS)
        return np.where(dates >= transition_end, CHAMPION_LOSS_METRIC_FACTOR, 1.0)
    return np.ones(n)


def _customer_usage(
    rng: np.random.Generator,
    customer_id: int,
    customer_type: str,
    size: str,
    story: str,
    start_date,
    go_live_date,
    window_end,
    champion_loss_event_date,
    low_engagement_decline_start,
    monday_closed: bool,
) -> pd.DataFrame:
    dates = pd.date_range(start_date, window_end, freq="D")
    n = len(dates)

    season, weekday_factor, dow = _season_and_weekday_factors(dates, monday_closed)
    golive = _golive_factor(dates, go_live_date)
    story_factor = _story_factor(dates, story, window_end, champion_loss_event_date, low_engagement_decline_start)

    baseline = USAGE_BASELINE_BY_SIZE[size]

    logins_lambda = baseline["logins"] * season * weekday_factor * golive * story_factor
    logins = rng.poisson(np.clip(logins_lambda, 0, None))

    active_lambda = baseline["active_users"] * season * weekday_factor * golive * story_factor
    active_users = rng.poisson(np.clip(active_lambda, 0, None))
    if story == "champion_loss" and champion_loss_event_date is not None:
        after_event = dates >= champion_loss_event_date
        open_day = weekday_factor > 0
        champion_active = np.where(open_day, CHAMPION_LOSS_ACTIVE_USERS_AFTER, 0)
        active_users = np.where(after_event, champion_active, active_users)

    # every active user logged in at least once
    logins = np.maximum(logins, active_users)

    if customer_type == "hotel":
        pos_transactions = np.zeros(n, dtype=int)
    else:
        low, high = POS_TRANSACTIONS_RANGE_BY_SIZE[size]
        pos_baseline = rng.uniform(low, high)
        # keeps running regardless of story, but still needs go-live: before that, the
        # restaurant is still on its old POS, and a never-live customer has no POS data in our system
        pos_lambda = pos_baseline * season * weekday_factor * golive
        pos_transactions = rng.poisson(np.clip(pos_lambda, 0, None))

    bookings_factor = LOW_ADOPTION_BOOKINGS_FACTOR if story == "low_adoption" else 1.0
    bookings_lambda = (
        baseline["bookings_created"] * BOOKINGS_CREATED_TYPE_FACTOR[customer_type] * season * weekday_factor * golive * story_factor * bookings_factor
    )
    bookings_created = rng.poisson(np.clip(bookings_lambda, 0, None))

    shifts_planned = np.zeros(n, dtype=int)
    thursday_mask = dow == 3
    shifts_lambda = SHIFTS_PLANNED_THURSDAY_MEAN_BY_SIZE[size] * season * golive * story_factor
    shifts_planned[thursday_mask] = rng.poisson(np.clip(shifts_lambda[thursday_mask], 0, None))
    if story == "low_adoption":
        zero_out = thursday_mask & (rng.random(n) < LOW_ADOPTION_SHIFTS_ZERO_SHARE)
        shifts_planned[zero_out] = 0

    return pd.DataFrame(
        {
            "customer_id": customer_id,
            "usage_date": dates.date,
            "logins": logins,
            "active_users": active_users,
            "pos_transactions": pos_transactions,
            "bookings_created": bookings_created,
            "shifts_planned": shifts_planned,
        }
    )


def generate_usage(
    rng: np.random.Generator,
    customers_df: pd.DataFrame,
    internal_df: pd.DataFrame,
    onboarding_df: pd.DataFrame,
    signals_df: pd.DataFrame,
) -> pd.DataFrame:
    """Generate the usage table: one row per customer per day."""
    internal = internal_df.set_index("customer_id")
    customers = customers_df.set_index("customer_id")
    onboarding = onboarding_df.set_index("customer_id")
    signals = signals_df.set_index("customer_id")

    frames = []
    for customer_id in customers_df["customer_id"]:
        frames.append(
            _customer_usage(
                rng,
                customer_id,
                customers.loc[customer_id, "type"],
                internal.loc[customer_id, "size"],
                internal.loc[customer_id, "story"],
                customers.loc[customer_id, "customer_since"],
                onboarding.loc[customer_id, "go_live_date"],
                signals.loc[customer_id, "window_end"],
                signals.loc[customer_id, "champion_loss_event_date"],
                signals.loc[customer_id, "low_engagement_decline_start"],
                signals.loc[customer_id, "monday_closed"],
            )
        )

    return pd.concat(frames, ignore_index=True)
