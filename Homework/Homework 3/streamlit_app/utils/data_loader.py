# utils/data_loader.py
# -----------------------------------------------------------------------------
# ETL + star schema construction for the dashboard.
# This is the same ETL implemented in section 2.1 of the Homework3 notebook,
# packaged as reusable functions so every page can share the data.
#
# @st.cache_data -> Streamlit re-runs the whole page script on every widget
# interaction; this decorator makes the ETL run only once, then be reused.
# -----------------------------------------------------------------------------

import pandas as pd
import streamlit as st

# Two company-country names in symbols.csv do not match the official ISO 3166
# names used by country.csv; we reconcile them at integration time.
COUNTRY_NAME_FIXES = {
    "Turkey": "Türkiye",
    "Taiwan": "Taiwan, Province of China",
}


@st.cache_data
def load_star_schema():
    """
    Run the ETL on the three CSV files and return the star schema as five
    dataframes: (fact_transactions, dim_time, dim_symbol, dim_geography,
    dim_type). See the Homework3 notebook (section 2.1) for the full
    explanation of every cleaning decision.
    """
    # ---------------- EXTRACTION ----------------
    # symbols.csv and the account statement use ';', country.csv uses ','.
    symbols = pd.read_csv("data/symbols.csv", sep=";")
    tx = pd.read_csv("data/account-statement-1-1-2024-12-31-2024.csv", sep=";")
    country = pd.read_csv("data/country.csv")

    # ---------------- CLEANSING -----------------
    # Trailing ';' on every line -> empty extra column; plus 464 fully empty rows.
    tx = tx.drop(columns=["Unnamed: 5"]).dropna(how="all")
    # Dates are day-first strings; Unit/IDTransaction became floats because of
    # the empty rows.
    tx["Date"] = pd.to_datetime(tx["Date"], format="%d/%m/%Y %H:%M:%S")
    tx["Unit"] = tx["Unit"].astype(int)
    tx["IDTransaction"] = tx["IDTransaction"].astype("int64")
    # Referential integrity: drop the transactions whose ticker does not exist
    # in symbols.csv (their Dim_Symbol / Dim_Geography keys cannot be resolved).
    tx = tx[tx["Symbol"].isin(symbols["symbol"])].copy()
    # Conform the two non-ISO country names.
    symbols = symbols.copy()
    symbols["country"] = symbols["country"].replace(COUNTRY_NAME_FIXES)

    # ---------------- LOADING: dimensions -------
    # Dim_Time: one row per calendar day, surrogate key in YYYYMMDD form.
    dim_time = pd.DataFrame({"Date": sorted(tx["Date"].dt.normalize().unique())})
    dim_time["TimeId"] = dim_time["Date"].dt.strftime("%Y%m%d").astype(int)
    dim_time["Day"] = dim_time["Date"].dt.day
    dim_time["DayOfWeek"] = dim_time["Date"].dt.day_name()
    dim_time["Month"] = dim_time["Date"].dt.month
    dim_time["MonthName"] = dim_time["Date"].dt.month_name()
    dim_time["Quarter"] = dim_time["Date"].dt.quarter
    dim_time["Year"] = dim_time["Date"].dt.year
    dim_time = dim_time[["TimeId", "Date", "Day", "DayOfWeek", "Month",
                         "MonthName", "Quarter", "Year"]]

    # Dim_Symbol: company attributes only (country lives in Dim_Geography).
    dim_symbol = symbols[["symbol", "company_name", "industry", "sector"]].copy()
    dim_symbol.columns = ["Symbol", "Company", "Industry", "Sector"]
    dim_symbol.insert(0, "SymbolId", range(1, len(dim_symbol) + 1))

    # Dim_Geography: countries hosting listed companies + their hierarchy.
    dim_geography = (country[["name", "sub-region", "region"]]
                     .rename(columns={"name": "Country",
                                      "sub-region": "SubRegion",
                                      "region": "Region"}))
    dim_geography = dim_geography[
        dim_geography["Country"].isin(symbols["country"])].reset_index(drop=True)
    # Taiwan has no region/sub-region in the ISO file: complete the hierarchy.
    taiwan = dim_geography["Country"] == "Taiwan, Province of China"
    dim_geography.loc[taiwan, ["Region", "SubRegion"]] = ["Asia", "Eastern Asia"]
    dim_geography.insert(0, "GeoId", range(1, len(dim_geography) + 1))

    # Dim_TransactionType: BUY / SELL / DIVIDENT.
    dim_type = pd.DataFrame({"TransactionType": sorted(tx["TransactionType"].unique())})
    dim_type.insert(0, "TypeId", range(1, len(dim_type) + 1))

    # ---------------- LOADING: fact table -------
    fact = tx.copy()
    fact["TimeId"] = fact["Date"].dt.strftime("%Y%m%d").astype(int)
    # Symbol lookup, carrying the company country as a bridge towards GeoId.
    bridge = symbols[["symbol", "country"]].merge(
        dim_symbol[["SymbolId", "Symbol"]], left_on="symbol", right_on="Symbol")
    fact = fact.merge(bridge[["symbol", "country", "SymbolId"]],
                      left_on="Symbol", right_on="symbol", how="left")
    fact = fact.merge(dim_geography[["GeoId", "Country"]],
                      left_on="country", right_on="Country", how="left")
    fact = fact.merge(dim_type, on="TransactionType", how="left")
    fact_transactions = fact[["TimeId", "SymbolId", "GeoId", "TypeId",
                              "IDTransaction", "Unit"]].copy()

    return fact_transactions, dim_time, dim_symbol, dim_geography, dim_type


@st.cache_data
def load_olap_view():
    """
    The 'star join': fact table joined with the four dimensions on the
    surrogate keys. Every chart in the dashboard is a filter + group-by
    over this multidimensional view.
    """
    fact, dim_time, dim_symbol, dim_geography, dim_type = load_star_schema()
    star = (fact
            .merge(dim_time, on="TimeId")
            .merge(dim_symbol, on="SymbolId")
            .merge(dim_geography, on="GeoId")
            .merge(dim_type, on="TypeId"))
    return star
