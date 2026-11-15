PLANS = ["Basic", "Pro", "Premium"]
SIZES = ["small", "medium", "large"]
SIZE_PROBABILITIES = [0.6, 0.3, 0.1]  # small, medium, large

CUSTOMER_TYPE_COUNTS = {"restaurant": 150, "hotel": 30, "both": 20}  # exact, sums to 200

# German cities, weighted toward NRW
NRW_SHARE = 0.4  # share of customers whose city is drawn from CITIES_NRW
CITIES_NRW = ["Köln", "Düsseldorf", "Dortmund", "Essen", "Duisburg", "Bochum", "Wuppertal", "Bielefeld", "Bonn", "Münster"]
CITIES_OTHER = ["Berlin", "Hamburg", "München", "Frankfurt am Main", "Stuttgart", "Leipzig", "Dresden", "Hannover", "Nürnberg", "Bremen"]

ROOM_BANDS = {"small": (5, 25), "medium": (26, 80), "large": (81, 200)}  # min 5 rooms
SEAT_BANDS = {"small": (15, 50), "medium": (51, 150), "large": (151, 400)}  # min 15 seats, 151+ capped at 400

# MRR ranges (EUR) per plan, split into size sub-bands so bigger customers pay more within a plan
MRR_RANGES = {
    "Basic":   {"small": (120, 250), "medium": (250, 400), "large": (400, 550)},
    "Pro":     {"small": (220, 500), "medium": (500, 800), "large": (800, 1100)},
    "Premium": {"small": (350, 800), "medium": (800, 1300), "large": (1300, 1800)},
}
# "both" pays the hotel package plus the restaurant module, with a bundle discount
MRR_FACTOR_BY_TYPE = {"restaurant": 0.6, "hotel": 1.0, "both": 1.4}

# Plan choice depends on size: larger customers are more likely to choose Pro/Premium.
# Weighted by SIZE_PROBABILITIES, this averages out close to the overall target of 50% / 35% / 15%.
PLAN_PROBABILITIES = {
    "small":  [0.65, 0.30, 0.05],
    "medium": [0.45, 0.40, 0.15],
    "large":  [0.20, 0.40, 0.40],
}

# Chain membership depends on size: larger customers are more likely to be a chain.
# Weighted by SIZE_PROBABILITIES, this averages out close to the overall target of 10%.
CHAIN_PROBABILITIES = {"small": 0.05, "medium": 0.12, "large": 0.35}

CUSTOMER_SINCE_RANGE = ("2024-01-01", "2026-09-30")

# Allowed contact roles depend on customer type; it_manager is added separately
# for large customers or chains (handled in customers.py), not listed here.
CONTACT_ROLES_BY_TYPE = {
    "restaurant": ["owner", "restaurant_manager", "shift_supervisor"],
    "hotel": ["owner", "general_manager", "front_office_manager"],
    "both": ["owner", "general_manager", "front_office_manager", "restaurant_manager", "shift_supervisor"],
}
IT_MANAGER_ROLE = "it_manager"

# Name prefixes by customer type, combined with a Faker last name to build a unique business name
NAME_PREFIXES_BY_TYPE = {
    "restaurant": ["Restaurant", "Bistro", "Trattoria", "Brauhaus", "Café", "Wirtshaus"],
    "hotel": ["Hotel", "Pension", "Boutique-Hotel", "Stadthotel"],
    "both": ["Landgasthof", "Gasthof", "Hotel-Restaurant", "Landhotel"],
}

CSM_OWNERS = ["Lena Vogt", "Tom Brandt", "Mara Keller"]  # fictional CSM team

STORIES = ["healthy", "price_sensitive", "low_engagement", "low_adoption", "champion_loss"]
STORY_PROBABILITIES = [0.6, 0.1, 0.1, 0.1, 0.1]
CHURN_STORIES = ["price_sensitive", "low_engagement", "low_adoption", "champion_loss"]
CHURN_CANCELLED_SHARE = 0.5  # share of each churn story that has already cancelled
CANCEL_MONTHS_RANGE = (6, 14)  # months after start until cancellation, for those that cancel

# "Today" for the generated dataset: controls which events have had time to happen
REFERENCE_DATE = "2026-11-15"
MIN_TENURE_MONTHS_FOR_CANCEL = 6  # must have been a customer this long (as of REFERENCE_DATE) to already be cancelled

PLAN_UPGRADE = {"Basic": "Pro", "Pro": "Premium"}  # healthy story; Premium has no further upgrade
PLAN_DOWNGRADE = {"Premium": "Pro", "Pro": "Basic"}  # price_sensitive story

UPGRADE_SHARE = 0.2  # share of healthy customers (on Basic/Pro) who upgrade
UPGRADE_MONTHS_RANGE = (4, 16)  # months after start until upgrade, for those that upgrade
DOWNGRADE_MONTHS_RANGE = (3, 8)  # months after start until downgrade, for price_sensitive
CANCEL_AFTER_DOWNGRADE_MONTHS_RANGE = (2, 4)  # extra months after the downgrade until cancellation
CANCELLED_EARLY_MONTHS_THRESHOLD = 9  # a cancellation within this many months of customer_since counts as "early"

# Onboarding timing
KICKOFF_DAYS_RANGE = (7, 14)  # kickoff happens 1-2 weeks after customer_since; always filled
GO_LIVE_WEEKS_RANGE = (3, 8)  # go-live happens 3-8 weeks after kickoff, if it happens at all
FIRST_VALUE_WEEKS_RANGE = (1, 4)  # first value 1-4 weeks after go-live
FIRST_VALUE_WEEKS_RANGE_LOW_ADOPTION = (6, 10)  # low_adoption: first value comes later than usual

# Stalling is only possible for customers newer than STALL_RECENT_TENURE_MONTHS, or
# who cancelled early. Customers with 6+ months of tenure who didn't cancel early are
# always "live" (for low_adoption, only the later first_value_date shows the story).
# Healthy customers never stall.
STALL_BASE_PROBABILITY = {
    "healthy": 0.0,
    "price_sensitive": 0.08,
    "low_engagement": 0.08,
    "low_adoption": 0.30,
    "champion_loss": 0.08,
}
STALL_CANCELLED_EARLY_BONUS = 0.25
STALL_RECENT_BONUS = 0.15
STALL_RECENT_TENURE_MONTHS = 6
