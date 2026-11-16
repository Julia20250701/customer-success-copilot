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

# champion_loss: when the champion actually leaves, as a fraction of [customer_since, window_end]
CHAMPION_LOSS_EVENT_PROGRESS_RANGE = (0.5, 0.8)
CHAMPION_LOSS_ACTIVE_USERS_AFTER = 1  # staff still use the POS, so active_users drops to 1 and stays there

# Usage: daily baselines (Poisson means), before season/weekday/story factors.
# pos_transactions is drawn per customer from a range (a restaurant's typical volume),
# then varies day to day with season/weekday only — it keeps running regardless of story.
USAGE_BASELINE_BY_SIZE = {
    "small": {"logins": 3, "active_users": 2, "bookings_created": 3},
    "medium": {"logins": 8, "active_users": 5, "bookings_created": 8},
    "large": {"logins": 18, "active_users": 12, "bookings_created": 18},
}
BOOKINGS_CREATED_TYPE_FACTOR = {"restaurant": 0.6, "hotel": 1.0, "both": 1.0}  # table reservations vs. room bookings
POS_TRANSACTIONS_RANGE_BY_SIZE = {"small": (30, 70), "medium": (50, 150), "large": (150, 300)}
# A shift is one person on one day; Thursday's planning covers the whole next week.
SHIFTS_PLANNED_THURSDAY_MEAN_BY_SIZE = {"small": 25, "medium": 60, "large": 120}  # 0 on all other days

SEASON_FACTOR_BY_MONTH = {
    1: 0.6, 2: 0.6, 3: 1.0, 4: 1.0, 5: 1.3, 6: 1.3, 7: 1.3, 8: 1.3, 9: 1.3, 10: 1.0, 11: 1.0, 12: 1.3,
}
WEEKEND_FACTOR = 1.3  # Friday and Saturday
RESTAURANT_MONDAY_CLOSED_SHARE = 0.6
PRE_GOLIVE_USAGE_FACTOR = 0.1

LOW_ENGAGEMENT_DECLINE_MONTHS_RANGE = (3, 6)  # decline starts this many months before window_end
LOW_ENGAGEMENT_DECLINE_FLOOR = 0.2  # down to ~20% of normal by window_end
CHAMPION_LOSS_TRANSITION_DAYS = 21  # days at active_users=1 before other metrics are also scaled down
CHAMPION_LOSS_METRIC_FACTOR = 0.15  # logins/bookings_created/shifts_planned factor once active_users=1
LOW_ADOPTION_SHIFTS_ZERO_SHARE = 0.9  # share of Thursdays with 0 shifts_planned anyway
LOW_ADOPTION_BOOKINGS_FACTOR = 0.25

# Tickets
FEATURE_NAMES_BY_TYPE = {
    "restaurant": ["POS till", "receipt printer", "TSE", "table reservations", "table map", "shift planner", "DATEV export"],
    "hotel": ["room calendar", "channel manager", "online check-in", "guest registration form", "shift planner", "invoice export"],
    "both": [
        "POS till", "receipt printer", "TSE", "table reservations", "table map", "shift planner", "DATEV export",
        "room calendar", "channel manager", "online check-in", "guest registration form", "invoice export",
    ],
}
TICKETS_PER_MONTH_MEAN_BY_STORY = {
    "healthy": 1.0, "price_sensitive": 1.0, "low_engagement": 0.4, "low_adoption": 1.5, "champion_loss": 1.0,
}
PRE_GOLIVE_HOWTO_SHARE = 0.9  # before go-live, tickets are mostly setup questions
TECHNICAL_WEEKEND_WEIGHT = 2.0  # Fri/Sat weighted this much more than other weekdays for technical tickets
TICKET_CATEGORY_PROBABILITIES_BY_STORY = {
    "healthy":          {"technical": 0.6, "how-to": 0.2, "billing": 0.1, "feature_request": 0.1},
    "price_sensitive":  {"technical": 0.25, "how-to": 0.15, "billing": 0.5, "feature_request": 0.1},
    "low_engagement":   {"technical": 0.3, "how-to": 0.3, "billing": 0.2, "feature_request": 0.2},
    "low_adoption":     {"technical": 0.15, "how-to": 0.65, "billing": 0.1, "feature_request": 0.1},
    "champion_loss":    {"technical": 0.5, "how-to": 0.2, "billing": 0.2, "feature_request": 0.1},
}
CHAMPION_LOSS_HOWTO_SHARE_AFTER_EVENT = 0.8
# Technical tickets cluster around service hours, which depend on customer type.
TECHNICAL_HOUR_CLUSTERS_BY_TYPE = {
    "restaurant": [11, 12, 17, 18, 19, 20, 21],  # opening, lunch, dinner service
    "hotel": [7, 8, 9, 10, 11, 15, 16, 17, 18],  # check-out, check-in
    "both": sorted({11, 12, 17, 18, 19, 20, 21, 7, 8, 9, 10, 15, 16}),
}
# how-to/billing/feature_request, and all pre-go-live tickets, cluster in the quiet weekday afternoon instead.
QUIET_HOUR_RANGE = (14, 17)
SERVICE_HOURS_PRIORITY_PROBABILITIES = {"low": 0.15, "medium": 0.35, "high": 0.35, "urgent": 0.15}
OFF_HOURS_PRIORITY_PROBABILITIES = {"low": 0.45, "medium": 0.35, "high": 0.15, "urgent": 0.05}
RESOLVED_FIRST_CONTACT_SHARE = 0.7
FIRST_CONTACT_RESOLUTION_HOURS_RANGE = (0.25, 2)  # 15 min to 2h, when resolved_first_contact
RESOLUTION_HOURS_RANGE_BY_PRIORITY = {"urgent": (1, 4), "high": (4, 24), "medium": (24, 72), "low": (72, 168)}  # otherwise
TICKET_CHANNELS = ["email", "phone", "chat", "portal"]
CHANNEL_PROBABILITIES_SERVICE_HOURS = {"email": 0.0, "phone": 0.7, "chat": 0.3, "portal": 0.0}
CHANNEL_PROBABILITIES_QUIET_HOURS = {"email": 0.35, "phone": 0.2, "chat": 0.2, "portal": 0.25}
PHONE_LOG_DELAY_MINUTES_RANGE = (5, 30)  # phone tickets are logged by the agent after the call, in third person

# Surveys
NPS_FIRST_MONTHS_AFTER_GO_LIVE = 1
NPS_INTERVAL_MONTHS = 6
CSAT_SHARE_OF_RESOLVED_TICKETS = 0.3
CES_WEEKS_AFTER_GO_LIVE_RANGE = (2, 4)
NPS_RESPONDENT_IS_CONTACT_ROLE_SHARE = 0.8  # otherwise a random other allowed role
# CES scale: 1 = very easy/low effort, 7 = very difficult/high effort (lower is better)
NPS_RANGE_BY_STORY = {
    "healthy": (8, 10), "price_sensitive": (6, 8),
    "low_adoption": (4, 6), "champion_loss": (7, 9),
}
NPS_LOW_ENGAGEMENT_RANGE_BEFORE = (7, 9)  # before low_engagement_decline_start
NPS_LOW_ENGAGEMENT_RANGE_AFTER = (3, 5)  # by window_end, in step with the usage decline
NPS_CHAMPION_LOSS_AFTER_EVENT_RANGE = (3, 5)
CES_RANGE_BY_STORY = {
    "healthy": (1, 3), "price_sensitive": (2, 4), "low_engagement": (3, 5),
    "low_adoption": (4, 6), "champion_loss": (2, 4),
}
CES_HIGH_EFFORT_MIN = 5  # CES >= this counts as a bad (high-effort) experience
CSAT_BASE_RANGE_BY_STORY = {
    "healthy": (4, 5), "price_sensitive": (3, 5), "low_engagement": (2, 4), "low_adoption": (2, 4),
}
CSAT_CHAMPION_LOSS_BEFORE_EVENT_RANGE = (4, 5)
CSAT_CHAMPION_LOSS_AFTER_EVENT_RANGE = (2, 3)

# Survey comments: not every survey gets one, and low scores get one more often
COMMENT_SHARE_DEFAULT = 0.4
COMMENT_SHARE_LOW_SCORE = 0.65
NPS_LOW_SCORE_MAX = 6
CSAT_LOW_SCORE_MAX = 2
