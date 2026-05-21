"""
app.py — Biopharma Command Center (MVP-1)
Single-page Streamlit dashboard.
"""

import html
import math
import altair as alt
import pandas as pd
import streamlit as st

from data import load_master, load_financials, get_latest_financials, get_lifecycle, get_positioning, get_sector_ratio_trend
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


def fmt_period_label(row):
    if row is None:
        return "—"
    period_type = row.get("Period_Type", "—")
    year_val = row.get("Calendar_Year")
    year_str = str(int(year_val)) if pd.notna(year_val) else ""
    
    disclosed = f"{period_type} {year_str}".strip()
    cal_q = row.get("Calendar_Quarter")
    if pd.notna(cal_q) and str(cal_q).strip():
        cal_q_str = str(cal_q).strip()
        calendar = f"Calendar {cal_q_str} {year_str}".strip()
        if calendar.replace("Calendar ", "") != disclosed:
            return f"{disclosed} · {calendar}"
        return disclosed
    return disclosed


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
period_label = fmt_period_label(lr)

# ── Sector Overview (reflects the lifecycle filter) ─────────────────
pool_ids = frozenset(pool["Unique_ID"])
combined_mcap = latest.loc[
    latest["Unique_ID"].isin(pool_ids), "Market_Cap_USD_M"
].sum()

# Reference quarter = the most recent CALENDAR quarter with BROAD coverage
# for the current lifecycle filter. Keep Period_Type only as a quarterly-row
# filter; use Calendar_Quarter as the market-time bucket so fiscal-quarter
# reporters land in the correct calendar period.
q_rows = financials[
    financials["Period_Type"].isin(QUARTERS)
    & financials["Calendar_Quarter"].isin(QUARTERS)
    & financials["Q_Revenue"].notna()
    & financials["Unique_ID"].isin(pool_ids)
].copy()
q_rows["_q"] = q_rows["Calendar_Quarter"].map({"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4})
coverage = (
    q_rows.groupby(["Calendar_Year", "_q", "Calendar_Quarter"])["Unique_ID"]
    .nunique()
    .reset_index(name="n")
)
# Coverage floor: prefer the most recent calendar quarter where at least 80%
# of companies in view reported quarterly revenue. Falls back to the broadest
# available calendar quarter if no quarter clears the floor.
pool_size = len(pool_ids) if len(pool_ids) > 0 else len(master)
threshold = max(1, math.ceil(0.80 * pool_size))
qualifying = coverage[coverage["n"] >= threshold].sort_values(
    ["Calendar_Year", "_q"], ascending=[False, False]
)
used_coverage_floor = not qualifying.empty
if used_coverage_floor:
    ref_year = int(qualifying.iloc[0]["Calendar_Year"])
    ref_q = qualifying.iloc[0]["Calendar_Quarter"]
else:
    fallback = coverage.sort_values(
        ["n", "Calendar_Year", "_q"], ascending=[False, False, False]
    )
    if fallback.empty:
        ref_year = None
        ref_q = None
    else:
        ref_year = int(fallback.iloc[0]["Calendar_Year"])
        ref_q = fallback.iloc[0]["Calendar_Quarter"]

if ref_year is not None and ref_q is not None:
    period_rows = financials[
        (financials["Calendar_Year"] == ref_year)
        & (financials["Calendar_Quarter"] == ref_q)
        & (financials["Period_Type"].isin(QUARTERS))
        & (financials["Unique_ID"].isin(pool_ids))
    ]
    combined_rev = period_rows["Q_Revenue"].sum()
    n_reporting = int(period_rows.loc[period_rows["Q_Revenue"].notna(), "Unique_ID"].nunique())
else:
    period_rows = pd.DataFrame()
    combined_rev = pd.NA
    n_reporting = 0

# Calculate Sector Trend dataset & latest plotted point (Priority 4)
trend_df = get_sector_ratio_trend(financials, pool_ids, min_coverage_pct=0.50)
if not trend_df.empty:
    max_trend_row = trend_df.sort_values("Sort_Key").iloc[-1]
    latest_trend_q = max_trend_row["Calendar_Quarter"]
    latest_trend_year = int(max_trend_row["Calendar_Year"])
    latest_trend_label = f"Calendar {latest_trend_q} {latest_trend_year}"
    max_plotted_sort_key = int(max_trend_row["Sort_Key"])
else:
    latest_trend_label = "None"
    max_plotted_sort_key = 0

# Check for hidden leading edge quarters
q_raw = financials[
    financials["Unique_ID"].isin(pool_ids)
    & financials["Period_Type"].isin(QUARTERS)
    & financials["Calendar_Quarter"].isin(QUARTERS)
].copy()
if not q_raw.empty:
    q_raw["_q"] = q_raw["Calendar_Quarter"].map({"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4})
    q_raw["Sort_Key"] = q_raw["Calendar_Year"] * 10 + q_raw["_q"]
    max_raw_sort_key = int(q_raw["Sort_Key"].max())
else:
    max_raw_sort_key = 0

has_hidden = max_raw_sort_key > max_plotted_sort_key

# Render Data Freshness Summary Card (Priority 4)
overview_label = f"Calendar {ref_q} {ref_year}" if ref_q is not None else "No quarterly data"
trend_label = latest_trend_label if latest_trend_label != "None" else "No quarterly data"
hidden_clause = " Sparse leading-edge quarters are hidden from sector trends until coverage improves." if has_hidden else ""

freshness_text = (
    f"Latest broad-coverage quarter: <b>{overview_label}</b>. "
    f"Latest eligible sector trend point: <b>{trend_label}</b>."
    f"{hidden_clause}"
)

st.markdown(
    f'<div style="font-size:13px; color:#E6E9EF; margin-bottom:15px; '
    f'padding:8px 12px; border-radius:6px; background-color:#1A1F2B; border:1px solid #2A2E3A;">'
    f'ℹ️ &nbsp;{freshness_text}'
    f'</div>',
    unsafe_allow_html=True
)

with st.container(border=True):
    st.subheader("Sector Overview")
    s1, s2, s3 = st.columns(3)
    s1.metric("Companies in view", str(len(pool_ids)))
    s2.metric("Combined Market Cap", fmt_money(combined_mcap))
    revenue_label = f"Calendar {ref_q} {ref_year}" if ref_q is not None else "No quarterly data"
    s3.metric(f"Combined Revenue · {revenue_label}", fmt_money(combined_rev))

    if ref_q is not None:
        coverage_phrase = (
            "the latest calendar quarter with at least 80% of companies in view "
            "reporting quarterly revenue"
            if used_coverage_floor
            else "the broadest available calendar quarter because no quarter cleared "
                 "the 80% coverage floor"
        )
        st.caption(
            "Totals reflect the lifecycle filter. Market cap is summed at each "
            "company's latest reported date (approximate). Revenue is the combined "
            f"calendar {ref_q} {ref_year} figure — {coverage_phrase} — from "
            f"{n_reporting} of {len(pool_ids)} companies. Fiscal-quarter labels are "
            "grouped by Calendar_Quarter, while Period_Type is used only to exclude "
            "FY, H1 and 9M rows from this quarterly sector view."
        )
    else:
        st.caption(
            "Totals reflect the lifecycle filter. Market cap is summed at each "
            "company's latest reported date (approximate). No Q1-Q4 revenue rows "
            "are available for the current lifecycle filter."
        )


# ── Sector Trend ────────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("Sector Trend")
    ratio_options = ["R&D Intensity", "Cash / Market Cap", "SG&A Intensity"]
    ratio_metric = st.selectbox(
        "Sector ratio",
        ratio_options,
        index=0,
        help=(
            "All ratios are dollar-weighted aggregate ratios using quarterly "
            "rows only: Σ numerator ÷ Σ denominator."
        ),
    )

    if trend_df.empty:
        st.info("No quarterly sector trend data available for the current lifecycle filter.")
    else:
        metric_df = trend_df[trend_df["Metric"] == ratio_metric].copy()
        metric_df = metric_df[metric_df["Value"].notna()]

        if metric_df.empty:
            st.info(f"No usable {ratio_metric} data available for this lifecycle filter.")
        else:
            chart = (
                alt.Chart(metric_df)
                .mark_line(point=True)
                .encode(
                    x=alt.X("Period:N", sort=list(metric_df["Period"]), title="Calendar quarter"),
                    y=alt.Y("Value:Q", title=ratio_metric, axis=alt.Axis(format="%")),
                    tooltip=[
                        alt.Tooltip("Period:N", title="Period"),
                        alt.Tooltip("Value:Q", title=ratio_metric, format=".1%"),
                        alt.Tooltip("Definition:N", title="Definition"),
                        alt.Tooltip("Contributing_Companies:Q", title="Companies in metric"),
                        alt.Tooltip("Reporting_Companies:Q", title="Quarterly reporters"),
                        alt.Tooltip("Companies_In_View:Q", title="Companies in filter"),
                        alt.Tooltip("Coverage:Q", title="Coverage", format=".0%"),
                    ],
                )
                .properties(height=280)
            )
            st.altair_chart(chart, use_container_width=True)

            latest_point = metric_df.sort_values("Sort_Key").iloc[-1]

            # Priority 1: Coverage Badges
            st.markdown(
                f'<div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom:10px; margin-top:5px;">'
                f'<span style="background:rgba(0,180,216,0.12); border:1px solid rgba(0,180,216,0.3); border-radius:6px; padding:4px 12px; font-size:12px; color:#E6E9EF;">'
                f'Metric contributors: &nbsp;<b>{int(latest_point["Contributing_Companies"])}</b></span>'
                f'<span style="background:rgba(0,180,216,0.12); border:1px solid rgba(0,180,216,0.3); border-radius:6px; padding:4px 12px; font-size:12px; color:#E6E9EF;">'
                f'Quarterly reporters: &nbsp;<b>{int(latest_point["Reporting_Companies"])}</b></span>'
                f'<span style="background:rgba(0,180,216,0.12); border:1px solid rgba(0,180,216,0.3); border-radius:6px; padding:4px 12px; font-size:12px; color:#E6E9EF;">'
                f'Companies in filter: &nbsp;<b>{int(latest_point["Companies_In_View"])}</b></span>'
                f'</div>',
                unsafe_allow_html=True
            )

            # Priority 2: "What this means / does not mean" Microcopy
            microcopy_map = {
                "R&D Intensity": "R&D Intensity measures spending commitment, not pipeline quality or clinical success probability.",
                "Cash / Market Cap": "Cash / Market Cap measures balance-sheet buffer relative to valuation, not whether a stock is undervalued.",
                "SG&A Intensity": "SG&A Intensity measures commercial and administrative cost burden relative to revenue; it does not measure sales efficiency by itself."
            }
            note_text = microcopy_map.get(ratio_metric, "")
            if note_text:
                st.markdown(
                    f'<div style="font-size:13px; color:#E6E9EF; margin-bottom:12px; '
                    f'padding:8px 12px; border-radius:6px; background-color:#1A1F2B; border:1px solid #2A2E3A;">'
                    f'💡 &nbsp;<b>Note:</b> {note_text}'
                    f'</div>',
                    unsafe_allow_html=True
                )

            quarterly_ids = set(financials.loc[
                financials["Period_Type"].isin(QUARTERS)
                & financials["Unique_ID"].isin(pool_ids),
                "Unique_ID"
            ].dropna().unique())
            quarterly_count = len(quarterly_ids)
            excluded_count = max(0, len(pool_ids) - quarterly_count)
            excluded_sentence = (
                f"Trend covers {quarterly_count} of {len(pool_ids)} companies with at least one Q1-Q4 row; "
                f"{excluded_count} non-quarterly companies in this filter are excluded rather than converted into synthetic quarters. "
                if excluded_count > 0
                else f"Trend covers all {len(pool_ids)} companies in this filter with Q1-Q4 rows. "
            )

            st.caption(
                f"Sector trend reflects the lifecycle filter. {ratio_metric} uses "
                f"{latest_point['Definition']} and is dollar-weighted, so larger companies have larger influence. "
                "Rows are grouped by Calendar_Quarter, not fiscal Period_Type, so fiscal-quarter reporters land in the correct market quarter. "
                "Only Q1-Q4 rows are included; FY, H1 and 9M rows are excluded to keep periods like-for-like. "
                "Quarters with less than 50% company coverage are hidden, so one-company leading-edge periods do not appear as sector trends. "
                f"{excluded_sentence}"
                f"Latest plotted point: {latest_point['Period']} from "
                f"{int(latest_point['Contributing_Companies'])} companies with usable metric data "
                f"and {int(latest_point['Reporting_Companies'])} quarterly reporters in view."
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
