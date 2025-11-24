import pandas as pd
from typing import Tuple


def compute_yearly_totals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates yearly totals and calculates year-on-year changes.
    Expects a DataFrame containing columns: 'Year' and 'Value'.
    """
    yearly = (
        df.groupby("Year", as_index=False)
        .agg(total_value=("Value", "sum"))
        .sort_values("Year")
    )

    # Calculate year-on-year differences
    yearly["change_abs"] = yearly["total_value"].diff()
    yearly["change_pct"] = yearly["total_value"].pct_change() * 100.0

    return yearly


def extract_year_row(yearly_df: pd.DataFrame, year: int) -> Tuple[pd.Series, pd.Series | None]:
    """
    Returns (current_year_row, previous_year_row)
    """
    current = yearly_df[yearly_df["Year"] == year]
    if current.empty:
        raise ValueError(f"No data available for year {year}")

    idx = current.index[0]
    prev = yearly_df.iloc[idx - 1] if idx > 0 else None

    return current.iloc[0], prev
