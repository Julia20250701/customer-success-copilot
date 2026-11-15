"""Generate the customers table and each customer's hidden story."""

import numpy as np
import pandas as pd
from faker import Faker

from .constants import (
    CHAIN_PROBABILITIES,
    CITIES_NRW,
    CITIES_OTHER,
    CONTACT_ROLES_BY_TYPE,
    CSM_OWNERS,
    CUSTOMER_SINCE_RANGE,
    CUSTOMER_TYPE_COUNTS,
    IT_MANAGER_ROLE,
    NAME_PREFIXES_BY_TYPE,
    NRW_SHARE,
    ROOM_BANDS,
    SEAT_BANDS,
    SIZE_PROBABILITIES,
    SIZES,
    STORIES,
    STORY_PROBABILITIES,
)


def _draw_customer_since(rng: np.random.Generator, n: int) -> list:
    start = pd.Timestamp(CUSTOMER_SINCE_RANGE[0])
    end = pd.Timestamp(CUSTOMER_SINCE_RANGE[1])
    total_days = (end - start).days
    offsets = rng.integers(0, total_days + 1, size=n)
    return [(start + pd.Timedelta(days=int(d))).date() for d in offsets]


def _draw_city(rng: np.random.Generator) -> str:
    cities = CITIES_NRW if rng.random() < NRW_SHARE else CITIES_OTHER
    return rng.choice(cities)


def _draw_rooms_seats(rng: np.random.Generator, customer_type: str, size: str):
    rooms = None
    seats = None
    if customer_type in ("hotel", "both"):
        low, high = ROOM_BANDS[size]
        rooms = int(rng.integers(low, high + 1))
    if customer_type in ("restaurant", "both"):
        low, high = SEAT_BANDS[size]
        seats = int(rng.integers(low, high + 1))
    return rooms, seats


def _draw_contact_role(rng: np.random.Generator, customer_type: str, size: str, is_chain: bool, story: str) -> str:
    roles = list(CONTACT_ROLES_BY_TYPE[customer_type])
    if size == "large" or is_chain:
        roles.append(IT_MANAGER_ROLE)
    if story == "champion_loss":
        # an owner doesn't leave their own business; the champion is an employee
        roles = [role for role in roles if role != "owner"]
    return rng.choice(roles)


def _build_name(rng: np.random.Generator, faker: Faker, customer_type: str, used_names: set) -> str:
    prefixes = NAME_PREFIXES_BY_TYPE[customer_type]
    while True:
        prefix = rng.choice(prefixes)
        name = f"{prefix} {faker.last_name()}"
        if name not in used_names:
            used_names.add(name)
            return name


def generate_customers(rng: np.random.Generator, faker: Faker) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate the customers table plus each customer's internal size/story.

    Returns (customers_df, internal_df). internal_df has columns
    customer_id, size, story and is used only inside the generator
    (subscriptions.py, onboarding.py) — it is never merged into the
    customers table itself.
    """
    types = np.array(
        ["restaurant"] * CUSTOMER_TYPE_COUNTS["restaurant"]
        + ["hotel"] * CUSTOMER_TYPE_COUNTS["hotel"]
        + ["both"] * CUSTOMER_TYPE_COUNTS["both"],
        dtype=object,
    )
    rng.shuffle(types)
    n = len(types)

    sizes = rng.choice(SIZES, size=n, p=SIZE_PROBABILITIES)
    stories = rng.choice(STORIES, size=n, p=STORY_PROBABILITIES)
    customer_since = _draw_customer_since(rng, n)
    used_names: set = set()

    rows = []
    for i in range(n):
        customer_type = types[i]
        size = sizes[i]
        story = stories[i]

        rooms, seats = _draw_rooms_seats(rng, customer_type, size)
        is_chain = rng.random() < CHAIN_PROBABILITIES[size]
        contact_role = _draw_contact_role(rng, customer_type, size, is_chain, story)

        rows.append(
            {
                "customer_id": i + 1,
                "name": _build_name(rng, faker, customer_type, used_names),
                "type": customer_type,
                "city": _draw_city(rng),
                "rooms": rooms,
                "seats": seats,
                "is_chain": bool(is_chain),
                "contact_role": contact_role,
                "customer_since": customer_since[i],
                "csm_owner": rng.choice(CSM_OWNERS),
            }
        )

    customers_df = pd.DataFrame(rows)
    customers_df["rooms"] = customers_df["rooms"].astype("Int64")
    customers_df["seats"] = customers_df["seats"].astype("Int64")

    internal_df = pd.DataFrame(
        {"customer_id": customers_df["customer_id"], "size": sizes, "story": stories}
    )
    return customers_df, internal_df
