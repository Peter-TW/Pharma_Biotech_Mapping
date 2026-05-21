"""
app.py — Biopharma Command Center (MVP-1)
Single-page Streamlit dashboard.
"""

import html
import pandas as pd
import streamlit as st

from data import load_master, load_financials, get_latest_financials, get_lifecycle, get_positioning
from charts import render_lifecycle_strip, render_financial_trend, render_intelligence_map

st.set_page_config(
    page_title="Biopharma Command Center",
    page_icon="💊",
    layout="wide",
)

# Force dark theme palette
st.markdown(
    """
    <style>
    .stApp, [data-testid="stAppViewContainer"], .block-container {
        background-color: #0E1117 !important;
        color: #E6E9EF !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Banner ──────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="padding:18px 22px; border-radius:10px; margin-bottom:10px;
                background:linear-gradient(90deg, rgba(16,36,48,0.55),
                rgba(26,31,43,0.95)); border:1px solid #2A2E3A;">
      <div style="font-size:24px; font-weight:700; color:#E6E9EF;">
        💊 Biopharma Command Center
      </div>
      <div style="font-size:13px; color:#8A91A0; margin-top:2px;">
        Company intelligence map &middot; sector overview, lifecycle footprint,
        financial snapshot &amp; trend
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Load data ───────────────────────────────────────────────────────
master = load_master()
financials = load_financials()
latest = get_latest_financials(financials)
lifecycle_df = get_lifecycle(master)
positioning_df = get_positioning(master, latest)

from data import load_data_notes
data_notes = load_data_notes()

FULL_CYCLE_LABEL = "Full-cycle (all 5 stages)"
QUARTERS = ["Q1", "Q2", "Q3", "Q4"]
METRICS = {
    "Revenue": "Q_Revenue",
    "R&D": "Q_RD",
    "SG&A": "Q_SGA",
    "Cash": "Q_Cash",
    "Market Cap": "Market_Cap_USD_M",
}


# ── Formatting helpers ──────────────────────────────────────────────

def fmt_money(value):
    """USD millions -> compact string ($X.XXT / $X.XB / $XXXM). NaN -> em dash."""
    if pd.isna(value):
        return "—"
    a = abs(value)
    if a >= 1_000_000:
        return f"${value / 1_000_000:,.2f}T"
    if a >= 1000:
        return f"${value / 1000:,.1f}B"
    return f"${value:,.0f}M"


def fmt_multiple(value):
    if pd.isna(value):
        return "—"
    return f"{value:.2f}\u00d7"


def fmt_pct(value):
    if pd.isna(value):
        return "—"
    return f"{value:.1%}"


def field(value):
    """Display a master/financials field, or an em dash if blank/NaN."""
    s = "" if value is None else str(value).strip()
    if s == "" or s.lower() == "nan":
        return "—"
    return s


def get_company_note(uid, scope="ALL"):
    """Return (Status_Label, Tooltip) for a company at a given scope,
    or (None, None) if no matching note exists."""
    if data_notes.empty:
        return (None, None)
    sub = data_notes[
        (data_notes["Unique_ID"] == uid) &
        (data_notes["Period_Type_Scope"] == scope)
    ]
    if sub.empty:
        return (None, None)
    row = sub.iloc[0]
    label = row.get("Status_Label")
    tip = row.get("Tooltip")
    return (
        str(label).strip() if pd.notna(label) else None,
        str(tip).strip() if pd.notna(tip) else None,
    )


# ── Sidebar: lifecycle filter + company selector ────────────────────
lifecycle_choice = st.sidebar.radio(
    "Lifecycle filter",
    ["All companies", "Full-cycle only", "Non-full-cycle only"],
)

full_ids = set(
    lifecycle_df.loc[lifecycle_df["lifecycle_profile"] == FULL_CYCLE_LABEL, "Unique_ID"]
)
if lifecycle_choice == "Full-cycle only":
    pool = master[master["Unique_ID"].isin(full_ids)]
elif lifecycle_choice == "Non-full-cycle only":
    pool = master[~master["Unique_ID"].isin(full_ids)]
else:
    pool = master

# Default the selector to the largest company (by latest market cap) in view.
mcap_by_id = latest.set_index("Unique_ID")["Market_Cap_USD_M"]
pool = pool.assign(_mcap=pool["Unique_ID"].map(mcap_by_id))

pool_clean = pool[pool["Company Name"].notna()].copy()
pool_clean = pool_clean.sort_values("Company Name")

labels = []
label_to_uid = {}
uid_to_name = {}

for _, row in pool_clean.iterrows():
    name = row["Company Name"]
    ticker = row.get("Ticker")
    if pd.isna(ticker) or str(ticker).strip() == "" or str(ticker).lower() == "nan":
        lbl = name
    else:
        lbl = f"{name} ({str(ticker).strip()})"
    labels.append(lbl)
    label_to_uid[lbl] = row["Unique_ID"]
    uid_to_name[row["Unique_ID"]] = name

flagship_row = pool_clean.sort_values("_mcap", ascending=False).iloc[0]
flagship_name = flagship_row["Company Name"]
flagship_ticker = flagship_row.get("Ticker")
if pd.isna(flagship_ticker) or str(flagship_ticker).strip() == "" or str(flagship_ticker).lower() == "nan":
    flagship_label = flagship_name
else:
    flagship_label = f"{flagship_name} ({str(flagship_ticker).strip()})"

default_index = labels.index(flagship_label)

selected_label = st.sidebar.selectbox(
    "Select company", labels, index=default_index
)
st.sidebar.caption(f"{len(labels)} of {len(master)} companies shown")

uid = label_to_uid[selected_label]
selected_name = uid_to_name[uid]

company_row = master[master["Unique_ID"] == uid].iloc[0]
company_fin = financials[financials["Unique_ID"] == uid].copy()

latest_row = latest[latest["Unique_ID"] == uid]
lr = latest_row.iloc[0] if not latest_row.empty else None
period_label = (
    f"{lr['Period_Type']} {int(lr['Calendar_Year'])}" if lr is not None else "—"
)

# ── Sector Overview (reflects the lifecycle filter) ─────────────────
pool_ids = set(pool["Unique_ID"])
combined_mcap = latest.loc[
    latest["Unique_ID"].isin(pool_ids), "Market_Cap_USD_M"
].sum()

# Reference quarter = the most recent quarter with BROAD coverage (most
# companies reporting), not the leading edge where only 1-2 firms have filed.
q_rows = financials[
    financials["Period_Type"].isin(QUARTERS) & financials["Q_Revenue"].notna()
].copy()
q_rows["_q"] = q_rows["Period_Type"].map({"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4})
coverage = (
    q_rows.groupby(["Calendar_Year", "_q", "Period_Type"])["Unique_ID"]
    .nunique()
    .reset_index(name="n")
)
# Coverage floor: prefer the most recent quarter where at least 80% of the
# companies in view have reported. Falls back to broadest-coverage if no
# quarter clears the floor.
pool_size = len(pool_ids) if len(pool_ids) > 0 else len(master)
threshold = max(1, int(0.80 * pool_size))
qualifying = coverage[coverage["n"] >= threshold].sort_values(
    ["Calendar_Year", "_q"], ascending=[False, False]
)
if not qualifying.empty:
    ref_year = int(qualifying.iloc[0]["Calendar_Year"])
    ref_q = qualifying.iloc[0]["Period_Type"]
else:
    fallback = coverage.sort_values(
        ["n", "Calendar_Year", "_q"], ascending=[False, False, False]
    )
    ref_year = int(fallback.iloc[0]["Calendar_Year"])
    ref_q = fallback.iloc[0]["Period_Type"]

period_rows = financials[
    (financials["Period_Type"] == ref_q)
    & (financials["Calendar_Year"] == ref_year)
    & (financials["Unique_ID"].isin(pool_ids))
]
combined_rev = period_rows["Q_Revenue"].sum()
n_reporting = int(period_rows["Q_Revenue"].notna().sum())

with st.container(border=True):
    st.subheader("Sector Overview")
    s1, s2, s3 = st.columns(3)
    s1.metric("Companies in view", str(len(pool_ids)))
    s2.metric("Combined Market Cap", fmt_money(combined_mcap))
    s3.metric(f"Combined Revenue · {ref_q} {ref_year}", fmt_money(combined_rev))
    st.caption(
        "Totals reflect the lifecycle filter. Market cap is summed at each "
        "company's latest reported date (approximate). Revenue is the combined "
        f"{ref_q} {ref_year} figure — the latest quarter "
        f"with at least 80% of companies reporting — from {n_reporting} of "
        f"{len(pool_ids)} companies that reported that period."
    )

# ── Intelligence Map ────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("Intelligence Map")
    plot_df = pool[["Unique_ID", "Company Name", "Commercial"]].merge(
        latest[["Unique_ID", "Q_Revenue", "rd_intensity", "Market_Cap_USD_M", "Period_Type"]],
        on="Unique_ID",
        how="left"
    ).merge(
        positioning_df[["Unique_ID", "positioning"]],
        on="Unique_ID",
        how="left"
    )
    plot_df = plot_df.rename(columns={"Commercial": "is_commercial"})
    render_intelligence_map(plot_df, uid)
    
    map_label, map_tip = get_company_note(uid, "INTELLIGENCE_MAP")
    if map_label:
        st.caption(f"ℹ️ {selected_name}: {map_tip}")

# ── Header ──────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown(f"### {selected_name}")
    st.markdown(
        f"**Ticker:** {field(company_row.get('Ticker'))} &nbsp;·&nbsp; "
        f"**Exchange:** {field(company_row.get('Exchange'))} &nbsp;·&nbsp; "
        f"**Market Segment:** {field(company_row.get('Market Segment'))} "
        f"&nbsp;·&nbsp; **Latest Period:** {period_label}"
    )
    sel_pos = positioning_df.loc[positioning_df["Unique_ID"] == uid, "positioning"].iloc[0]
    
    # Calculate freshness badge
    if lr is not None and pd.notna(lr.get("Calendar_Year")):
        year = int(lr["Calendar_Year"])
        if year >= 2026:
            freshness = "Current"
        elif year == 2025:
            freshness = "Lagging"
        else:
            freshness = "Stale"
    else:
        freshness = "Stale"

    status_label, status_tooltip = get_company_note(uid, "ALL")
    badge_html = (
        f'&nbsp;&nbsp;'
        f'<span title="{html.escape(status_tooltip or "")}" '
        f'style="background:rgba(243,156,18,0.16); '
        f'border:1px solid #F39C12; border-radius:6px; '
        f'padding:3px 10px; font-size:13px; color:#E6E9EF;">'
        f'Data Status &nbsp;<b>{html.escape(status_label)}</b></span>'
    ) if status_label else ""

    st.markdown(
        f'<span style="background:rgba(0,180,216,0.16); border:1px solid #00B4D8; '
        f'border-radius:6px; padding:3px 10px; font-size:13px; color:#E6E9EF;">'
        f'Positioning &nbsp;<b>{sel_pos}</b></span>'
        f'&nbsp;&nbsp;'
        f'<span style="background:rgba(0,180,216,0.16); border:1px solid #00B4D8; '
        f'border-radius:6px; padding:3px 10px; font-size:13px; color:#E6E9EF;">'
        f'Freshness &nbsp;<b>{freshness}</b></span>'
        f'{badge_html}',
        unsafe_allow_html=True,
    )

# ── Lifecycle Footprint ─────────────────────────────────────────────
with st.container(border=True):
    st.subheader("Lifecycle Footprint")
    lc_row = lifecycle_df[lifecycle_df["Unique_ID"] == uid].iloc[0]
    render_lifecycle_strip(lc_row)

# ── Financial Snapshot ──────────────────────────────────────────────
with st.container(border=True):
    st.subheader("Financial Snapshot")
    st.markdown(
        '<span style="background:rgba(0,180,216,0.16); border:1px solid #00B4D8; '
        'border-radius:6px; padding:3px 10px; font-size:13px; color:#E6E9EF;">'
        f"Latest reported period &nbsp;<b>{period_label}</b></span>",
        unsafe_allow_html=True,
    )
    st.write("")
    if lr is not None:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Revenue", fmt_money(lr["Q_Revenue"]))
        c2.metric("R&D", fmt_money(lr["Q_RD"]))
        c3.metric("SG&A", fmt_money(lr["Q_SGA"]))
        c4.metric("Cash", fmt_money(lr["Q_Cash"]))

        c5, c6, c7 = st.columns(3)
        c5.metric("Market Cap", fmt_money(lr["Market_Cap_USD_M"]))
        c6.metric("R&D Intensity", fmt_multiple(lr["rd_intensity"]),
                  help="R&D \u00f7 Revenue")
        c7.metric("Cash / Market Cap", fmt_pct(lr["cash_to_mktcap"]),
                  help="Cash \u00f7 Market Cap")

        st.caption(
            "All figures in USD. Cash and Market Cap are point-in-time snapshots. "
            "Some companies show \u201c\u2014\u201d for a metric where their "
            "official financial reports do not separately disclose that line item "
            "(for example, R&D or SG&A bundled into broader expense categories). "
            "In those cases we leave the value blank rather than estimating from "
            "mixed totals \u2014 see the company\u2019s Data Status badge for "
            "specifics."
        )
    else:
        st.info("No financial data available for this company.")

# ── Financial Trend ─────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("Financial Trend")
    metric_label = st.selectbox("Metric", list(METRICS.keys()), index=0)
    if not company_fin.empty:
        render_financial_trend(company_fin, metric_label, METRICS[metric_label])
    else:
        st.info("No reporting data available.")

    status_label, _ = get_company_note(uid, "ALL")
    partial_metrics = {"R&D", "SG&A", "Cash"}
    if (status_label == "Accepted partial"
        and metric_label in partial_metrics
        and not company_fin.empty):
        st.caption(
            f"\u26A0\uFE0F  {metric_label} values shown here come from legacy "
            f"data sources. {selected_name} does not separately disclose this "
            f"line item in its official consolidated financial results \u2014 line "
            f"items are bundled into broader expense categories. The latest "
            f"period reflects this (value shown as \u201c\u2014\u201d in the "
            f"Financial Snapshot above). Earlier periods are preserved for "
            f"trend context but are tagged "
            f"[LEGACY_SGA_UNAUDITED] in the data and have not been audited "
            f"against the company\u2019s primary filings."
        )

# ── Data Sources ────────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("Data Sources")
    fin_sources = sorted(
        str(s) for s in company_fin["Source"].dropna().unique() if str(s).strip()
    )
    st.markdown(f"**Company profile source:** {field(company_row.get('Data Source'))}")
    st.markdown(
        "**Financial data sources:** "
        + (", ".join(fin_sources) if fin_sources else "—")
    )
    st.markdown(
        f"**Reporting standard:** {field(company_row.get('Reporting_Standard'))}"
    )
    st.markdown(f"**Reporting currency:** {field(company_row.get('Currency'))}")
    n_complete = (company_fin["Row_Data_Status"].astype(str).str.strip().str.lower() == "complete").sum()
    n_derived = (company_fin["Row_Data_Status"].astype(str).str.strip().str.lower() == "derived").sum()
    n_manual = (company_fin["Manual_Review_Required"].astype(str).str.strip().str.lower() == "yes").sum()
    st.markdown(
        f"**Row status:** {n_complete} complete · {n_derived} derived · {n_manual} manual-review"
    )

    manual_used = (
        company_fin["Manual_Data_Source"].astype(str).str.strip().str.lower() == "yes"
    ).any()
    if manual_used:
        st.caption("Some periods include manually extracted (IR / PDF) data.")
