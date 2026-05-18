"""
app.py — Biopharma Command Center (MVP-1)
Single-page Streamlit dashboard with 6 modules.
"""

import pandas as pd
import streamlit as st

from data import load_master, load_financials, get_latest_financials, get_lifecycle
from charts import render_lifecycle_strip, render_reporting_timeline

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
        Company intelligence map &middot; lifecycle footprint, financial
        snapshot &amp; reporting audit
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


# ── Formatting helpers ──────────────────────────────────────────────

def fmt_money(value):
    """USD millions -> compact string ($X.XB or $XXXM). NaN -> em dash."""
    if pd.isna(value):
        return "—"
    if abs(value) >= 1000:
        return f"${value / 1000:,.1f}B"
    return f"${value:,.0f}M"


def fmt_multiple(value):
    """Ratio as a multiple, e.g. 0.20x. NaN -> em dash."""
    if pd.isna(value):
        return "—"
    return f"{value:.2f}\u00d7"


def fmt_pct(value):
    """Ratio as a percentage. NaN -> em dash."""
    if pd.isna(value):
        return "—"
    return f"{value:.1%}"


# ── Module 1: Sidebar — Company Selector ────────────────────────────
company_names = sorted(master["Company Name"].dropna().tolist())
selected_name = st.sidebar.selectbox("Select Company", company_names)
st.sidebar.caption(f"{len(company_names)} companies · MVP-1")

company_row = master[master["Company Name"] == selected_name].iloc[0]
uid = company_row["Unique_ID"]

latest_row = latest[latest["Unique_ID"] == uid]
lr = latest_row.iloc[0] if not latest_row.empty else None
period_label = (
    f"{lr['Period_Type']} {int(lr['Calendar_Year'])}" if lr is not None else "—"
)

# ── Module 2: Header ────────────────────────────────────────────────
with st.container(border=True):
    st.markdown(f"### {selected_name}")
    st.markdown(
        f"**Ticker:** {company_row['Ticker']} &nbsp;·&nbsp; "
        f"**Exchange:** {company_row['Exchange']} &nbsp;·&nbsp; "
        f"**Market Segment:** {company_row['Market Segment']} &nbsp;·&nbsp; "
        f"**Latest Period:** {period_label}"
    )

# ── Module 3: Lifecycle Footprint ───────────────────────────────────
with st.container(border=True):
    st.subheader("Lifecycle Footprint")
    lc_row = lifecycle_df[lifecycle_df["Unique_ID"] == uid].iloc[0]
    render_lifecycle_strip(lc_row, lifecycle_df, master)

# ── Module 4: Financial Snapshot ────────────────────────────────────
with st.container(border=True):
    st.subheader("Financial Snapshot")
    if lr is not None:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Revenue", fmt_money(lr["Q_Revenue"]), help=f"Period: {period_label}")
        c2.metric("R&D", fmt_money(lr["Q_RD"]), help=f"Period: {period_label}")
        c3.metric("SG&A", fmt_money(lr["Q_SGA"]), help=f"Period: {period_label}")
        c4.metric("Cash", fmt_money(lr["Q_Cash"]), help=f"Period: {period_label}")

        c5, c6, c7 = st.columns(3)
        c5.metric("Market Cap", fmt_money(lr["Market_Cap_USD_M"]),
                  help=f"Period: {period_label}")
        c6.metric("R&D Intensity", fmt_multiple(lr["rd_intensity"]),
                  help="R&D \u00f7 Revenue")
        c7.metric("Cash / Market Cap", fmt_pct(lr["cash_to_mktcap"]),
                  help="Cash \u00f7 Market Cap")

        st.caption(
            f"All figures for **{period_label}**, USD. "
            "Cash and Market Cap are point-in-time snapshots."
        )
    else:
        st.info("No financial data available for this company.")

# ── Module 5: Reporting Timeline ────────────────────────────────────
company_fin = financials[financials["Unique_ID"] == uid].copy()
with st.container(border=True):
    st.subheader("Reporting Timeline (2024–2026)")
    if not company_fin.empty:
        render_reporting_timeline(company_fin)
    else:
        st.info("No reporting data available.")

# ── Module 6: Data Quality ──────────────────────────────────────────
with st.container(border=True):
    st.subheader("Data Quality")
    if not company_fin.empty:
        flags_found = False

        manual_rows = company_fin[
            company_fin["Manual_Review_Required"].astype(str)
            .str.strip().str.lower() == "yes"
        ]
        if not manual_rows.empty:
            flags_found = True
            st.markdown("**Periods requiring manual review:**")
            for _, r in manual_rows.iterrows():
                date = (
                    r["Quarter_End_Date"].strftime("%d/%m/%Y")
                    if pd.notna(r["Quarter_End_Date"]) else "—"
                )
                st.markdown(
                    f"- {r['Period_Type']} {int(r['Calendar_Year'])} ({date})"
                )

        derived_count = (
            company_fin["Derived_Row_Flag"].astype(str)
            .str.strip().str.upper() == "TRUE"
        ).sum()
        if derived_count > 0:
            flags_found = True
            st.markdown(f"**Derived rows:** {derived_count}")

        missing = [
            m for m in company_fin["Missing_Periods"].dropna().unique()
            if str(m).strip()
        ]
        if missing:
            flags_found = True
            st.markdown(f"**Missing periods:** {', '.join(str(m) for m in missing)}")

        notes = [
            n for n in company_fin["Reviewer_Notes"].dropna().unique()
            if str(n).strip()
        ]
        if notes:
            flags_found = True
            with st.expander("Reviewer Notes"):
                for note in notes:
                    st.markdown(f"- {note}")

        if not flags_found:
            st.success("No data-quality flags.")
    else:
        st.info("No financial data available.")
