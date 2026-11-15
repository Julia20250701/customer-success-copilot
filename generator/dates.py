"""Shared date helpers for the generator: what "today" means for the dataset, and tenure."""

import pandas as pd
from dateutil.relativedelta import relativedelta

from .constants import REFERENCE_DATE

REFERENCE = pd.Timestamp(REFERENCE_DATE)


def tenure_months(start_date) -> int:
    """Whole months between start_date and REFERENCE_DATE."""
    delta = relativedelta(REFERENCE.date(), start_date)
    return delta.years * 12 + delta.months
