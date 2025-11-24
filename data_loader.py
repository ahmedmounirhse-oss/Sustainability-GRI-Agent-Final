from pathlib import Path
from typing import Dict
import pandas as pd

from .config import DATA_DIR, EXCEL_PATTERN, INDICATORS, IndicatorSheet


def discover_files(pattern: str = EXCEL_PATTERN) -> Dict[int, Path]:
    files: Dict[int, Path] = {}

    for path in DATA_DIR.glob(pattern):
        try:
            year_str = path.stem.split()[-1]
            year = int(year_str)
        except (IndexError, ValueError):
            continue

        files[year] = path

    return dict(sorted(files.items()))


def load_indicator(indicator_key: str) -> pd.DataFrame:
    if indicator_key not in INDICATORS:
        raise ValueError(f"Unknown indicator key: {indicator_key}")

    indicator: IndicatorSheet = INDICATORS[indicator_key]
    files = discover_files()

    frames = []

    for year, path in files.items():
        df = pd.read_excel(path, sheet_name=indicator.sheet_name)

        expected_cols = {"Year", "Month", "Indicator", "Value", "Unit", "Remarks"}
        missing = expected_cols - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns {missing} in {path.name}")

        df["Year"] = df["Year"].astype(int)
        df["Month"] = df["Month"].astype(str)

        frames.append(df)

    data = pd.concat(frames, ignore_index=True)
    data.sort_values(["Year", "Month"], inplace=True)

    return data
