import streamlit as st

from src.report_generator import build_gri_pdf_report, get_available_years_for_reports


st.set_page_config(page_title="GRI PDF Report", layout="centered")

st.title("📄 GRI PDF Report Generator")
st.write(
    "Generate a consolidated GRI-aligned PDF report for a selected year, "
    "covering energy, water, emissions, and waste indicators."
)

years = get_available_years_for_reports()

if not years:
    st.error("No data available to generate reports.")
else:
    selected_year = st.selectbox("Select reporting year", years, index=len(years) - 1)

    if st.button("Generate GRI PDF Report"):
        with st.spinner("Generating PDF report..."):
            pdf_buffer = build_gri_pdf_report(selected_year)

        st.success("Report generated successfully!")

        st.download_button(
            label="⬇️ Download GRI PDF Report",
            data=pdf_buffer,
            file_name=f"GRI_Report_{selected_year}.pdf",
            mime="application/pdf",
        )
