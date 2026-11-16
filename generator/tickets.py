"""Generate the tickets table from each customer's phase (pre/post go-live), story, and timing."""

import numpy as np
import pandas as pd

from .constants import (
    CHANNEL_PROBABILITIES_QUIET_HOURS,
    CHANNEL_PROBABILITIES_SERVICE_HOURS,
    CHAMPION_LOSS_HOWTO_SHARE_AFTER_EVENT,
    FEATURE_NAMES_BY_TYPE,
    FIRST_CONTACT_RESOLUTION_HOURS_RANGE,
    OFF_HOURS_PRIORITY_PROBABILITIES,
    PHONE_LOG_DELAY_MINUTES_RANGE,
    PRE_GOLIVE_HOWTO_SHARE,
    QUIET_HOUR_RANGE,
    RESOLUTION_HOURS_RANGE_BY_PRIORITY,
    RESOLVED_FIRST_CONTACT_SHARE,
    SERVICE_HOURS_PRIORITY_PROBABILITIES,
    TECHNICAL_HOUR_CLUSTERS_BY_TYPE,
    TECHNICAL_WEEKEND_WEIGHT,
    TICKET_CATEGORY_PROBABILITIES_BY_STORY,
    TICKETS_PER_MONTH_MEAN_BY_STORY,
)

OTHER_CATEGORIES = ["technical", "billing", "feature_request"]

TEMPLATES_BY_CATEGORY = {
    "technical": [
        ("{feature} is not working", "The {feature} stopped working this morning, we can't find a cause."),
        ("Error when opening {feature}", "We get an error message every time we try to open the {feature}."),
        ("{feature} crashed during service", "The {feature} crashed in the middle of service, please check it."),
        ("Data missing in {feature}", "Some entries in the {feature} seem to have disappeared since yesterday."),
    ],
    "how-to": [
        ("How do I set up {feature}?", "Could you walk us through how to set up the {feature}? We're not sure where to start."),
        ("Question about {feature}", "We're trying to use the {feature} but aren't sure how it's supposed to work."),
        ("New staff need help with {feature}", "We have new staff and they need a quick explanation of the {feature}."),
        ("Where do I find {feature} settings?", "We can't find where to change the settings for the {feature}."),
    ],
    "billing": [
        ("Question about our invoice", "We have a question about a charge on our latest invoice."),
        ("Can we change our plan?", "We'd like to understand what changing our plan would mean for the price."),
        ("Billing seems too high this month", "The amount billed this month looks higher than usual, can you check?"),
        ("Need a copy of an invoice", "Could you send us a copy of a previous invoice for our records?"),
    ],
    "feature_request": [
        ("Could {feature} data be exported directly?", "It would help a lot if {feature} data could be exported directly."),
        ("Suggestion for {feature}", "We have a suggestion for how {feature} could work better for us."),
        ("Missing option in {feature}", "We miss an option in {feature} that we had with our previous system."),
    ],
}
PHONE_SUMMARY_TEMPLATES = {
    "technical": [
        "Customer called: {feature} is not working{service_note}.",
        "Customer called: having trouble with {feature}{service_note}.",
        "Customer called: {feature} showing an error{service_note}.",
    ],
    "how-to": [
        "Customer called: asked how to use {feature}.",
        "Customer called: needed help setting up {feature}.",
        "Customer called: wanted an explanation of {feature}.",
    ],
    "billing": [
        "Customer called: had a question about their invoice.",
        "Customer called: asked about a charge on their bill.",
        "Customer called: wanted to understand their current plan cost.",
    ],
    "feature_request": [
        "Customer called: suggested an improvement for {feature}.",
        "Customer called: asked if {feature} could work differently.",
        "Customer called: requested a new option for {feature}.",
    ],
}


def _weighted_dates(start: pd.Timestamp, end: pd.Timestamp, monday_closed: bool, weekend_weighted: bool):
    if end < start:
        return None
    dates = pd.date_range(start, end, freq="D")
    dow = dates.dayofweek.to_numpy()
    if weekend_weighted:
        weights = np.where((dow == 4) | (dow == 5), TECHNICAL_WEEKEND_WEIGHT, 1.0)
    else:
        weights = np.where(dow < 5, 1.0, 0.0)
    if monday_closed:
        weights = weights.copy()
        weights[dow == 0] = 0.0
    if weights.sum() == 0:
        return None
    return dates, weights / weights.sum()


def _pick_date(rng: np.random.Generator, start, end, monday_closed: bool, weekend_weighted: bool):
    result = _weighted_dates(start, end, monday_closed, weekend_weighted)
    if result is None:
        return None
    dates, probs = result
    return dates[rng.choice(len(dates), p=probs)]


def _draw_category(rng: np.random.Generator, story: str) -> str:
    probs = TICKET_CATEGORY_PROBABILITIES_BY_STORY[story]
    categories = list(probs.keys())
    return rng.choice(categories, p=list(probs.values()))


def _ticket_timing(rng: np.random.Generator, category: str, customer_type: str, start, end, monday_closed: bool, pre_golive: bool):
    """Returns (date, hour, is_service_hour), or None if the window is empty."""
    if pre_golive or category != "technical":
        date = _pick_date(rng, start, end, monday_closed, weekend_weighted=False)
        if date is None:
            return None
        hour = int(rng.integers(QUIET_HOUR_RANGE[0], QUIET_HOUR_RANGE[1] + 1))
        return date, hour, False

    date = _pick_date(rng, start, end, monday_closed, weekend_weighted=True)
    if date is None:
        return None
    hour = int(rng.choice(TECHNICAL_HOUR_CLUSTERS_BY_TYPE[customer_type]))
    return date, hour, True


def _draw_channel(rng: np.random.Generator, is_service_hour: bool) -> str:
    probs = CHANNEL_PROBABILITIES_SERVICE_HOURS if is_service_hour else CHANNEL_PROBABILITIES_QUIET_HOURS
    channels = list(probs.keys())
    return rng.choice(channels, p=list(probs.values()))


def _draw_subject_body(rng: np.random.Generator, category: str, channel: str, customer_type: str, is_service_hour: bool) -> tuple[str, str]:
    feature = rng.choice(FEATURE_NAMES_BY_TYPE[customer_type])
    if channel == "phone":
        service_note = ", reported during service" if category == "technical" and is_service_hour else ""
        templates = PHONE_SUMMARY_TEMPLATES[category]
        template = templates[rng.integers(0, len(templates))]
        body = template.format(feature=feature, service_note=service_note)
        return f"Phone call: {category}", body
    subject_fmt, body_fmt = TEMPLATES_BY_CATEGORY[category][rng.integers(0, len(TEMPLATES_BY_CATEGORY[category]))]
    return subject_fmt.format(feature=feature), body_fmt.format(feature=feature)


def _customer_tickets(
    rng: np.random.Generator,
    customer_id: int,
    customer_type: str,
    story: str,
    start_date,
    go_live_date,
    window_end,
    champion_loss_event_date,
    monday_closed: bool,
    rate_per_month: float,
) -> list[dict]:
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(window_end)
    total_days = (end - start).days
    if total_days <= 0:
        return []

    n_tickets = rng.poisson(rate_per_month * total_days / 30.4)
    go_live = None if go_live_date is None or pd.isna(go_live_date) else pd.Timestamp(go_live_date)
    pre_days = total_days if go_live is None else max((min(go_live, end) - start).days, 0)
    pre_prob = pre_days / total_days

    rows = []
    for _ in range(n_tickets):
        pre_golive = rng.random() < pre_prob

        if pre_golive:
            window_start, window_stop = start, (go_live - pd.Timedelta(days=1)) if go_live is not None else end
            category = "how-to" if rng.random() < PRE_GOLIVE_HOWTO_SHARE else rng.choice(OTHER_CATEGORIES)
        else:
            post_start = go_live if go_live is not None else start
            if story == "champion_loss" and champion_loss_event_date is not None:
                event = pd.Timestamp(champion_loss_event_date)
                post_days = (end - post_start).days
                after_days = max((end - max(event, post_start)).days, 0)
                after_prob = after_days / post_days if post_days > 0 else 0.0
                if rng.random() < after_prob:
                    window_start, window_stop = max(event, post_start), end
                    category = "how-to" if rng.random() < CHAMPION_LOSS_HOWTO_SHARE_AFTER_EVENT else rng.choice(OTHER_CATEGORIES)
                else:
                    window_start, window_stop = post_start, min(event, end)
                    category = _draw_category(rng, story)
            else:
                window_start, window_stop = post_start, end
                category = _draw_category(rng, story)

        timing = _ticket_timing(rng, category, customer_type, window_start, window_stop, monday_closed, pre_golive)
        if timing is None:
            continue
        date, hour, is_service_hour = timing
        minute = int(rng.integers(0, 60))
        created_at = pd.Timestamp(date) + pd.Timedelta(hours=hour, minutes=minute)

        priority_probs = SERVICE_HOURS_PRIORITY_PROBABILITIES if is_service_hour else OFF_HOURS_PRIORITY_PROBABILITIES
        priority = rng.choice(list(priority_probs.keys()), p=list(priority_probs.values()))

        channel = _draw_channel(rng, is_service_hour)
        if channel == "phone":
            delay_low, delay_high = PHONE_LOG_DELAY_MINUTES_RANGE
            created_at = created_at + pd.Timedelta(minutes=int(rng.integers(delay_low, delay_high + 1)))

        resolved_first_contact = rng.random() < RESOLVED_FIRST_CONTACT_SHARE
        if resolved_first_contact:
            low, high = FIRST_CONTACT_RESOLUTION_HOURS_RANGE
        else:
            low, high = RESOLUTION_HOURS_RANGE_BY_PRIORITY[priority]
        resolved_at = created_at + pd.Timedelta(hours=rng.uniform(low, high))
        if resolved_at > end:
            resolved_at = None
            resolved_first_contact = False

        subject, body = _draw_subject_body(rng, category, channel, customer_type, is_service_hour)

        rows.append(
            {
                "customer_id": customer_id,
                "created_at": created_at,
                "resolved_at": resolved_at,
                "channel": channel,
                "category": category,
                "priority": priority,
                "resolved_first_contact": bool(resolved_first_contact),
                "subject": subject,
                "body": body,
                "embedding": None,
            }
        )

    return rows


def generate_tickets(
    rng: np.random.Generator,
    customers_df: pd.DataFrame,
    internal_df: pd.DataFrame,
    onboarding_df: pd.DataFrame,
    signals_df: pd.DataFrame,
) -> pd.DataFrame:
    """Generate the tickets table."""
    internal = internal_df.set_index("customer_id")
    customers = customers_df.set_index("customer_id")
    onboarding = onboarding_df.set_index("customer_id")
    signals = signals_df.set_index("customer_id")

    rows = []
    for customer_id in customers_df["customer_id"]:
        story = internal.loc[customer_id, "story"]
        rows.extend(
            _customer_tickets(
                rng,
                customer_id,
                customers.loc[customer_id, "type"],
                story,
                customers.loc[customer_id, "customer_since"],
                onboarding.loc[customer_id, "go_live_date"],
                signals.loc[customer_id, "window_end"],
                signals.loc[customer_id, "champion_loss_event_date"],
                signals.loc[customer_id, "monday_closed"],
                TICKETS_PER_MONTH_MEAN_BY_STORY[story],
            )
        )

    tickets_df = pd.DataFrame(rows).sort_values("created_at").reset_index(drop=True)
    tickets_df.insert(0, "ticket_id", range(1, len(tickets_df) + 1))
    return tickets_df[
        ["ticket_id", "customer_id", "created_at", "resolved_at", "channel", "category", "priority", "resolved_first_contact", "subject", "body", "embedding"]
    ]
