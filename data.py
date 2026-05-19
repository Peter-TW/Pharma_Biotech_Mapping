"""
data.py — Load CSVs and derive tables for the Biopharma Command Center.
All public functions are wrapped in @st.cache_data.
"""

import pathlib

import pandas as pd
import streamlit as st

DATA_DIR = pathlib.Path(__file__).parent / "data"

LIFECYCLE_STAGES = ["Discovery", "Preclinical", "Clinical Trials", "FDA Review", "Commercial"]
FINANCIAL_COLS = ["Q_Revenue", "Q_RD", "Q_SGA", "Q_Cash", "Market_Cap_USD_M"]

# Q4 and FY rows routinely share the same Dec-31 end date. On a tied
# Quarter_End_Date, prefer the longer / more complete period so the "latest
# snapshot" is deterministic and does not depend on CSV row order.
PERIOD_PRIORITY = {"FY": 6, "9M": 5, "H1": 4, "Q4": 3, "Q3": 2, "Q2": 1, "Q1": 0}


@st.cache_data
def load_master() -> pd.DataFrame:
    """Load Company_Master.csv and cast the 5 lifecycle columns to bool."""
    df = pd.read_csv(DATA_DIR / "Company_Master.csv", encoding="utf-8-sig")
    for col in LIFECYCLE_STAGES:
        df[col] = df[col].astype(str).str.strip().str.upper() == "TRUE"
    return df


@st.cache_data
def load_financials() -> pd.DataFrame:
    """Load Quarterly_Financials.csv with date parsing and numeric coercion."""
    df = pd.read_csv(DATA_DIR / "Quarterly_Financials.csv", encoding="utf-8-sig")
    df["Quarter_End_Date"] = pd.to_datetime(
        df["Quarter_End_Date"], dayfirst=True, errors="coerce"
    )
    for col in FINANCIAL_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data
def get_latest_financials(fin: pd.DataFrame) -> pd.DataFrame:
    """Per company, the most recent reported row.

    Rows without a parseable Quarter_End_Date are dropped (so a bad date
    upstream cannot crash the app). Sorted by date, then by period length, so
    a tied end-date resolves deterministically (e.g. FY beats Q4). Adds
    rd_intensity and cash_to_mktcap.
    """
    df = fin[fin["Quarter_End_Date"].notna()].copy()
    df["_prio"] = df["Period_Type"].map(PERIOD_PRIORITY).fillna(-1)
    df = df.sort_values(["Quarter_End_Date", "_prio"])
    latest = df.drop_duplicates(subset="Unique_ID", keep="last").copy()
    latest = latest.drop(columns="_prio")

    # Denominators of 0 become NaN so the ratio is NaN, not inf.
    revenue = latest["Q_Revenue"].where(latest["Q_Revenue"] != 0)
    market_cap = latest["Market_Cap_USD_M"].where(latest["Market_Cap_USD_M"] != 0)
    latest["rd_intensity"] = latest["Q_RD"] / revenue
    latest["cash_to_mktcap"] = latest["Q_Cash"] / market_cap
    return latest


@st.cache_data
def get_lifecycle(master: pd.DataFrame) -> pd.DataFrame:
    """Build a lifecycle profile (active stages + label) per company."""
    lc = master[["Unique_ID", "Company Name"] + LIFECYCLE_STAGES].copy()
    lc["active_stages"] = lc[LIFECYCLE_STAGES].apply(
        lambda row: [s for s, v in zip(LIFECYCLE_STAGES, row) if v], axis=1
    )
    lc["lifecycle_profile"] = lc["active_stages"].apply(
        lambda stages: "Full-cycle (all 5 stages)"
        if len(stages) == 5
        else ", ".join(stages) if stages else "None"
    )
    return lc


@st.cache_data
def get_positioning(master: pd.DataFrame, latest: pd.DataFrame) -> pd.DataFrame:
    """Derive positioning labels per company based on lifecycle and latest financials."""
    df = master[["Unique_ID", "Commercial"]].merge(
        latest[["Unique_ID", "rd_intensity", "Market_Cap_USD_M"]],
        on="Unique_ID",
        how="left"
    )

    def compute_pos(row):
        comm = row["Commercial"]
        mcap = row["Market_Cap_USD_M"]
        rdi = row["rd_intensity"]
        
        if not comm:
            return "Pipeline-stage challenger"
        
        if pd.notna(mcap) and mcap >= 100000:
            return "Full-cycle leader"
        
        if pd.notna(rdi):
            if rdi >= 0.30:
                return "R&D-driven commercial"
            else:
                return "Commercial-led"
        else:
            return "Commercial-led"

    df["positioning"] = df.apply(compute_pos, axis=1)
    return df[["Unique_ID", "positioning"]]

