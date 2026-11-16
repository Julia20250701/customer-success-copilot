"""Generate the surveys table: NPS every ~6 months, CSAT after some resolved tickets, CES once."""

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta

from .constants import (
    CES_HIGH_EFFORT_MIN,
    CES_RANGE_BY_STORY,
    CES_WEEKS_AFTER_GO_LIVE_RANGE,
    CONTACT_ROLES_BY_TYPE,
    CSAT_BASE_RANGE_BY_STORY,
    CSAT_CHAMPION_LOSS_AFTER_EVENT_RANGE,
    CSAT_CHAMPION_LOSS_BEFORE_EVENT_RANGE,
    CSAT_LOW_SCORE_MAX,
    CSAT_SHARE_OF_RESOLVED_TICKETS,
    COMMENT_SHARE_DEFAULT,
    COMMENT_SHARE_LOW_SCORE,
    FEATURE_NAMES_BY_TYPE,
    IT_MANAGER_ROLE,
    NPS_CHAMPION_LOSS_AFTER_EVENT_RANGE,
    NPS_FIRST_MONTHS_AFTER_GO_LIVE,
    NPS_INTERVAL_MONTHS,
    NPS_LOW_ENGAGEMENT_RANGE_AFTER,
    NPS_LOW_ENGAGEMENT_RANGE_BEFORE,
    NPS_LOW_SCORE_MAX,
    NPS_RANGE_BY_STORY,
    NPS_RESPONDENT_IS_CONTACT_ROLE_SHARE,
)

# NPS: relationship-level, reflects the story
NPS_COMMENTS_BY_STORY = {
    "price_sensitive": [
        "It's a good product, but the price feels high for what we use.",
        "We like it, though we're reconsidering because of the cost.",
        "Good software, but getting expensive for a business our size.",
    ],
    "low_adoption": [
        "It's too complicated for our team right now.",
        "We could really use more training on this.",
        "Not sure we're using it right — feels like a lot to learn.",
    ],
    "low_engagement": [
        "We haven't had much time to use this lately.",
        "Things have been busy, we barely log in anymore.",
        "Honestly we've fallen out of the habit of using it.",
    ],
    "champion_loss_after": [
        "Our manager left, and nobody really knows the system anymore.",
        "We lost our go-to person for this software, it's been a struggle since.",
        "Since the person who set this up left, we're a bit lost with it.",
    ],
}
NPS_PRAISE_TEMPLATES = [
    "We really like the {feature}.",
    "The {feature} has made things much easier for us.",
    "Big fan of the {feature} especially.",
]

# CSAT: about this one support interaction
CSAT_GOOD_COMMENTS = [
    "Quick and friendly help, thank you!",
    "Solved right away, great support.",
    "Support got back to us fast and sorted it out.",
]
CSAT_BAD_COMMENTS = [
    "Took a while to get this resolved.",
    "Still not sure the issue is fully fixed.",
    "Support was slow to respond on this one.",
]

# CES: about the onboarding/setup effort
CES_EASY_COMMENTS = [
    "Setup was quick and straightforward.",
    "Getting started was easier than we expected.",
    "No trouble at all setting things up.",
]
CES_HARD_COMMENTS = [
    "Setup took a lot of effort.",
    "We needed a lot of help to get going.",
    "The onboarding process was harder than we expected.",
]


def _allowed_roles(customer_type: str, size: str, is_chain: bool) -> list:
    roles = list(CONTACT_ROLES_BY_TYPE[customer_type])
    if size == "large" or is_chain:
        roles.append(IT_MANAGER_ROLE)
    return roles


def _random_role(rng: np.random.Generator, roles: list, exclude: str | None = None) -> str:
    pool = [r for r in roles if r != exclude] or roles
    return rng.choice(pool)


def _comment_or_none(rng: np.random.Generator, is_bad: bool, good_choices: list, bad_choices: list | None = None) -> str | None:
    share = COMMENT_SHARE_LOW_SCORE if is_bad else COMMENT_SHARE_DEFAULT
    if rng.random() >= share:
        return None
    choices = bad_choices if is_bad and bad_choices is not None else good_choices
    return rng.choice(choices)


def _nps_comment(
    rng: np.random.Generator, story: str, score: int, after_event: bool, customer_type: str, date: pd.Timestamp, low_engagement_decline_start
) -> str | None:
    is_bad = score <= NPS_LOW_SCORE_MAX
    if story == "champion_loss" and after_event:
        return _comment_or_none(rng, is_bad, NPS_COMMENTS_BY_STORY["champion_loss_after"])
    if story == "low_engagement" and low_engagement_decline_start is not None and date >= low_engagement_decline_start:
        return _comment_or_none(rng, is_bad, NPS_COMMENTS_BY_STORY["low_engagement"])
    if story in ("price_sensitive", "low_adoption"):
        return _comment_or_none(rng, is_bad, NPS_COMMENTS_BY_STORY[story])
    # healthy, champion_loss before the event, and low_engagement before its decline
    feature = rng.choice(FEATURE_NAMES_BY_TYPE[customer_type])
    praise = [t.format(feature=feature) for t in NPS_PRAISE_TEMPLATES]
    return _comment_or_none(rng, is_bad, praise)


def _csat_comment(rng: np.random.Generator, score: int) -> str | None:
    is_bad = score <= CSAT_LOW_SCORE_MAX
    return _comment_or_none(rng, is_bad, CSAT_GOOD_COMMENTS, CSAT_BAD_COMMENTS)


def _ces_comment(rng: np.random.Generator, score: int) -> str | None:
    is_bad = score >= CES_HIGH_EFFORT_MIN
    return _comment_or_none(rng, is_bad, CES_EASY_COMMENTS, CES_HARD_COMMENTS)


def _nps_score(rng: np.random.Generator, story: str, after_event: bool, date: pd.Timestamp, window_end: pd.Timestamp, low_engagement_decline_start) -> int:
    if story == "champion_loss" and after_event:
        low, high = NPS_CHAMPION_LOSS_AFTER_EVENT_RANGE
        return int(rng.integers(low, high + 1))
    if story == "low_engagement":
        before_low, before_high = NPS_LOW_ENGAGEMENT_RANGE_BEFORE
        after_low, after_high = NPS_LOW_ENGAGEMENT_RANGE_AFTER
        if low_engagement_decline_start is not None and date >= low_engagement_decline_start:
            total = (window_end - low_engagement_decline_start).total_seconds()
            progress = min(max((date - low_engagement_decline_start).total_seconds() / total, 0.0), 1.0) if total > 0 else 1.0
        else:
            progress = 0.0
        low = round(before_low - (before_low - after_low) * progress)
        high = round(before_high - (before_high - after_high) * progress)
        return int(rng.integers(low, high + 1))
    low, high = NPS_RANGE_BY_STORY[story]
    return int(rng.integers(low, high + 1))


def _nps_rows(
    rng: np.random.Generator, customer_id, customer_type, story, contact_role, roles, go_live_date, window_end, champion_loss_event_date, low_engagement_decline_start
) -> list[dict]:
    if go_live_date is None or pd.isna(go_live_date):
        return []

    rows = []
    date = pd.Timestamp(go_live_date) + relativedelta(months=NPS_FIRST_MONTHS_AFTER_GO_LIVE)
    while date <= window_end:
        after_event = story == "champion_loss" and champion_loss_event_date is not None and date >= champion_loss_event_date
        score = _nps_score(rng, story, after_event, date, window_end, low_engagement_decline_start)

        if after_event:
            role = _random_role(rng, roles, exclude=contact_role)
        elif rng.random() < NPS_RESPONDENT_IS_CONTACT_ROLE_SHARE:
            role = contact_role
        else:
            role = _random_role(rng, roles)

        comment = _nps_comment(rng, story, score, after_event, customer_type, date, low_engagement_decline_start)
        rows.append(
            {
                "customer_id": customer_id,
                "type": "NPS",
                "score": score,
                "comment": comment,
                "answered_at": date,
                "respondent_role": role,
                "ticket_id": None,
            }
        )
        date = date + relativedelta(months=NPS_INTERVAL_MONTHS)
    return rows


def _csat_rows(
    rng: np.random.Generator, customer_id, story, contact_role, roles, window_end, champion_loss_event_date, customer_tickets: pd.DataFrame
) -> list[dict]:
    rows = []
    resolved = customer_tickets[customer_tickets["resolved_at"].notna()]
    for _, ticket in resolved.iterrows():
        if rng.random() >= CSAT_SHARE_OF_RESOLVED_TICKETS:
            continue
        date = ticket["resolved_at"] + pd.Timedelta(days=int(rng.integers(1, 4)))
        if date > window_end:
            continue

        after_event = story == "champion_loss" and champion_loss_event_date is not None and ticket["created_at"] >= champion_loss_event_date
        if story == "champion_loss":
            low, high = CSAT_CHAMPION_LOSS_AFTER_EVENT_RANGE if after_event else CSAT_CHAMPION_LOSS_BEFORE_EVENT_RANGE
        else:
            low, high = CSAT_BASE_RANGE_BY_STORY[story]
        base = int(rng.integers(low, high + 1))
        score = min(5, base + 1) if ticket["resolved_first_contact"] else max(1, base - 1)

        role = _random_role(rng, roles, exclude=contact_role if after_event else None)
        comment = _csat_comment(rng, score)
        rows.append(
            {
                "customer_id": customer_id,
                "type": "CSAT",
                "score": score,
                "comment": comment,
                "answered_at": date,
                "respondent_role": role,
                "ticket_id": ticket["ticket_id"],
            }
        )
    return rows


def _ces_rows(rng: np.random.Generator, customer_id, story, contact_role, go_live_date, window_end) -> list[dict]:
    if go_live_date is None or pd.isna(go_live_date):
        return []
    low, high = CES_WEEKS_AFTER_GO_LIVE_RANGE
    date = pd.Timestamp(go_live_date) + pd.Timedelta(weeks=int(rng.integers(low, high + 1)))
    if date > window_end:
        return []

    score_low, score_high = CES_RANGE_BY_STORY[story]
    score = int(rng.integers(score_low, score_high + 1))
    comment = _ces_comment(rng, score)

    return [
        {
            "customer_id": customer_id,
            "type": "CES",
            "score": score,
            "comment": comment,
            "answered_at": date,
            "respondent_role": contact_role,  # the person who did the onboarding
            "ticket_id": None,
        }
    ]


def generate_surveys(
    rng: np.random.Generator,
    customers_df: pd.DataFrame,
    internal_df: pd.DataFrame,
    onboarding_df: pd.DataFrame,
    signals_df: pd.DataFrame,
    tickets_df: pd.DataFrame,
) -> pd.DataFrame:
    """Generate the surveys table."""
    internal = internal_df.set_index("customer_id")
    customers = customers_df.set_index("customer_id")
    onboarding = onboarding_df.set_index("customer_id")
    signals = signals_df.set_index("customer_id")
    tickets_by_customer = tickets_df.groupby("customer_id")

    rows = []
    for customer_id in customers_df["customer_id"]:
        story = internal.loc[customer_id, "story"]
        size = internal.loc[customer_id, "size"]
        customer_type = customers.loc[customer_id, "type"]
        contact_role = customers.loc[customer_id, "contact_role"]
        is_chain = customers.loc[customer_id, "is_chain"]
        go_live_date = onboarding.loc[customer_id, "go_live_date"]
        window_end = signals.loc[customer_id, "window_end"]
        champion_loss_event_date = signals.loc[customer_id, "champion_loss_event_date"]
        low_engagement_decline_start = signals.loc[customer_id, "low_engagement_decline_start"]
        roles = _allowed_roles(customer_type, size, is_chain)

        rows.extend(
            _nps_rows(
                rng, customer_id, customer_type, story, contact_role, roles, go_live_date, window_end, champion_loss_event_date, low_engagement_decline_start
            )
        )

        customer_tickets = (
            tickets_by_customer.get_group(customer_id)
            if customer_id in tickets_by_customer.groups
            else pd.DataFrame(columns=["ticket_id", "created_at", "resolved_at", "resolved_first_contact"])
        )
        rows.extend(_csat_rows(rng, customer_id, story, contact_role, roles, window_end, champion_loss_event_date, customer_tickets))

        rows.extend(_ces_rows(rng, customer_id, story, contact_role, go_live_date, window_end))

    surveys_df = pd.DataFrame(rows).sort_values("answered_at").reset_index(drop=True)
    surveys_df.insert(0, "survey_id", range(1, len(surveys_df) + 1))
    return surveys_df[["survey_id", "customer_id", "type", "score", "comment", "answered_at", "respondent_role", "ticket_id"]]
