"""Per-customer values shared across usage.py, tickets.py, and surveys.py.

Computed once so these three files stay consistent instead of each rolling
their own random numbers for the same underlying event.
"""

from dateutil.relativedelta import relativedelta
import numpy as np
import pandas as pd

from .constants import (
    CHAMPION_LOSS_EVENT_PROGRESS_RANGE,
    LOW_ENGAGEMENT_DECLINE_MONTHS_RANGE,
    RESTAURANT_MONDAY_CLOSED_SHARE,
)
from .dates import REFERENCE


def generate_signals(rng: np.random.Generator, customers_df: pd.DataFrame, internal_df: pd.DataFrame, subscriptions_df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame with customer_id, window_end, champion_loss_event_date,
    low_engagement_decline_start, monday_closed."""
    internal = internal_df.set_index("customer_id")
    customers = customers_df.set_index("customer_id")
    cancelled_end_dates = (
        subscriptions_df[subscriptions_df["status"] == "cancelled"]
        .groupby("customer_id")["end_date"]
        .max()
    )

    rows = []
    for customer_id in customers_df["customer_id"]:
        story = internal.loc[customer_id, "story"]
        customer_type = customers.loc[customer_id, "type"]
        start_date = pd.Timestamp(customers.loc[customer_id, "customer_since"])

        cancel_date = cancelled_end_dates.get(customer_id)
        window_end = pd.Timestamp(cancel_date) if cancel_date is not None else REFERENCE

        champion_loss_event_date = None
        if story == "champion_loss":
            low, high = CHAMPION_LOSS_EVENT_PROGRESS_RANGE
            progress = rng.uniform(low, high)
            champion_loss_event_date = start_date + (window_end - start_date) * progress

        low_engagement_decline_start = None
        if story == "low_engagement":
            low, high = LOW_ENGAGEMENT_DECLINE_MONTHS_RANGE
            decline_months = int(rng.integers(low, high + 1))
            low_engagement_decline_start = window_end - relativedelta(months=decline_months)

        monday_closed = customer_type == "restaurant" and rng.random() < RESTAURANT_MONDAY_CLOSED_SHARE

        rows.append(
            {
                "customer_id": customer_id,
                "window_end": window_end,
                "champion_loss_event_date": champion_loss_event_date,
                "low_engagement_decline_start": low_engagement_decline_start,
                "monday_closed": monday_closed,
            }
        )

    return pd.DataFrame(rows)
