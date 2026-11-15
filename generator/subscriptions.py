"""Generate the subscriptions table from each customer's size, type, and hidden story."""

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta

from .constants import (
    CANCEL_AFTER_DOWNGRADE_MONTHS_RANGE,
    CANCEL_MONTHS_RANGE,
    CHURN_CANCELLED_SHARE,
    DOWNGRADE_MONTHS_RANGE,
    MIN_TENURE_MONTHS_FOR_CANCEL,
    MRR_RANGES,
    PLAN_DOWNGRADE,
    PLAN_PROBABILITIES,
    MRR_FACTOR_BY_TYPE,
    PLAN_UPGRADE,
    UPGRADE_MONTHS_RANGE,
    UPGRADE_SHARE,
)
from .dates import REFERENCE, tenure_months


def _add_months_with_jitter(start_date, rng: np.random.Generator, months_low: int, months_high: int) -> pd.Timestamp:
    months = int(rng.integers(months_low, months_high + 1))
    base = pd.Timestamp(start_date) + relativedelta(months=months)
    return base + pd.Timedelta(days=int(rng.integers(0, 28)))


def _draw_mrr(rng: np.random.Generator, plan: str, size: str, customer_type: str) -> float:
    low, high = MRR_RANGES[plan][size]
    mrr = rng.uniform(low, high)
    mrr *= MRR_FACTOR_BY_TYPE[customer_type]
    return round(mrr, 2)


def _cancel_date_if_eligible(rng: np.random.Generator, start_date, min_date: pd.Timestamp | None = None):
    """Decide if a churn-story customer has already cancelled, and if so, when.

    A cancellation can never be dated after REFERENCE_DATE — it simply
    hasn't happened yet, so the customer stays active (at risk) instead.
    """
    tenure = tenure_months(start_date)
    if tenure < MIN_TENURE_MONTHS_FOR_CANCEL:
        return None
    if rng.random() >= CHURN_CANCELLED_SHARE:
        return None

    low, high = CANCEL_MONTHS_RANGE
    high = min(high, tenure)
    month_offset = int(rng.integers(low, high + 1))
    base = pd.Timestamp(start_date) + relativedelta(months=month_offset)
    if min_date is not None and base < min_date:
        base = min_date
    if base > REFERENCE:
        return None

    max_jitter_days = max(0, min(27, (REFERENCE - base).days))
    return base + pd.Timedelta(days=int(rng.integers(0, max_jitter_days + 1)))


def _healthy_rows(rng: np.random.Generator, size: str, customer_type: str, start_date):
    plan = rng.choice(["Basic", "Pro", "Premium"], p=PLAN_PROBABILITIES[size])
    mrr = _draw_mrr(rng, plan, size, customer_type)

    upgrade_plan = PLAN_UPGRADE.get(plan)
    if upgrade_plan is not None and rng.random() < UPGRADE_SHARE:
        low, high = UPGRADE_MONTHS_RANGE
        upgrade_date = _add_months_with_jitter(start_date, rng, low, high)
        if upgrade_date <= REFERENCE:
            new_mrr = _draw_mrr(rng, upgrade_plan, size, customer_type)
            return [
                {"plan": plan, "mrr": mrr, "start_date": start_date, "end_date": upgrade_date, "status": "replaced"},
                {
                    "plan": upgrade_plan,
                    "mrr": new_mrr,
                    "start_date": upgrade_date + pd.Timedelta(days=1),
                    "end_date": None,
                    "status": "active",
                },
            ]

    return [{"plan": plan, "mrr": mrr, "start_date": start_date, "end_date": None, "status": "active"}]


def _price_sensitive_rows(rng: np.random.Generator, size: str, customer_type: str, start_date):
    plan = rng.choice(["Pro", "Premium"])  # overbought, so always starts high
    mrr = _draw_mrr(rng, plan, size, customer_type)

    low, high = DOWNGRADE_MONTHS_RANGE
    downgrade_date = _add_months_with_jitter(start_date, rng, low, high)
    downgrade_plan = PLAN_DOWNGRADE[plan]

    if downgrade_date > REFERENCE:
        # hasn't happened yet: still on the original, overbought plan
        return [{"plan": plan, "mrr": mrr, "start_date": start_date, "end_date": None, "status": "active"}]

    new_mrr = _draw_mrr(rng, downgrade_plan, size, customer_type)
    second_row_start = downgrade_date + pd.Timedelta(days=1)

    cancel_extra_low, _ = CANCEL_AFTER_DOWNGRADE_MONTHS_RANGE
    earliest_cancel_date = downgrade_date + relativedelta(months=cancel_extra_low)
    cancel_date = _cancel_date_if_eligible(rng, start_date, min_date=earliest_cancel_date)

    return [
        {"plan": plan, "mrr": mrr, "start_date": start_date, "end_date": downgrade_date, "status": "replaced"},
        {
            "plan": downgrade_plan,
            "mrr": new_mrr,
            "start_date": second_row_start,
            "end_date": cancel_date,
            "status": "cancelled" if cancel_date is not None else "active",
        },
    ]


def _other_churn_rows(rng: np.random.Generator, size: str, customer_type: str, start_date):
    plan = rng.choice(["Basic", "Pro", "Premium"], p=PLAN_PROBABILITIES[size])
    mrr = _draw_mrr(rng, plan, size, customer_type)
    cancel_date = _cancel_date_if_eligible(rng, start_date)
    return [
        {
            "plan": plan,
            "mrr": mrr,
            "start_date": start_date,
            "end_date": cancel_date,
            "status": "cancelled" if cancel_date is not None else "active",
        }
    ]


def generate_subscriptions(rng: np.random.Generator, customers_df: pd.DataFrame, internal_df: pd.DataFrame) -> pd.DataFrame:
    """Generate the subscriptions table: one or more rows per customer, no gaps or overlaps."""
    internal = internal_df.set_index("customer_id")
    customers = customers_df.set_index("customer_id")

    rows = []
    for customer_id in customers_df["customer_id"]:
        size = internal.loc[customer_id, "size"]
        story = internal.loc[customer_id, "story"]
        customer_type = customers.loc[customer_id, "type"]
        start_date = customers.loc[customer_id, "customer_since"]

        if story == "healthy":
            customer_rows = _healthy_rows(rng, size, customer_type, start_date)
        elif story == "price_sensitive":
            customer_rows = _price_sensitive_rows(rng, size, customer_type, start_date)
        else:
            customer_rows = _other_churn_rows(rng, size, customer_type, start_date)

        for row in customer_rows:
            row["customer_id"] = customer_id
            rows.append(row)

    subscriptions_df = pd.DataFrame(rows)
    subscriptions_df.insert(0, "subscription_id", range(1, len(subscriptions_df) + 1))
    subscriptions_df["start_date"] = pd.to_datetime(subscriptions_df["start_date"]).dt.date
    subscriptions_df["end_date"] = pd.to_datetime(subscriptions_df["end_date"]).dt.date
    return subscriptions_df[["subscription_id", "customer_id", "plan", "mrr", "start_date", "end_date", "status"]]
