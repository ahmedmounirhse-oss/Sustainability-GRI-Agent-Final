from io import BytesIO
from typing import List

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

from .config import INDICATORS
from .data_loader import load_indicator
from .kpi_service import compute_yearly_totals
from .reporting import build_indicator_narrative


def _get_available_years() -> List[int]:
    years: set[int] = set()
    for key in INDICATORS.keys():
        df = load_indicator(key)
        years.update(df["Year"].unique().tolist())
    return sorted(years)


def build_gri_pdf_report(year: int) -> BytesIO:
    """
    Build a consolidated GRI PDF report for all indicators for a given year.
    Returns a BytesIO buffer that can be used for download (e.g. in Streamlit).
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Sustainability GRI Report {year}",
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="SectionHeader",
            parent=styles["Heading2"],
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="KpiLabel",
            parent=styles["Normal"],
            spaceAfter=4,
        )
    )

    story = []

    # ---------- COVER PAGE ----------
    story.append(Paragraph("Sustainability GRI Report", styles["Title"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(f"Reporting Year: {year}", styles["Heading2"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(
        Paragraph(
            "This report provides a consolidated overview of key sustainability "
            "indicators in alignment with the GRI Standards, including energy "
            "consumption, water usage, greenhouse gas emissions, and waste generation.",
            styles["BodyText"],
        )
    )
    story.append(Spacer(1, 1.5 * cm))

    # Summary table header
    story.append(Paragraph("Report Contents", styles["Heading2"]))
    story.append(Spacer(1, 0.3 * cm))

    toc_data = [["Indicator", "GRI Code", "Included"]]
    for key, meta in INDICATORS.items():
        df = load_indicator(key)
        yearly = compute_yearly_totals(df)
        row = yearly[yearly["Year"] == year]
        included = "Yes" if not row.empty else "No data for this year"
        toc_data.append([meta.kpi_name, meta.gri_code, included])

    toc_table = Table(toc_data, colWidths=[6 * cm, 3 * cm, 5 * cm])
    toc_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E7D32")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    story.append(toc_table)
    story.append(PageBreak())

    # ---------- SECTION PER INDICATOR ----------
    for key, meta in INDICATORS.items():
        df = load_indicator(key)
        yearly = compute_yearly_totals(df)
        row = yearly[yearly["Year"] == year]

        if row.empty:
            # Skip indicators without data for this year
            continue

        row = row.iloc[0]
        unit = str(df["Unit"].iloc[0])

        total = float(row["total_value"])
        change_abs = row["change_abs"]
        change_pct = row["change_pct"]

        # Section header
        story.append(Paragraph(meta.kpi_name, styles["SectionHeader"]))
        story.append(Paragraph(f"GRI Reference: {meta.gri_code}", styles["KpiLabel"]))
        story.append(Spacer(1, 0.2 * cm))

        # KPI Table
        kpi_data = [
            ["Metric", "Value"],
            [f"Total ({year})", f"{total:,.1f} {unit}"],
            [
                "Year-on-Year Change",
                "n/a" if pd.isna(change_abs) else f"{change_abs:,.1f} {unit}",
            ],
            [
                "Year-on-Year % Change",
                "n/a" if pd.isna(change_pct) else f"{change_pct:,.1f}%",
            ],
        ]

        kpi_table = Table(kpi_data, colWidths=[6 * cm, 8 * cm])
        kpi_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1565C0")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                ]
            )
        )

        story.append(kpi_table)
        story.append(Spacer(1, 0.5 * cm))

        # Narrative paragraph
        narrative = build_indicator_narrative(
            indicator_key=key,
            df=df,
            year=year,
            unit_label=unit,
        )
        story.append(Paragraph("Narrative", styles["Heading3"]))
        story.append(Spacer(1, 0.1 * cm))
        story.append(Paragraph(narrative, styles["BodyText"]))
        story.append(Spacer(1, 1 * cm))

        story.append(PageBreak())

    # ---------- BUILD DOCUMENT ----------
    doc.build(story)
    buffer.seek(0)
    return buffer


def get_available_years_for_reports() -> list[int]:
    return _get_available_years()
