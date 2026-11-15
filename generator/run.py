"""Entry point for generating the fictional Gastgeber Cloud dataset.

Part 1 (this script): customers, subscriptions, onboarding.
Usage, tickets and surveys come in part 2 (issue #5). Loading into
Postgres comes in issue #6.
"""

from pathlib import Path

import numpy as np
from faker import Faker

from generator.customers import generate_customers
from generator.onboarding import generate_onboarding
from generator.subscriptions import generate_subscriptions

SEED = 42
OUTPUT_DIR = Path("data/generated")


def main() -> None:
    rng = np.random.default_rng(SEED)
    faker = Faker("de_DE")
    faker.seed_instance(SEED)

    customers_df, internal_df = generate_customers(rng, faker)
    subscriptions_df = generate_subscriptions(rng, customers_df, internal_df)
    onboarding_df = generate_onboarding(rng, customers_df, internal_df, subscriptions_df)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    customers_df.to_csv(OUTPUT_DIR / "customers.csv", index=False)
    subscriptions_df.to_csv(OUTPUT_DIR / "subscriptions.csv", index=False)
    onboarding_df.to_csv(OUTPUT_DIR / "onboarding.csv", index=False)
    internal_df[["customer_id", "story"]].to_csv(OUTPUT_DIR / "_truth.csv", index=False)

    print_summary(customers_df, subscriptions_df, onboarding_df, internal_df)


def print_summary(customers_df, subscriptions_df, onboarding_df, internal_df) -> None:
    print("Customers per type:")
    print(customers_df["type"].value_counts().to_string())
    print()

    # size isn't a stored column; join it back in from internal_df for this check only
    size_by_customer = internal_df.set_index("customer_id")["size"]
    print("Customers per size:")
    print(size_by_customer.value_counts().to_string())
    print()

    print("Subscriptions per status:")
    print(subscriptions_df["status"].value_counts().to_string())
    print()

    print("Onboarding per status:")
    print(onboarding_df["status"].value_counts().to_string())
    print()

    final_status = subscriptions_df.groupby("customer_id")["status"].apply(
        lambda s: "cancelled" if (s == "cancelled").any() else "active"
    )
    story_by_status = (
        internal_df.set_index("customer_id")["story"]
        .to_frame()
        .join(final_status.rename("final_status"))
    )
    print("Stories per final status (cancelled vs active):")
    print(story_by_status.groupby(["story", "final_status"]).size().unstack(fill_value=0).to_string())
    print()

    active = subscriptions_df[subscriptions_df["status"] == "active"]
    active_with_type = active.merge(customers_df[["customer_id", "type"]], on="customer_id")
    print("Average current MRR per type (active subscriptions only):")
    print(active_with_type.groupby("type")["mrr"].mean().round(2).to_string())
    print()
    print(f"Total current MRR (active subscriptions only): {active['mrr'].sum():.2f}")


if __name__ == "__main__":
    main()
