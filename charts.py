"""
charts.py — Lifecycle pipeline strip and financial trend chart.
"""

import plotly.graph_objects as go
import streamlit as st

from data import LIFECYCLE_STAGES

ACCENT = "#00B4D8"

# Quarterly periods form one continuous series; other cadences are plotted as
# their own series so a full-year value is never drawn level with a quarter.
CADENCE_GROUP = {
    "Q1": "Quarterly", "Q2": "Quarterly", "Q3": "Quarterly", "Q4": "Quarterly",
    "H1": "Half-year", "9M": "Nine-month", "FY": "Full-year",
}
CADENCE_COLORS = {
    "Quarterly": "#00B4D8",
    "Full-year": "#9B59B6",
    "Half-year": "#F39C12",
    "Nine-month": "#2ECC71",
    "Other": "#888888",
}


# ── Lifecycle Footprint ─────────────────────────────────────────────

def render_lifecycle_strip(company_lifecycle):
    """Render the 5-stage drug-development pipeline strip for one company."""
    active = set(company_lifecycle["active_stages"])
    profile = company_lifecycle["lifecycle_profile"]

    base = (
        "flex:1; text-align:center; padding:14px 6px; border-radius:8px; "
        "font-size:13px;"
    )
    chips = []
    for i, stage in enumerate(LIFECYCLE_STAGES):
        if stage in active:
            style = (
                base + "background:rgba(0,180,216,0.16); border:1px solid "
                f"{ACCENT}; color:#E6E9EF; font-weight:600;"
            )
            label = f"&#10003; {stage}"
        else:
            style = (
                base + "background:#1A1F2B; border:1px solid #2A2E3A; "
                "color:#5A6072; font-weight:500;"
            )
            label = stage
        chips.append(f'<div style="{style}">{label}</div>')
        if i < len(LIFECYCLE_STAGES) - 1:
            chips.append(
                '<div style="color:#5A6072; font-size:16px; padding:0 2px;">'
                "&#8594;</div>"
            )

    st.markdown(
        '<div style="display:flex; align-items:center; gap:6px; '
        'margin:4px 0 10px 0;">' + "".join(chips) + "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"**Profile:** {profile}")


# ── Financial Trend ─────────────────────────────────────────────────

def render_financial_trend(company_fin, metric_label, metric_col):
    """Line chart of one financial metric over time, split by reporting cadence.

    Quarterly periods connect as one series; FY / H1 / 9M each get their own
    series so different-length periods are never compared on the same line.
    """
    df = company_fin[
        company_fin["Quarter_End_Date"].notna() & company_fin[metric_col].notna()
    ].copy()
    if df.empty:
        st.info(f"No {metric_label} data reported for this company.")
        return

    df = df.sort_values("Quarter_End_Date")
    df["cadence"] = df["Period_Type"].map(CADENCE_GROUP).fillna("Other")
    df["plabel"] = (
        df["Period_Type"].astype(str)
        + " "
        + df["Calendar_Year"].astype("Int64").astype(str)
    )

    fig = go.Figure()
    for cadence, color in CADENCE_COLORS.items():
        sub = df[df["cadence"] == cadence]
        if sub.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=sub["Quarter_End_Date"],
                y=sub[metric_col],
                mode="lines+markers",
                name=cadence,
                line=dict(color=color, width=2),
                marker=dict(size=7, color=color, line=dict(width=1, color="white")),
                customdata=sub["plabel"],
                hovertemplate="%{customdata}<br>"
                + metric_label
                + ": %{y:,.0f} USD M<extra></extra>",
            )
        )

    fig.update_layout(
        height=300,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(showgrid=True, gridcolor="#2A2E3A", tickformat="%b %Y"),
        yaxis=dict(
            title=f"{metric_label} (USD M)",
            showgrid=True, gridcolor="#2A2E3A", zeroline=False,
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.0,
            xanchor="center", x=0.5, font=dict(size=11),
        ),
        hovermode="closest",
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    cadences = set(df["cadence"])
    if "Quarterly" in cadences and len(cadences) > 1:
        st.caption(
            "Each line is one reporting cadence — a full-year figure is never "
            "plotted level with a single quarter."
        )
