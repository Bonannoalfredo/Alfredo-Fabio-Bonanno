# Home.py

# HOMEWORK 3 - FINANCIAL TRANSACTIONS DASHBOARD (entry point)

# Multi-page Streamlit app: this file is the Home page, every file inside
# pages/ automatically becomes an extra page in the left-hand menu.
#
# HOW TO RUN
#   pip install -r requirements.txt
#   streamlit run Home.py
#
# GOLDEN RULE OF STREAMLIT
#   Every time the user touches a widget, Streamlit runs the page script
#   again from top to bottom; the (expensive) ETL is therefore cached in
#   utils/data_loader.py with @st.cache_data.


import streamlit as st
from utils.data_loader import load_star_schema

# st.set_page_config() must be the FIRST Streamlit command in the script.
st.set_page_config(page_title="Homework 3 - Financial Transactions")

st.title("Financial Transactions Dashboard")
st.write(
    "Interactive dashboard built on the **star schema** designed in Homework 3: "
    "one fact table (`Fact_Transactions`) surrounded by four dimensions "
    "(`Dim_Time`, `Dim_Symbol`, `Dim_Geography`, `Dim_TransactionType`)."
)

# A short description of each page.
st.subheader("Pages")
st.write("**1 - Time Analysis** : date-range filter + transactions over time, top symbols / sectors / industries.")

st.divider()

# A first look at the star schema shared by the pages.
fact, dim_time, dim_symbol, dim_geography, dim_type = load_star_schema()

st.subheader("The star schema at a glance")
c1, c2, c3 = st.columns(3)
c1.metric("Fact rows (transactions)", f"{len(fact):,}")
c2.metric("Trading days", len(dim_time))
c3.metric("Countries", len(dim_geography))

st.write("First rows of the fact table:")
st.dataframe(fact.head(8), width="stretch", hide_index=True)

st.write("First rows of `Dim_Symbol`:")
st.dataframe(dim_symbol.head(8), width="stretch", hide_index=True)

st.caption("Streamlit " + st.__version__)
