"""
data.py — Load CSVs and derive tables for the Biopharma Command Center.
All public functions are wrapped in @st.cache_data.
"""

import math
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
def load_profiles() -> pd.DataFrame:
    """Load Company_Profile.csv."""
    return pd.read_csv(DATA_DIR / "Company_Profile.csv", encoding="utf-8-sig")



@st.cache_data
def load_financials() -> pd.DataFrame:
    """Load Quarterly_Financials.csv with date parsing and numeric coercion."""
    df = pd.read_csv(DATA_DIR / "Quarterly_Financials.csv", encoding="utf-8-sig")
    df["Quarter_End_Date"] = pd.to_datetime(
        df["Quarter_End_Date"], format="mixed", dayfirst=True, errors="coerce"
    )
    for col in FINANCIAL_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data
def load_data_notes() -> pd.DataFrame:
    """Load Dashboard_Data_Notes.csv. Returns empty frame if missing."""
    path = DATA_DIR / "Dashboard_Data_Notes.csv"
    if not path.exists():
        return pd.DataFrame(columns=[
            "Unique_ID", "Period_Type_Scope", "Status_Label",
            "Tooltip", "Data_Treatment_Note", "Source_Files",
        ])
    df = pd.read_csv(path, encoding="utf-8-sig")
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
def get_sector_ratio_trend(
    fin: pd.DataFrame,
    pool_ids,
    min_coverage_pct: float = 0.50,
) -> pd.DataFrame:
    """Build dollar-weighted sector ratio trends for the selected company pool.

    Ratios are calculated only from true quarterly rows (Q1-Q4), so FY/H1/9M
    reporters are not mixed into quarter-level trend lines. Rows are grouped by
    Calendar_Quarter, not Period_Type, because some companies disclose fiscal
    quarter labels that do not match the market calendar quarter. Each ratio is
    computed as sum(numerator) / sum(denominator) using only rows where both
    parts of that metric are disclosed.
    """
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    q_order = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}
    metric_specs = {
        "R&D Intensity": {
            "num": "Q_RD",
            "den": "Q_Revenue",
            "definition": "Σ R&D ÷ Σ Revenue",
            "help": "Dollar-weighted sector R&D spend as a share of revenue.",
        },
        "Cash / Market Cap": {
            "num": "Q_Cash",
            "den": "Market_Cap_USD_M",
            "definition": "Σ Cash ÷ Σ Market Cap",
            "help": "Sector cash buffer relative to public market valuation.",
        },
        "SG&A Intensity": {
            "num": "Q_SGA",
            "den": "Q_Revenue",
            "definition": "Σ SG&A ÷ Σ Revenue",
            "help": "Dollar-weighted operating/commercial overhead as a share of revenue.",
        },
    }

    pool_ids = set(pool_ids)
    pool_size = len(pool_ids)
    if pool_size == 0:
        return pd.DataFrame()

    q = fin[
        fin["Unique_ID"].isin(pool_ids)
        & fin["Period_Type"].isin(quarters)
    ].copy()
    if q.empty:
        return pd.DataFrame()

    for col in ["Q_Revenue", "Q_RD", "Q_SGA", "Q_Cash", "Market_Cap_USD_M"]:
        q[col] = pd.to_numeric(q[col], errors="coerce")

    # Period_Type says how the company disclosed the row. Calendar_Quarter says
    # where that row belongs on a market-time x-axis. Group the sector trend by
    # Calendar_Quarter so non-calendar fiscal reporters do not get silently
    # bucketed into the wrong market quarter.
    q["Calendar_Quarter"] = q["Calendar_Quarter"].astype(str).str.strip().str.upper()
    q = q[q["Calendar_Quarter"].isin(quarters)].copy()
    if q.empty:
        return pd.DataFrame()

    # Prevent one-company leading-edge quarters from reading as an industry trend.
    min_reporting = max(1, math.ceil(pool_size * min_coverage_pct))
    if pool_size >= 6:
        min_reporting = max(3, min_reporting)

    rows = []
    grouped = q.groupby(["Calendar_Year", "Calendar_Quarter"], dropna=False)
    for (year, calendar_quarter), g in grouped:
        if pd.isna(year) or calendar_quarter not in q_order:
            continue

        reporting_companies = int(g["Unique_ID"].nunique())
        if reporting_companies < min_reporting:
            continue

        year = int(year)
        period_label = f"{calendar_quarter} {year}"
        sort_key = year * 10 + q_order[calendar_quarter]
        period_end = g["Quarter_End_Date"].max()

        for metric, spec in metric_specs.items():
            paired = g[["Unique_ID", spec["num"], spec["den"]]].dropna()
            paired = paired[paired[spec["den"]] != 0]
            denominator = paired[spec["den"]].sum()
            value = paired[spec["num"]].sum() / denominator if denominator else pd.NA

            rows.append({
                "Metric": metric,
                "Period": period_label,
                "Calendar_Year": year,
                "Calendar_Quarter": calendar_quarter,
                "Quarter_End_Date": period_end,
                "Sort_Key": sort_key,
                "Value": value,
                "Definition": spec["definition"],
                "Metric_Help": spec["help"],
                "Reporting_Companies": reporting_companies,
                "Contributing_Companies": int(paired["Unique_ID"].nunique()),
                "Companies_In_View": pool_size,
                "Coverage": reporting_companies / pool_size,
            })

    trend = pd.DataFrame(rows)
    if trend.empty:
        return trend
    trend["Value"] = pd.to_numeric(trend["Value"], errors="coerce")
    return trend.sort_values(["Sort_Key", "Metric"]).reset_index(drop=True)


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
    cols_to_use = ["Unique_ID"] + [c for c in LIFECYCLE_STAGES if c in master.columns]
    if "Commercial" not in cols_to_use:
        cols_to_use.append("Commercial")
    cols_to_use = list(dict.fromkeys(cols_to_use))

    df = master[cols_to_use].merge(
        latest[["Unique_ID", "rd_intensity", "Market_Cap_USD_M"]],
        on="Unique_ID",
        how="left"
    )

    def compute_pos(row):
        is_full_cycle = all(row.get(col) == True for col in LIFECYCLE_STAGES)
        comm = row["Commercial"]
        mcap = row["Market_Cap_USD_M"]
        rdi = row["rd_intensity"]
        
        if is_full_cycle and pd.notna(mcap) and mcap >= 100000:
            return "Full-cycle leader"
        elif comm == True and pd.notna(rdi) and rdi >= 0.30:
            return "R&D-driven commercial"
        elif comm == True:
            return "Commercial-led"
        else:
            return "Pipeline-stage challenger"

    df["positioning"] = df.apply(compute_pos, axis=1)
    return df[["Unique_ID", "positioning"]]


@st.cache_data
def load_clinical_status_summary() -> pd.DataFrame:
    """Load ClinicalTrials_Status_Summary.csv with type coercion. Returns empty if missing."""
    path = DATA_DIR / "clinical_trials" / "ClinicalTrials_Status_Summary.csv"
    if not path.exists():
        return pd.DataFrame(columns=[
            "Fetch_Date", "Unique_ID", "Company_Name", "Expected_Zero",
            "Owned_Active_Pipeline_Count", "Owned_Recruiting_Count",
            "Owned_Active_Not_Recruiting_Count", "Owned_Operational_Risk_Count",
            "Owned_Phase_III_Count_Exclusive", "Participated_All_Trials"
        ])
    df = pd.read_csv(path, encoding="utf-8-sig")
    # Coerce numeric columns
    numeric_cols = [c for c in df.columns if c.startswith(("Owned_", "Participated_"))]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    # Coerce boolean column
    df["Expected_Zero"] = df["Expected_Zero"].astype(str).str.upper() == "TRUE"
    return df


@st.cache_data
def load_expected_zero() -> pd.DataFrame:
    """Load Expected_Zero_Companies.csv."""
    path = DATA_DIR / "clinical_trials" / "Expected_Zero_Companies.csv"
    if not path.exists():
        return pd.DataFrame(columns=["Unique_ID", "Company_Name", "Reason"])
    return pd.read_csv(path, encoding="utf-8-sig")


@st.cache_data
def build_bridge_chart_data(master: pd.DataFrame, latest_financials: pd.DataFrame, status_summary: pd.DataFrame) -> pd.DataFrame:
    """One row per company with the columns the bridge chart needs.

    Filters:
      - Excludes companies where Expected_Zero == True
      - Excludes companies where latest R&D spend is null OR <= 0
      - Excludes companies where Market_Cap is null OR <= 0
    """
    df_base = master[["Unique_ID", "Company Name"]].copy()
    df_base = df_base.rename(columns={"Company Name": "Company_Name"})
    
    # 1. R&D annualization helper
    def annualize_rd(row):
        period = row.get("Period_Type")
        q_rd = row.get("Q_RD")
        if pd.isna(q_rd) or q_rd is None:
            return None
        try:
            q_rd = float(q_rd)
        except ValueError:
            return None
            
        if period == "FY":
            return q_rd
        elif period == "9M":
            return q_rd * (4.0 / 3.0)
        elif period == "H1":
            return q_rd * 2.0
        elif period in ("Q1", "Q2", "Q3", "Q4"):
            return q_rd * 4.0
        return None

    # 2. Period label helper
    def get_period_label(row):
        period = row.get("Period_Type")
        year = row.get("Calendar_Year")
        if pd.isna(period) or period is None or period == "":
            return ""
        year_str = str(int(year)) if pd.notna(year) else ""
        return f"{period} {year_str}".strip()

    # Merge master with latest financials
    df_merged = df_base.merge(
        latest_financials[["Unique_ID", "Market_Cap_USD_M", "Q_RD", "Period_Type", "Calendar_Year"]],
        on="Unique_ID",
        how="left"
    )
    
    df_merged["RD_Annualized_USD_M"] = df_merged.apply(annualize_rd, axis=1)
    df_merged["Latest_Period_Label"] = df_merged.apply(get_period_label, axis=1)
    
    # Merge positioning
    df_pos = get_positioning(master, latest_financials)
    df_merged = df_merged.merge(df_pos, on="Unique_ID", how="left")
    df_merged = df_merged.rename(columns={"positioning": "Positioning"})
    
    # Load and merge expected zero UIDs to be robust
    ez_df = load_expected_zero()
    ez_uids = set(ez_df["Unique_ID"].tolist())
    
    # Merge clinical summary
    df_merged = df_merged.merge(
        status_summary[[
            "Unique_ID", "Expected_Zero",
            "Owned_Active_Phase_III_Count", "Owned_Active_Phase_Weighted_Score",
            "Owned_Active_Pipeline_Count", "Owned_Operational_Risk_Count",
            "Owned_Active_Phase_I_Count", "Owned_Active_Phase_II_Count",
            "Participated_Active_Phase_III_Count"
        ]],
        on="Unique_ID",
        how="left"
    )
    
    df_merged["Expected_Zero"] = df_merged["Expected_Zero"].fillna(False) | df_merged["Unique_ID"].isin(ez_uids)
    
    # Rename columns to match specifications
    df_merged = df_merged.rename(columns={
        "Owned_Active_Phase_III_Count": "Phase_III_Count_Active",
        "Owned_Active_Phase_Weighted_Score": "Phase_Weighted_Score_Active",
        "Owned_Active_Pipeline_Count": "Active_Pipeline_Count",
        "Owned_Operational_Risk_Count": "Operational_Risk_Count",
        "Owned_Active_Phase_I_Count": "Phase_I_Active_Count",
        "Owned_Active_Phase_II_Count": "Phase_II_Active_Count",
        "Participated_Active_Phase_III_Count": "Participated_Phase_III_Active_Count"
    })
    
    df_merged["Phase_III_Active_Count"] = df_merged["Phase_III_Count_Active"]
    
    # Filters
    df_filtered = df_merged[
        df_merged["RD_Annualized_USD_M"].notna() & (df_merged["RD_Annualized_USD_M"] > 0) &
        df_merged["Market_Cap_USD_M"].notna() & (df_merged["Market_Cap_USD_M"] > 0) &
        (df_merged["Expected_Zero"] != True)
    ].copy()
    
    return df_filtered.reset_index(drop=True)


@st.cache_data
def load_clinical_inventory_normalized() -> pd.DataFrame:
    """Load ClinicalTrials_Inventory_Normalized.csv with type coercion and date parsing."""
    path = DATA_DIR / "clinical_trials" / "ClinicalTrials_Inventory_Normalized.csv"
    expected_cols = [
        "Unique_ID", "Company_Name", "NCT_ID", "Brief_Title", "Official_Title",
        "Overall_Status", "Status_Bucket", "Status_Group", "Phases_Raw",
        "Phase_Bucket_Exclusive", "Phase_Buckets_Inclusive", "Phase_Weight",
        "Lead_Sponsor", "Collaborators", "Sponsor_Match_Type", "Sponsor_Match_Confidence",
        "Ownership_Context", "Counts_As_Owned_Trial", "Counts_As_Participated_In",
        "Conditions", "Interventions", "Study_Type", "Enrollment", "Start_Date",
        "Primary_Completion_Date", "Completion_Date", "Last_Update_Submit_Date",
        "Study_URL", "Reviewer_Notes"
    ]
    if not path.exists():
        return pd.DataFrame(columns=expected_cols)
    
    # Read the file preserving NCT_ID as string
    df = pd.read_csv(path, encoding="utf-8-sig", dtype={"NCT_ID": str})
    
    # Parse date columns where present
    date_cols = ["Last_Update_Submit_Date", "Start_Date", "Primary_Completion_Date", "Completion_Date", "Fetched_At_UTC"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", format="mixed", dayfirst=True)
            
    # Coerce booleans for owned/participated flags
    for col in ["Counts_As_Owned_Trial", "Counts_As_Participated_In"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper() == "TRUE"
            
    # If Study_URL is missing but NCT_ID exists, construct
    if "Study_URL" in df.columns:
        mask = df["Study_URL"].isna() & df["NCT_ID"].notna()
        df.loc[mask, "Study_URL"] = "https://clinicaltrials.gov/study/" + df.loc[mask, "NCT_ID"]
    else:
        df["Study_URL"] = ""
        mask = df["NCT_ID"].notna()
        df.loc[mask, "Study_URL"] = "https://clinicaltrials.gov/study/" + df.loc[mask, "NCT_ID"]

    # Keep only the expected columns that are present, and add missing ones
    for col in expected_cols:
        if col not in df.columns:
            df[col] = None
            
    return df[expected_cols]


@st.cache_data
def get_company_clinical_inventory(clinical_inventory: pd.DataFrame, uid: str, scope: str) -> pd.DataFrame:
    """Filter inventory by Unique_ID and scope, then sort by priority rules."""
    if clinical_inventory.empty:
        return clinical_inventory.copy()
        
    # Filter by Unique_ID
    df = clinical_inventory[clinical_inventory["Unique_ID"] == uid].copy()
    if df.empty:
        return df

    # Apply the chosen scope
    # scope values: "Owned footprint", "Participated / collaborator exposure"
    if scope == "Owned footprint":
        df = df[df["Counts_As_Owned_Trial"] == True]
    elif scope == "Participated / collaborator exposure":
        df = df[df["Counts_As_Participated_In"] == True]
        
    if df.empty:
        return df
        
    # Sort priority mapping
    status_prio_map = {
        "Active Pipeline": 0,
        "Operational Risk": 1,
        "Other": 2
    }
    phase_prio_map = {
        "Phase III": 0,
        "Phase II": 1,
        "Mixed Phase": 2,
        "Phase I": 3,
        "Other / NA": 4
    }
    
    # Create temp sort columns
    df["_status_prio"] = df["Status_Group"].fillna("Other").astype(str).str.strip().map(status_prio_map).fillna(2)
    df["_phase_prio"] = df["Phase_Bucket_Exclusive"].fillna("Other / NA").astype(str).str.strip().map(phase_prio_map).fillna(4)
    
    # Sort by:
    # 1. _status_prio ascending
    # 2. _phase_prio ascending
    # 3. Last_Update_Submit_Date descending
    df = df.sort_values(
        by=["_status_prio", "_phase_prio", "Last_Update_Submit_Date"],
        ascending=[True, True, False]
    )
    
    # Drop temp columns
    df = df.drop(columns=["_status_prio", "_phase_prio"])
    
    return df


@st.cache_data
def load_clinical_change_feed() -> pd.DataFrame:
    """Load ClinicalTrials_Change_Feed.csv with type coercion and date parsing. Returns empty if missing."""
    path = DATA_DIR / "clinical_trials" / "ClinicalTrials_Change_Feed.csv"
    expected_cols = [
        "Event_ID", "Run_ID", "Detected_At_UTC", "Snapshot_Date_Current", "Snapshot_Date_Previous",
        "Unique_ID", "Company_Name", "NCT_ID", "Brief_Title", "Study_URL",
        "Change_Type", "Change_Priority", "Previous_Status_Bucket", "Current_Status_Bucket",
        "Previous_Overall_Status_Raw", "Current_Overall_Status_Raw",
        "Previous_Phase_Bucket_Exclusive", "Current_Phase_Bucket_Exclusive",
        "Previous_Phases_Raw", "Current_Phases_Raw", "Previous_Sponsor_Match_Type",
        "Current_Sponsor_Match_Type", "Previous_Ownership_Context", "Current_Ownership_Context",
        "Counts_As_Owned_Trial_Previous", "Counts_As_Owned_Trial_Current",
        "Counts_As_Participated_In_Previous", "Counts_As_Participated_In_Current",
        "Changed_Fields_Detail", "Window_30D", "Window_90D", "Last_Update_Submit_Date",
        "Reviewer_Notes"
    ]
    if not path.exists():
        return pd.DataFrame(columns=expected_cols)
    
    # Read preserving NCT_ID as string
    df = pd.read_csv(path, encoding="utf-8-sig", dtype={"NCT_ID": str})
    
    if df.empty:
        return pd.DataFrame(columns=expected_cols)
        
    # Parse Detected_At_UTC as datetime
    if "Detected_At_UTC" in df.columns:
        df["Detected_At_UTC"] = pd.to_datetime(df["Detected_At_UTC"], errors="coerce", format="mixed", dayfirst=True)
        
    # Parse booleans Window_30D and Window_90D robustly if present
    for col in ["Window_30D", "Window_90D"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper() == "TRUE"
            
    # Construct Study_URL from NCT_ID if missing
    if "Study_URL" in df.columns:
        mask = df["Study_URL"].isna() & df["NCT_ID"].notna()
        df.loc[mask, "Study_URL"] = "https://clinicaltrials.gov/study/" + df.loc[mask, "NCT_ID"]
    else:
        df["Study_URL"] = ""
        mask = df["NCT_ID"].notna()
        df.loc[mask, "Study_URL"] = "https://clinicaltrials.gov/study/" + df.loc[mask, "NCT_ID"]
        
    # Keep only the expected columns that are present, and add missing ones
    for col in expected_cols:
        if col not in df.columns:
            df[col] = None
            
    return df[expected_cols]


def _coerce_active_flag(series: pd.Series) -> pd.Series:
    """Return a robust boolean active flag from TRUE/Y/YES/1-style values."""
    return series.astype(str).str.strip().str.upper().isin(["TRUE", "Y", "YES", "1"])


@st.cache_data
def load_therapeutic_area_taxonomy() -> pd.DataFrame:
    """Load Therapeutic_Area_Taxonomy.csv with robust type coercion."""
    path = DATA_DIR / "dictionaries" / "Therapeutic_Area_Taxonomy.csv"
    df = pd.read_csv(path, encoding="utf-8-sig")

    if "Is_Active" in df.columns:
        df["Is_Active"] = _coerce_active_flag(df["Is_Active"])
    else:
        df["Is_Active"] = True

    if "Display_Order" in df.columns:
        df["Display_Order"] = pd.to_numeric(df["Display_Order"], errors="coerce")
    else:
        df["Display_Order"] = range(1, len(df) + 1)

    for col in ["Therapeutic_Area", "Profile_Column"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    return df


@st.cache_data
def load_modality_taxonomy() -> pd.DataFrame:
    """Load Modality_Taxonomy.csv with robust type coercion."""
    path = DATA_DIR / "dictionaries" / "Modality_Taxonomy.csv"
    df = pd.read_csv(path, encoding="utf-8-sig")

    if "Is_Active" in df.columns:
        df["Is_Active"] = _coerce_active_flag(df["Is_Active"])
    else:
        df["Is_Active"] = True

    if "Display_Order" in df.columns:
        df["Display_Order"] = pd.to_numeric(df["Display_Order"], errors="coerce")
    else:
        df["Display_Order"] = range(1, len(df) + 1)

    for col in ["Modality_Name", "Profile_Column"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    return df




