# pages/1_Time_Analysis.py
# =============================================================================
# PAGE 1 - TIME ANALYSIS
# =============================================================================
# Required by the assignment:
#   - a date range filter with defaults 01/01/2024 -> 31/12/2024;
#   - ALL charts on this page react to the selected range;
#   - a line chart of total BUY+SELL transactions over time;
#   - bar charts: top 3 symbols, top 5 sectors, top 5 industries by
#     transaction count.
# =============================================================================

import datetime

import streamlit as st
from utils.data_loader import load_olap_view

# layout="wide" uses the full browser width - good for a dashboard.
st.set_page_config(page_title="Time Analysis", layout="wide")

star = load_olap_view()

st.title("Page 1 - Time Analysis")
st.write("Pick a date range; every chart below reacts to it.")

# -----------------------------------------------------------------------------
# 1. FILTER - date range with the defaults required by the assignment
# -----------------------------------------------------------------------------
DEFAULT_START = datetime.date(2024, 1, 1)
DEFAULT_END = datetime.date(2024, 12, 31)

# st.date_input returns a (start, end) tuple when value is a tuple.
date_range = st.date_input(
    "Date range",
    value=(DEFAULT_START, DEFAULT_END),
    min_value=DEFAULT_START,
    max_value=DEFAULT_END,
)

# While the user is still picking, the widget may return a single date:
# in that case we stop the script and wait for a complete range.
if len(date_range) != 2:
    st.info("Select both a start and an end date.")
    st.stop()

start_date, end_date = date_range

# The assignment asks for BUY + SELL transactions; we also apply the range.
# Dim_Time stores Date at day grain, so a simple between() implements the slice.
data = star[
    star["TransactionType"].isin(["BUY", "SELL"])
    & star["Date"].dt.date.between(start_date, end_date)
]

if data.empty:
    st.warning("No transactions in the selected date range - widen the filter.")
    st.stop()

st.caption(f"{len(data):,} BUY/SELL transactions between {start_date} and {end_date}.")

st.divider()

# -----------------------------------------------------------------------------
# 2. LINE CHART - total transactions (BUY + SELL) over time
# -----------------------------------------------------------------------------
st.subheader("Transactions over time (BUY + SELL)")

# One point per trading day: COUNT(*) grouped on the Date level of Dim_Time.
daily = data.groupby("Date").size().rename("Transactions")
st.line_chart(daily)

# -----------------------------------------------------------------------------
# 3. BAR CHARTS - top symbols / sectors / industries by transaction count
# -----------------------------------------------------------------------------
# Three roll-ups of the same counting measure along the Symbol hierarchy:
# ticker level (top 3), sector level (top 5), industry level (top 5).
col_symbols, col_sectors = st.columns(2)

with col_symbols:
    st.subheader("Top 3 traded symbols")
    top_symbols = data["Symbol"].value_counts().head(3)
    st.bar_chart(top_symbols)

with col_sectors:
    st.subheader("Top 5 sectors")
    top_sectors = data["Sector"].value_counts().head(5)
    st.bar_chart(top_sectors)

st.subheader("Top 5 industries")
top_industries = data["Industry"].value_counts().head(5)
# horizontal=True keeps the long industry names readable.
st.bar_chart(top_industries, horizontal=True)
