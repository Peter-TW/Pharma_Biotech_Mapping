"""
app.py — Biopharma Command Center (MVP-1)
Single-page Streamlit dashboard.
"""

import html
import math
import altair as alt
import pandas as pd
import streamlit as st

from data import load_master, load_financials, get_latest_financials, get_lifecycle, get_positioning, get_sector_ratio_trend, load_clinical_status_summary, load_expected_zero, build_bridge_chart_data, load_clinical_inventory_normalized, get_company_clinical_inventory
from charts import render_lifecycle_strip, render_financial_trend, render_intelligence_map, render_strategic_posture_quadrant, render_bridge_chart

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


def question_prompt(text):
    """Small section guide showing the question a chart is designed to answer."""
    st.markdown(
        f'<div style="font-size:13px; color:#C9D1D9; margin:-2px 0 12px 0; '
        f'padding:8px 12px; border-radius:6px; background-color:#111827; '
        f'border-left:3px solid #00B4D8;">'
        f'<b>Question answered:</b> {html.escape(text)}</div>',
        unsafe_allow_html=True,
    )


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
# Coverage floor: prefer the most recent Calendar Quarter where at least 80%
# of companies in view reported quarterly revenue. Falls back to the broadest
# available Calendar Quarter if no quarter clears the floor.
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
    f"Latest broad-coverage Calendar Quarter: <b>{overview_label}</b>. "
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
    question_prompt("What is the aggregate size and latest broad-coverage Calendar Quarter revenue base of the selected biopharma universe?")
    s1, s2, s3 = st.columns(3)
    s1.metric("Companies in view", str(len(pool_ids)))
    s2.metric("Combined Market Cap", fmt_money(combined_mcap))
    revenue_label = f"Calendar {ref_q} {ref_year}" if ref_q is not None else "No quarterly data"
    s3.metric(f"Combined Revenue · {revenue_label}", fmt_money(combined_rev))

    if ref_q is not None:
        coverage_phrase = (
            "the latest Calendar Quarter with at least 80% of companies in view "
            "reporting quarterly revenue"
            if used_coverage_floor
            else "the broadest available Calendar Quarter because no quarter cleared "
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
    question_prompt("Is the selected biopharma universe becoming more research-intensive, more cash-rich, or more SG&A-heavy over time?")
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

    focus_ranges = {
        "R&D Intensity": (0.15, 0.25),
        "Cash / Market Cap": (0.00, 0.10),
        "SG&A Intensity": (0.15, 0.35),
    }
    y_axis_view = st.radio(
        "Y-axis view",
        ["Focus range", "Full range"],
        index=0,
        horizontal=True,
        help=(
            "Focus range narrows the y-axis to make small sector-level changes "
            "easier to see. It does not change the underlying calculation."
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
            metric_df = metric_df.sort_values("Sort_Key").copy()
            metric_df["Period_Display"] = (
                metric_df["Calendar_Year"].astype(int).astype(str)
                + " "
                + metric_df["Calendar_Quarter"].astype(str)
            )

            # Y-axis scale. Focus range auto-expands when data falls outside
            # the default band so the line is never silently drawn off-canvas
            # (e.g. R&D Intensity in the Non-full-cycle pool lands below 15%).
            focus_min, focus_max = focus_ranges[ratio_metric]
            data_min = float(metric_df["Value"].min())
            data_max = float(metric_df["Value"].max())
            focus_covers = data_min >= focus_min and data_max <= focus_max
            focus_expanded = False
            y_min_eff, y_max_eff = focus_min, focus_max

            if y_axis_view == "Focus range":
                if focus_covers:
                    y_scale = alt.Scale(domain=[focus_min, focus_max])
                else:
                    pad = max((data_max - data_min) * 0.1, 0.005)
                    y_min_eff = min(focus_min, data_min - pad)
                    y_max_eff = max(focus_max, data_max + pad)
                    y_scale = alt.Scale(domain=[y_min_eff, y_max_eff])
                    focus_expanded = True
            else:
                # Full range = include 0 to show absolute magnitude.
                y_scale = alt.Scale(zero=True)

            chart = (
                alt.Chart(metric_df)
                .mark_line(point=True)
                .encode(
                    x=alt.X(
                        "Period_Display:N",
                        sort=list(metric_df["Period_Display"]),
                        title="Calendar Quarter",
                    ),
                    y=alt.Y(
                        "Value:Q",
                        title=ratio_metric,
                        axis=alt.Axis(format="%"),
                        scale=y_scale,
                    ),
                    tooltip=[
                        alt.Tooltip("Period_Display:N", title="Calendar Quarter"),
                        alt.Tooltip("Value:Q", title=ratio_metric, format=".1%"),
                        alt.Tooltip("Definition:N", title="Definition"),
                        alt.Tooltip("Contributing_Companies:Q", title="Metric contributors"),
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

            latest_period_display = latest_point.get("Period_Display", latest_point["Period"])
            st.markdown(
                f'<div style="font-size:13px; color:#E6E9EF; margin:8px 0 10px 0; '
                f'padding:10px 12px; border-radius:6px; background-color:#1A1F2B; '
                f'border:1px solid #2A2E3A; line-height:1.45;">'
                f'<b>Latest eligible point:</b> {latest_period_display} — '
                f'<b>{ratio_metric} {fmt_pct(latest_point["Value"])}</b> from '
                f'<b>{int(latest_point["Contributing_Companies"])}</b> metric contributors and '
                f'<b>{int(latest_point["Reporting_Companies"])}</b> quarterly reporters.<br>'
                f'Dollar-weighted {latest_point["Definition"]} across the lifecycle filter. '
                f'Only Q1–Q4 rows are included; FY/H1/9M rows are excluded to keep periods like-for-like.'
                f'</div>',
                unsafe_allow_html=True,
            )

            if y_axis_view == "Focus range":
                if focus_expanded:
                    st.caption(
                        f"Y-axis expanded to {y_min_eff:.1%}–{y_max_eff:.1%} because some "
                        f"values fall outside the default {focus_min:.0%}–{focus_max:.0%} focus band "
                        f"for this lifecycle filter. The underlying calculation is unchanged; "
                        f"switch to Full range to see absolute magnitude from 0."
                    )
                else:
                    st.caption(
                        f"Y-axis focus range: {focus_min:.0%}–{focus_max:.0%}. "
                        "This zoom makes small sector-level changes easier to see and does not change the underlying calculation."
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



# ── Intelligence Map ────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("Intelligence Map")
    question_prompt("How does this company position commercially and scientifically against the rest of the industry?")
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

# ── Strategic Posture Quadrant ───────────────────────────────────────
with st.container(border=True):
    st.subheader("Strategic Posture Quadrant")
    question_prompt("Does this company have enough financial firepower to support its scientific investment?")
    posture_df = pool[["Unique_ID", "Company Name", "Commercial"]].merge(
        latest[[
            "Unique_ID", "Q_Revenue", "Q_RD", "Q_Cash",
            "rd_intensity", "cash_to_mktcap", "Market_Cap_USD_M", "Period_Type"
        ]],
        on="Unique_ID",
        how="left"
    ).merge(
        positioning_df[["Unique_ID", "positioning"]],
        on="Unique_ID",
        how="left"
    ).merge(
        lifecycle_df[["Unique_ID", "lifecycle_profile"]],
        on="Unique_ID",
        how="left"
    )

    render_strategic_posture_quadrant(posture_df, uid)


# ── Clinical Productivity vs. R&D Spend ──────────────────────────────
with st.container(border=True):
    st.subheader("Clinical Productivity vs. R&D Spend")
    question_prompt("Which companies show the largest late-stage clinical footprint relative to reported R&D investment?")

    # Y-axis toggle
    y_axis_choice = st.radio(
        "Y-axis metric",
        options=["Active Phase III count", "Phase-weighted active exposure"],
        index=0,
        horizontal=True,
        key="bridge_chart_y_axis",
        help="Select Y-axis metric: Active Phase III count or Phase-weighted clinical exposure score."
    )
    y_choice_key = "phase_iii_count" if y_axis_choice == "Active Phase III count" else "weighted_score"

    status_summary = load_clinical_status_summary()
    df_bridge = build_bridge_chart_data(master, latest, status_summary)

    # 4a Validation Row count check
    if len(df_bridge) < 35 or len(df_bridge) > 50:
        st.warning(f"Warning: Unexpected number of companies in bridge chart data: {len(df_bridge)} (expected 40-46). Some data might be missing.")

    # 4b Expected-zero verification
    expected_zero_check_uids = ["CMP-022", "CMP-043", "CMP-047", "CMP-049"]
    for ez_uid in expected_zero_check_uids:
        if ez_uid in df_bridge["Unique_ID"].values:
            st.warning(f"Warning: Expected-zero company {ez_uid} was not correctly filtered out of the bridge chart.")

    # Render chart
    render_bridge_chart(df_bridge, y_choice_key, selected_unique_id=uid)

    # 3g Footnote construct
    ez_df = load_expected_zero()
    expected_zero_names = ", ".join(ez_df["Company_Name"].tolist())

    # Find companies excluded for missing R&D or Market Cap
    all_master_uids = set(master["Unique_ID"].tolist())
    ez_uids = set(ez_df["Unique_ID"].tolist())
    included_uids = set(df_bridge["Unique_ID"].tolist())
    missing_rd_uids = all_master_uids - ez_uids - included_uids

    # Map missing R&D UIDs to names
    missing_rd_names_list = sorted([
        master[master["Unique_ID"] == m_uid]["Company Name"].iloc[0]
        for m_uid in missing_rd_uids
        if not master[master["Unique_ID"] == m_uid].empty
    ])
    missing_rd_names = ", ".join(missing_rd_names_list)

    footnote_text = f"Showing {len(df_bridge)} of 50 companies. Excluded: 4 non-pharma businesses ({expected_zero_names} — animal health, royalty financier, and life-sciences tools)."
    if missing_rd_names:
        footnote_text += f" {len(missing_rd_names_list)} additional company/companies excluded due to missing latest-period R&D or market cap disclosure ({missing_rd_names})."

    st.caption(footnote_text)

    # 3h Methodology Disclaimer
    st.caption(
        "This chart links reported R&D investment with ClinicalTrials.gov late-stage exposure. "
        "Active Phase III count is a registry-based exposure measure, not a probability-of-success "
        "forecast, asset quality measure, or valuation upside indicator. Differences in trial size, "
        "indication, and outsourcing model make cross-company comparisons indicative only."
    )
    st.caption(
        "Companies with generics-led or specialty-branded business models "
        "(e.g., Sun Pharmaceutical Industries) typically have lower R&D "
        "Intensity than discovery-led peers and will appear far to the "
        "left on this chart. This reflects business-model differences, "
        "not pipeline quality or commercial weakness."
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
    question_prompt("What is this company’s latest reported financial position?")
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


# ── Clinical Trial Footprint ─────────────────────────────────────────
with st.container(border=True):
    st.subheader("Clinical Trial Footprint")
    question_prompt("What active, late-stage, and risk-flagged ClinicalTrials.gov records support this company’s clinical footprint?")

    # Load data
    try:
        clinical_inventory = load_clinical_inventory_normalized()
        # Find if expected zero
        ez_df = load_expected_zero()
        is_expected_zero = uid in ez_df["Unique_ID"].values
        
        # Load status summary for KPI cards
        status_sum_df = load_clinical_status_summary()
        company_summary = status_sum_df[status_sum_df["Unique_ID"] == uid]
        
        # Determine if expected zero based on either source
        if not company_summary.empty:
            summary_row = company_summary.iloc[0]
            is_expected_zero = is_expected_zero or bool(summary_row.get("Expected_Zero", False))
        else:
            summary_row = None
            
        data_loaded = True
    except Exception as e:
        st.error(f"Error loading clinical data: {e}")
        data_loaded = False

    if data_loaded:
        # Check if the summary is completely missing
        if summary_row is None and not is_expected_zero:
            st.info("No ClinicalTrials.gov summary data is available for this company.")
        else:
            # Expected zero note
            if is_expected_zero:
                st.warning("This company is marked as expected-zero for the ClinicalTrials.gov human-trial layer, based on its business model / scope.")
            
            # Show KPI cards
            if summary_row is not None:
                k1, k2, k3, k4, k5, k6 = st.columns(6)
                
                # Retrieve metrics safely, default to 0 if NaN/None
                def get_kpi_val(col_name):
                    val = summary_row.get(col_name, 0)
                    if pd.isna(val) or val is None:
                        return 0
                    return int(val)
                
                k1.metric("Owned Active Pipeline", f"{get_kpi_val('Owned_Active_Pipeline_Count')}")
                k2.metric("Owned Recruiting", f"{get_kpi_val('Owned_Recruiting_Count')}")
                k3.metric("Owned Active Not Recruiting", f"{get_kpi_val('Owned_Active_Not_Recruiting_Count')}")
                k4.metric("Owned Operational Risk", f"{get_kpi_val('Owned_Operational_Risk_Count')}")
                k5.metric("Owned Phase III", f"{get_kpi_val('Owned_Phase_III_Count_Exclusive')}")
                k6.metric("Participated Trials", f"{get_kpi_val('Participated_All_Trials')}")
                
            # Scope toggle
            scope_choice = st.radio(
                "Clinical record scope",
                options=["Owned footprint", "Participated / collaborator exposure"],
                index=0,
                horizontal=True,
                key="clinical_record_scope_toggle",
                help="Select the ownership scope of clinical trials to view."
            )
            
            st.markdown(
                '<div style="font-size:13px; color:#A3B3C2; margin-top:-10px; margin-bottom:15px;">'
                '<i>Owned footprint includes lead sponsor, subsidiaries, and acquired entities in the current portfolio. '
                'Participated / collaborator exposure also includes collaborator-only records.</i>'
                '</div>',
                unsafe_allow_html=True
            )
            
            # Fetch NCT-level inventory
            comp_inv = get_company_clinical_inventory(clinical_inventory, uid, scope_choice)
            
            # Filters Layout
            f1, f2, f3 = st.columns([2, 2, 1])
            
            status_filter = f1.selectbox(
                "Status filter",
                options=["All surfaced statuses", "Active Pipeline only", "Operational Risk only", "All statuses"],
                index=0,
                key="clinical_status_filter"
            )
            
            phase_filter = f2.selectbox(
                "Phase filter",
                options=["All phases", "Phase III", "Phase II", "Phase I", "Mixed Phase", "Other / NA"],
                index=0,
                key="clinical_phase_filter"
            )
            
            limit_choice = f3.selectbox(
                "Rows to show",
                options=["10", "25", "50", "All"],
                index=1,
                key="clinical_rows_limit_select"
            )
            
            # Filter the records
            filtered_df = comp_inv.copy()
            
            # 1. Phase Filter
            if phase_filter != "All phases":
                filtered_df = filtered_df[filtered_df["Phase_Bucket_Exclusive"] == phase_filter]
                
            # 2. Status Filter
            if status_filter == "All surfaced statuses":
                surfaced_statuses = ["Recruiting", "Active Not Recruiting", "Suspended", "Terminated"]
                temp_filtered = filtered_df[filtered_df["Status_Bucket"].isin(surfaced_statuses)]
                # If none exist, show most recent records (fall back to all statuses)
                if not temp_filtered.empty:
                    filtered_df = temp_filtered
            elif status_filter == "Active Pipeline only":
                filtered_df = filtered_df[filtered_df["Status_Group"] == "Active Pipeline"]
            elif status_filter == "Operational Risk only":
                filtered_df = filtered_df[filtered_df["Status_Group"] == "Operational Risk"]
            # "All statuses" doesn't filter by status
            
            # Table display or empty handling
            if filtered_df.empty:
                st.info("No matched ClinicalTrials.gov records are available for this company under the selected scope.")
                if is_expected_zero:
                    st.caption("This is expected for this company in the current MVP scope.")
                else:
                    st.caption("This may reflect a sponsor-alias coverage gap or a company with no ClinicalTrials.gov footprint under the current matching rules.")
            else:
                # Apply row limit
                if limit_choice != "All":
                    limit_val = int(limit_choice)
                    display_df_raw = filtered_df.head(limit_val)
                else:
                    display_df_raw = filtered_df
                    
                # Prepare columns for presentation
                display_df = pd.DataFrame()
                display_df["NCT ID"] = display_df_raw["NCT_ID"].fillna("")
                display_df["Brief Title"] = display_df_raw["Brief_Title"].fillna("")
                display_df["Status"] = display_df_raw["Status_Bucket"].fillna("")
                display_df["Phase"] = display_df_raw["Phase_Bucket_Exclusive"].fillna("")
                display_df["Sponsor Role"] = display_df_raw["Sponsor_Match_Type"].fillna("")
                display_df["Ownership Context"] = display_df_raw["Ownership_Context"].fillna("")
                
                # Format date nicely
                date_vals = pd.to_datetime(display_df_raw["Last_Update_Submit_Date"])
                display_df["Last Update"] = date_vals.dt.strftime("%Y-%m-%d").fillna("")
                
                display_df["Study Link"] = display_df_raw["Study_URL"].fillna("")
                
                # Column Configuration
                col_config = {
                    "NCT ID": st.column_config.TextColumn("NCT ID", width="small"),
                    "Brief Title": st.column_config.TextColumn("Brief Title", width="large"),
                    "Status": st.column_config.TextColumn("Status", width="medium"),
                    "Phase": st.column_config.TextColumn("Phase", width="small"),
                    "Sponsor Role": st.column_config.TextColumn("Sponsor Role", width="medium"),
                    "Ownership Context": st.column_config.TextColumn("Ownership Context", width="medium"),
                    "Last Update": st.column_config.TextColumn("Last Update", width="small"),
                    "Study Link": st.column_config.LinkColumn("Study Link", display_text="Open NCT", width="small")
                }
                
                st.dataframe(
                    display_df,
                    column_config=col_config,
                    use_container_width=True,
                    hide_index=True
                )
                
            # Notes and disclaimers below the table
            main_note = (
                "Clinical trial records are sourced from ClinicalTrials.gov and attributed using the project’s "
                "sponsor-alias and M&A ownership rules. Counts reflect registry exposure, not clinical success "
                "probability, asset quality, or valuation upside."
            )
            if scope_choice == "Owned footprint":
                scope_note = "This view excludes collaborator-only records and is the default scope for headline clinical counts."
            else:
                scope_note = "This view includes collaborator-only records, so it represents ecosystem participation rather than owned clinical footprint."
            
            non_us_note = (
                "ClinicalTrials.gov does not cover every non-US registry-only trial. "
                "Region-only studies on jRCT, CTIS/EUCTR, or ChiCTR may be absent."
            )
            
            st.markdown(
                f'<div style="font-size:12px; color:#8C9BA5; margin-top:15px; padding:10px 14px; '
                f'border-radius:6px; background-color:#161B22; border:1px solid #21262D; line-height:1.6;">'
                f'📢 &nbsp;<b>Attribution Note:</b> {main_note}<br/>'
                f'🔍 &nbsp;<b>Scope Context:</b> {scope_note}<br/>'
                f'🌎 &nbsp;<b>Geographic Coverage:</b> {non_us_note}'
                f'</div>',
                unsafe_allow_html=True
            )


# ── Financial Trend ─────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("Financial Trend")
    question_prompt("How has this company’s reported financial profile changed over time without mixing reporting cadences?")
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
    question_prompt("Can I trace where this company’s financial and profile data came from?")
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
