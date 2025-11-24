import streamlit as st
import pandas as pd
from src.ai_agent import SustainabilityAgent
from src.data_loader import load_indicator
from src.kpi_service import compute_yearly_totals



# ---------- INITIALIZATION ----------
st.set_page_config(
    page_title="Sustainability GRI AI Agent",
    layout="wide",
)


agent = SustainabilityAgent()

st.title("🌿 Sustainability GRI AI Agent")
st.write("Ask questions in English about Energy, Water, Emissions, and Waste.")


# ---------- SIDEBAR ----------
st.sidebar.header("Dataset Overview")

indicators = ["energy", "water", "emissions", "waste"]
selected_indicator = st.sidebar.selectbox("Select Indicator", indicators)

# Load data for sidebar stats
df = load_indicator(selected_indicator)
yearly = compute_yearly_totals(df)

st.sidebar.subheader("Yearly Totals")
st.sidebar.dataframe(yearly)


# ---------- MAIN CHAT INTERFACE ----------
st.subheader("💬 Ask the AI Agent")

query = st.text_input("Enter your question in English:")

if st.button("Submit"):
    if query.strip() == "":
        st.warning("Please enter a valid question.")
    else:
        try:
            answer = agent.answer(query)
            st.success("AI Agent Response:")
            st.write(answer)
        except Exception as e:
            st.error(f"Error: {e}")


# ---------- KPI CARDS SECTION ----------
st.subheader("📊 KPI Summary")

col1, col2, col3 = st.columns(3)

latest_year = int(df["Year"].max())
latest_row = yearly[yearly["Year"] == latest_year].iloc[0]

with col1:
    st.metric(
        label=f"Total ({latest_year})",
        value=f"{latest_row['total_value']:,.1f} {df['Unit'].iloc[0]}"
    )

with col2:
    st.metric(
        label="Year-over-Year Change",
        value="n/a" if pd.isna(latest_row["change_abs"]) else f"{latest_row['change_abs']:,.1f}"
    )

with col3:
    st.metric(
        label="YoY % Change",
        value="n/a" if pd.isna(latest_row['change_pct']) else f"{latest_row['change_pct']:,.1f}%"
    )


st.info("This is the first UI version. More visualization dashboards will be added.")
# ---------- TREND CHART ----------
st.subheader("📈 Yearly Trend Chart")

chart_df = yearly.copy()
chart_df["Year"] = chart_df["Year"].astype(str)

st.line_chart(
    chart_df.set_index("Year")["total_value"],
    height=350
)
st.subheader("📊 Year-to-Year Comparison")

years_available = sorted(df["Year"].unique())

colA, colB = st.columns(2)

year1 = colA.selectbox("Select Year A", years_available, index=0)
year2 = colB.selectbox("Select Year B", years_available, index=len(years_available)-1)

if year1 != year2:
    total1 = yearly[yearly["Year"] == year1]["total_value"].iloc[0]
    total2 = yearly[yearly["Year"] == year2]["total_value"].iloc[0]

    diff_abs = total2 - total1
    diff_pct = (diff_abs / total1) * 100.0

    st.write(f"### Comparing **{year1} → {year2}**")
    st.write(f"- **{year1} Total:** {total1:,.1f}")
    st.write(f"- **{year2} Total:** {total2:,.1f}")
    st.write(f"- **Change:** {diff_abs:,.1f} ({diff_pct:,.1f}%)")
