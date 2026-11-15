"""Generate the onboarding table from each customer's tenure, story, and subscription outcome."""

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta

from .constants import (
    CANCELLED_EARLY_MONTHS_THRESHOLD,
    FIRST_VALUE_WEEKS_RANGE,
    FIRST_VALUE_WEEKS_RANGE_LOW_ADOPTION,
    GO_LIVE_WEEKS_RANGE,
    KICKOFF_DAYS_RANGE,
    STALL_BASE_PROBABILITY,
    STALL_CANCELLED_EARLY_BONUS,
    STALL_RECENT_BONUS,
    STALL_RECENT_TENURE_MONTHS,
)
from .dates import REFERENCE, tenure_months


def _had_early_cancellation(customer_subscriptions: pd.DataFrame, start_date) -> bool:
    cancelled = customer_subscriptions[customer_subscriptions["status"] == "cancelled"]
    for end_date in cancelled["end_date"]:
        delta = relativedelta(end_date, start_date)
        if delta.years * 12 + delta.months <= CANCELLED_EARLY_MONTHS_THRESHOLD:
            return True
    return False


def _stall_probability(story: str, tenure: int, cancelled_early: bool, kickoff_date: pd.Timestamp) -> float:
    _, go_live_high = GO_LIVE_WEEKS_RANGE
    time_eligible = kickoff_date + pd.Timedelta(weeks=go_live_high) <= REFERENCE
    reason_eligible = tenure < STALL_RECENT_TENURE_MONTHS or cancelled_early

    if story == "healthy" or not time_eligible or not reason_eligible:
        return 0.0

    p = STALL_BASE_PROBABILITY[story]
    if cancelled_early:
        p += STALL_CANCELLED_EARLY_BONUS
    if tenure < STALL_RECENT_TENURE_MONTHS:
        p += STALL_RECENT_BONUS
    return min(p, 0.9)


def _onboarding_row(rng: np.random.Generator, story: str, start_date, cancelled_early: bool) -> dict:
    tenure = tenure_months(start_date)

    kickoff_low, kickoff_high = KICKOFF_DAYS_RANGE
    kickoff_date = pd.Timestamp(start_date) + pd.Timedelta(days=int(rng.integers(kickoff_low, kickoff_high + 1)))

    stall_probability = _stall_probability(story, tenure, cancelled_early, kickoff_date)
    if rng.random() < stall_probability:
        return {"kickoff_date": kickoff_date, "go_live_date": None, "first_value_date": None, "status": "stalled"}

    go_live_low, go_live_high = GO_LIVE_WEEKS_RANGE
    go_live_date = kickoff_date + pd.Timedelta(weeks=int(rng.integers(go_live_low, go_live_high + 1)))
    if go_live_date > REFERENCE:
        return {"kickoff_date": kickoff_date, "go_live_date": None, "first_value_date": None, "status": "in_progress"}

    if story == "low_adoption":
        fv_low, fv_high = FIRST_VALUE_WEEKS_RANGE_LOW_ADOPTION
    else:
        fv_low, fv_high = FIRST_VALUE_WEEKS_RANGE
    first_value_date = go_live_date + pd.Timedelta(weeks=int(rng.integers(fv_low, fv_high + 1)))
    if first_value_date > REFERENCE:
        first_value_date = None

    return {"kickoff_date": kickoff_date, "go_live_date": go_live_date, "first_value_date": first_value_date, "status": "live"}


def generate_onboarding(
    rng: np.random.Generator, customers_df: pd.DataFrame, internal_df: pd.DataFrame, subscriptions_df: pd.DataFrame
) -> pd.DataFrame:
    """Generate the onboarding table: one row per customer."""
    internal = internal_df.set_index("customer_id")
    customers = customers_df.set_index("customer_id")
    subscriptions_by_customer = subscriptions_df.groupby("customer_id")

    rows = []
    for customer_id in customers_df["customer_id"]:
        story = internal.loc[customer_id, "story"]
        start_date = customers.loc[customer_id, "customer_since"]
        customer_subscriptions = subscriptions_by_customer.get_group(customer_id)
        cancelled_early = _had_early_cancellation(customer_subscriptions, start_date)

        row = _onboarding_row(rng, story, start_date, cancelled_early)
        row["customer_id"] = customer_id
        rows.append(row)

    onboarding_df = pd.DataFrame(rows)
    for col in ("kickoff_date", "go_live_date", "first_value_date"):
        onboarding_df[col] = pd.to_datetime(onboarding_df[col]).dt.date
    return onboarding_df[["customer_id", "kickoff_date", "go_live_date", "first_value_date", "status"]]
