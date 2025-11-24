from typing import Optional
import pandas as pd

from .config import INDICATORS
from .kpi_service import compute_yearly_totals, extract_year_row


def _format_change(change_abs: float | None, change_pct: float | None) -> str:
    if change_abs is None or pd.isna(change_abs):
        return "This is the baseline year with no year-on-year comparison available."

    direction = "increase" if change_abs > 0 else "reduction"

    return (
        f"This represents a {direction} of approximately "
        f"{abs(change_abs):,.1f} units "
        f"({abs(change_pct):,.1f}% compared to the previous year)."
    )


def build_indicator_narrative(
    indicator_key: str,
    df: pd.DataFrame,
    year: int,
    unit_label: Optional[str] = None,
) -> str:
    """
    Generates a professional GRI-aligned textual narrative for the given indicator and year.
    """
    meta = INDICATORS[indicator_key]
    yearly = compute_yearly_totals(df)
    current, prev = extract_year_row(yearly, year)

    total = current["total_value"]
    change_abs = None if prev is None else float(current["change_abs"])
    change_pct = None if prev is None else float(current["change_pct"])

    unit = unit_label or str(df["Unit"].iloc[0])

    change_sentence = _format_change(change_abs, change_pct)

    text = (
        f"In {year}, the company reported a total {meta.kpi_name.lower()} of "
        f"approximately {total:,.1f} {unit}. "
        f"{change_sentence} "
        f"This performance is disclosed in alignment with {meta.gri_code}. "
        f"Data is monitored and reviewed on a monthly basis to ensure accuracy, "
        f"identify significant trends, and support decision-making for continuous improvement."
    )

    return text
