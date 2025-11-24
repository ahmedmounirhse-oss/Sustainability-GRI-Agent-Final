import re
from typing import Literal, Dict, Any, List

import pandas as pd

from .config import INDICATORS
from .data_loader import load_indicator
from .kpi_service import compute_yearly_totals
from .reporting import build_indicator_narrative
from .llm_engine import generate_sustainability_answer


IndicatorKey = Literal["energy", "water", "emissions", "waste"]


class SustainabilityAgent:
    """
    Sustainability AI agent that combines:
    - Deterministic KPI calculations (your code, from Excel files)
    - GRI-aligned narratives
    - A powerful LLM (Groq) to generate professional English answers.
    """

    def __init__(self) -> None:
        self._cache: Dict[IndicatorKey, pd.DataFrame] = {}

    # ---------- DATA ACCESS ----------
    def _get_data(self, indicator_key: IndicatorKey) -> pd.DataFrame:
        if indicator_key not in self._cache:
            self._cache[indicator_key] = load_indicator(indicator_key)
        return self._cache[indicator_key]

    # ---------- INTENT DETECTION ----------
    @staticmethod
    def _detect_indicator(query: str) -> IndicatorKey:
        q = query.lower()

        if any(word in q for word in ["energy", "electricity", "power", "302"]):
            return "energy"
        if any(word in q for word in ["water", "303"]):
            return "water"
        if any(word in q for word in ["emission", "emissions", "co2", "carbon", "ghg", "305"]):
            return "emissions"
        if any(word in q for word in ["waste", "306"]):
            return "waste"

        raise ValueError(
            "I could not detect which indicator you're asking about. "
            "Please mention energy, water, emissions, or waste."
        )

    # ---------- YEAR DETECTION ----------
    @staticmethod
    def _detect_years(query: str, df: pd.DataFrame) -> List[int]:
        years_found = [int(y) for y in re.findall(r"\b(20[0-9]{2})\b", query)]
        if years_found:
            return years_found

        # fallback → use latest year
        return [int(df["Year"].max())]

    # ---------- MAIN ANSWER ----------
    def answer(self, query: str) -> str:
        # 1) Detect indicator
        indicator_key = self._detect_indicator(query)
        meta = INDICATORS[indicator_key]

        # 2) Load data + KPIs
        df = self._get_data(indicator_key)
        yearly = compute_yearly_totals(df)

        # 3) Detect years mentioned in the query
        years_requested = self._detect_years(query, df)
        years_available = yearly["Year"].tolist()

        years_valid = [y for y in years_requested if y in years_available]

        if not years_valid:
            raise ValueError(
                f"No data available for the requested year(s). "
                f"Available years: {years_available}"
            )

        # 4) Build KPI context
        unit = df["Unit"].iloc[0]
        kpi_records = []
        narratives = {}

        for year in years_valid:
            row = yearly[yearly["Year"] == year].iloc[0]

            kpi_records.append(
                {
                    "year": int(year),
                    "total_value": float(row["total_value"]),
                    "change_abs": None if pd.isna(row["change_abs"]) else float(row["change_abs"]),
                    "change_pct": None if pd.isna(row["change_pct"]) else float(row["change_pct"]),
                    "unit": unit,
                }
            )

            narratives[year] = build_indicator_narrative(
                indicator_key,
                df,
                year,
                unit_label=unit,
            )

        kpi_context = {
            "indicator_key": indicator_key,
            "indicator_name": meta.kpi_name,
            "gri_code": meta.gri_code,
            "unit": unit,
            "years": years_valid,
            "kpis": kpi_records,
            "base_narratives": narratives,
        }

        # 5) LLM answer
        try:
            llm_answer = generate_sustainability_answer(query, kpi_context)
            return llm_answer

        except Exception as exc:
            # --------------------------
            # Fallback (NO LLM)
            # --------------------------
            fallback_lines = []

            fallback_lines.append(f"Indicator: {meta.kpi_name} ({meta.gri_code})")
            fallback_lines.append(f"Unit: {unit}")
            fallback_lines.append("")

            for rec in kpi_records:
                change_abs_val = (
                    "n/a" if rec["change_abs"] is None else f"{rec['change_abs']:,.1f} {unit}"
                )

                change_pct_val = (
                    "n/a" if rec["change_pct"] is None else f"{rec['change_pct']:,.1f}%"
                )

                line = (
                    f"Year {rec['year']}: total {rec['total_value']:,.1f} {unit} "
                    f"(change: {change_abs_val}; {change_pct_val})."
                )

                fallback_lines.append(line)
                fallback_lines.append(narratives[rec["year"]])
                fallback_lines.append("")

            fallback_text = "\n".join(fallback_lines)

            return (
                "LLM integration failed — returning deterministic KPI-based answer.\n\n"
                + fallback_text
                + f"\n\n[Error details: {exc}]"
            )
