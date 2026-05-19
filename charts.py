"""
charts.py — Lifecycle pipeline strip and financial trend chart.
"""

import pandas as pd
import numpy as np
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


def render_intelligence_map(plot_df, selected_uid):
    """Render Plotly scatter plot for all companies in view."""
    # Drop rows where Q_Revenue or rd_intensity is NaN, and Q_Revenue <= 0 for log scale.
    df = plot_df[plot_df["Q_Revenue"].notna() & plot_df["rd_intensity"].notna()].copy()
    
    # Consistent X-axis positioning for FY reporters (Fix 2)
    if "Period_Type" in df.columns:
        df["plotted_revenue"] = df.apply(
            lambda r: r["Q_Revenue"] / 4.0 if r["Period_Type"] == "FY" else r["Q_Revenue"],
            axis=1
        )
    else:
        df["plotted_revenue"] = df["Q_Revenue"]
        
    df = df[df["plotted_revenue"] > 0]
    
    if len(df) < 3:
        st.info("Not enough data to plot the map.")
        return
        
    def _fmt_money(val):
        if pd.isna(val):
            return "—"
        a = abs(val)
        if a >= 1_000_000:
            return f"${val / 1_000_000:,.2f}T"
        if a >= 1000:
            return f"${val / 1000:,.1f}B"
        return f"${val:,.0f}M"

    def _fmt_pct(val):
        if pd.isna(val):
            return "—"
        return f"{val:.1%}"

    # Hover-specific percentage formatter for R&D intensity (Fix 1)
    def _fmt_pct_hover(val):
        if pd.isna(val):
            return "—"
        if val > 1.0:
            return f"{val:.1%} (off-scale)"
        return f"{val:.1%}"

    # Y-axis outlier clamping (Fix 1)
    df["plotted_rd_intensity"] = df["rd_intensity"].clip(upper=1.0)
    df["marker_symbol"] = df["rd_intensity"].apply(lambda v: "triangle-up" if v > 1.0 else "circle")

    # Calculate bubble size based on np.log10(Market_Cap)
    mcap_vals = df["Market_Cap_USD_M"].fillna(1.0).clip(lower=1.0)
    df["log_mcap"] = np.log10(mcap_vals)
    
    min_log = df["log_mcap"].min()
    max_log = df["log_mcap"].max()
    if pd.isna(min_log) or pd.isna(max_log) or min_log == max_log:
        df["bubble_size"] = 22.0
    else:
        df["bubble_size"] = 9.0 + (df["log_mcap"] - min_log) / (max_log - min_log) * (40.0 - 9.0)
    
    fig = go.Figure()
    
    # Trace groups by is_commercial
    groups = [
        (True, "Commercial-stage", "#00B4D8"),
        (False, "Pipeline-stage", "#FF758F")
    ]
    
    for is_comm, label, color in groups:
        sub = df[df["is_commercial"] == is_comm]
        if sub.empty:
            continue
            
        sub_sizes = sub["bubble_size"]
        sub_symbols = sub["marker_symbol"]
        custom_data = list(zip(
            sub["Company Name"],
            sub["positioning"],
            sub["Q_Revenue"].apply(_fmt_money),
            sub["rd_intensity"].apply(_fmt_pct_hover),
            sub["Market_Cap_USD_M"].apply(_fmt_money)
        ))
        
        fig.add_trace(
            go.Scatter(
                x=sub["plotted_revenue"],
                y=sub["plotted_rd_intensity"],
                mode="markers",
                name=label,
                marker=dict(
                    size=sub_sizes,
                    sizemode="diameter",
                    color=color,
                    symbol=sub_symbols,
                    line=dict(width=1, color="rgba(255,255,255,0.3)"),
                ),
                customdata=custom_data,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Positioning: %{customdata[1]}<br>"
                    "Revenue: %{customdata[2]}<br>"
                    "R&D Intensity: %{customdata[3]}<br>"
                    "Market Cap: %{customdata[4]}<extra></extra>"
                )
            )
        )
        
    # Overlay distinct marker for the selected company if it exists in the plot
    if selected_uid:
        sel_row = df[df["Unique_ID"] == selected_uid]
        if not sel_row.empty:
            row = sel_row.iloc[0]
            sel_size = row["bubble_size"]
            sel_symbol = "triangle-up" if row["rd_intensity"] > 1.0 else "circle"
            fig.add_trace(
                go.Scatter(
                    x=[row["plotted_revenue"]],
                    y=[row["plotted_rd_intensity"]],
                    mode="markers",
                    name="Selected",
                    marker=dict(
                        size=[sel_size],
                        sizemode="diameter",
                        color="rgba(0,0,0,0)",  # transparent fill
                        symbol=sel_symbol,
                        line=dict(width=3, color="#FFFFFF"),  # thick white border
                    ),
                    showlegend=False,
                    hoverinfo="skip"
                )
            )
            
    fig.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(
            title="Revenue per quarter (USD M, log scale; FY reporters annualised ÷4)",
            type="log",
            showgrid=True,
            gridcolor="#2A2E3A",
            zeroline=False,
        ),
        yaxis=dict(
            title="R&D Intensity",
            tickformat=".0%",
            showgrid=True,
            gridcolor="#2A2E3A",
            zeroline=False,
            range=[-0.05, 1.0],
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color="#E6E9EF"),
        ),
        hovermode="closest",
    )
    
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.caption(
        "Bubble size: log-scaled market cap. Companies above 100% R&D intensity "
        "are shown clamped at the top edge (100%)."
    )

