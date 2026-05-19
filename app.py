"""
app.py — Biopharma Command Center (MVP-1)
Single-page Streamlit dashboard.
"""

import pandas as pd
import streamlit as st

from data import load_master, load_financials, get_latest_financials, get_lifecycle
from charts import render_lifecycle_strip, render_financial_trend

st.set_page_config(
    page_title="Biopharma Command Center",
    page_icon="💊",
    layout="wide",
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
company_names = sorted(pool["Company Name"].dropna().tolist())
flagship = pool.sort_values("_mcap", ascending=False)["Company Name"].iloc[0]
default_index = company_names.index(flagship)

selected_name = st.sidebar.selectbox(
    "Select company", company_names, index=default_index
)
st.sidebar.caption(f"{len(company_names)} of {len(master)} companies shown")

company_row = master[master["Company Name"] == selected_name].iloc[0]
uid = company_row["Unique_ID"]
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

# Most recent quarter present anywhere in the data (like-for-like revenue sum).
q_rows = financials[financials["Period_Type"].isin(QUARTERS)].copy()
q_rows["_q"] = q_rows["Period_Type"].map({"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4})
q_rows = q_rows.sort_values(["Calendar_Year", "_q"])
latest_year = int(q_rows["Calendar_Year"].iloc[-1])
latest_q = q_rows.loc[q_rows["Calendar_Year"] == latest_year, "Period_Type"].iloc[-1]

period_rows = financials[
    (financials["Period_Type"] == latest_q)
    & (financials["Calendar_Year"] == latest_year)
    & (financials["Unique_ID"].isin(pool_ids))
]
combined_rev = period_rows["Q_Revenue"].sum()
n_reporting = int(period_rows["Q_Revenue"].notna().sum())

with st.container(border=True):
    st.subheader("Sector Overview")
    s1, s2, s3 = st.columns(3)
    s1.metric("Companies in view", str(len(pool_ids)))
    s2.metric("Combined Market Cap", fmt_money(combined_mcap))
    s3.metric(f"Combined Revenue · {latest_q} {latest_year}", fmt_money(combined_rev))
    st.caption(
        "Totals reflect the lifecycle filter. Market cap is summed at each "
        "company's latest reported date (approximate). Revenue is the combined "
        f"{latest_q} {latest_year} figure from {n_reporting} of {len(pool_ids)} "
        "companies that reported that period."
    )

# ── Header ──────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown(f"### {selected_name}")
    st.markdown(
        f"**Ticker:** {field(company_row.get('Ticker'))} &nbsp;·&nbsp; "
        f"**Exchange:** {field(company_row.get('Exchange'))} &nbsp;·&nbsp; "
        f"**Market Segment:** {field(company_row.get('Market Segment'))} "
        f"&nbsp;·&nbsp; **Latest Period:** {period_label}"
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
            "All figures in USD. Cash and Market Cap are point-in-time snapshots."
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

    manual_used = (
        company_fin["Manual_Data_Source"].astype(str).str.strip().str.lower() == "yes"
    ).any()
    if manual_used:
        st.caption("Some periods include manually extracted (IR / PDF) data.")
