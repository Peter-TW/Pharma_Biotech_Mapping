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
        "Bubble size: log-scaled market cap. X-axis uses reported quarterly "
        "revenue where available; FY reporters are visually annualised ÷4 for "
        "map placement only and are not written back as synthetic quarters. "
        "Companies above 100% R&D intensity are shown clamped at the top edge "
        "(100%)."
    )



# ── Strategic Posture Quadrant ───────────────────────────────────────

def render_strategic_posture_quadrant(plot_df, selected_uid):
    """Render the investor-style posture quadrant.

    X-axis: Cash / Market Cap, a balance-sheet buffer relative to public
    valuation. Y-axis: R&D Intensity, a spending commitment measure. Median
    reference lines are calculated from companies currently in view, so the
    quadrant adapts to the lifecycle filter instead of using hard-coded
    thresholds.
    """
    required = ["cash_to_mktcap", "rd_intensity", "Market_Cap_USD_M"]
    df = plot_df.dropna(subset=required).copy()
    df = df[(df["cash_to_mktcap"] >= 0) & (df["Market_Cap_USD_M"] > 0)]

    if len(df) < 3:
        st.info("Not enough cash, market cap and R&D intensity data to plot the quadrant.")
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

    def _fmt_rd_hover(val):
        if pd.isna(val):
            return "—"
        if val > 1.0:
            return f"{val:.1%} (off-scale)"
        return f"{val:.1%}"

    # Keep the visual field readable without changing the underlying values.
    df["plotted_rd_intensity"] = df["rd_intensity"].clip(upper=1.0)
    df["marker_symbol"] = df["rd_intensity"].apply(
        lambda v: "triangle-up" if v > 1.0 else "circle"
    )

    median_cash = df["cash_to_mktcap"].median()
    median_rd = df["rd_intensity"].median()
    plotted_median_rd = min(median_rd, 1.0)

    mcap_vals = df["Market_Cap_USD_M"].fillna(1.0).clip(lower=1.0)
    df["log_mcap"] = np.log10(mcap_vals)
    min_log = df["log_mcap"].min()
    max_log = df["log_mcap"].max()
    if pd.isna(min_log) or pd.isna(max_log) or min_log == max_log:
        df["bubble_size"] = 22.0
    else:
        df["bubble_size"] = 9.0 + (df["log_mcap"] - min_log) / (max_log - min_log) * (40.0 - 9.0)

    # Use existing positioning categories for color so this chart connects with
    # the Intelligence Map's language.
    positioning_colors = {
        "Full-cycle leader": "#00B4D8",
        "R&D-driven commercial": "#2ECC71",
        "Commercial-led": "#F39C12",
        "Pipeline-stage challenger": "#FF758F",
    }
    fallback_color = "#888888"

    fig = go.Figure()
    for pos in sorted(df["positioning"].fillna("Unclassified").unique()):
        sub = df[df["positioning"].fillna("Unclassified") == pos]
        if sub.empty:
            continue
        custom_data = list(zip(
            sub["Company Name"],
            sub["positioning"].fillna("Unclassified"),
            sub.get("lifecycle_profile", pd.Series(["—"] * len(sub), index=sub.index)).fillna("—"),
            sub["cash_to_mktcap"].apply(_fmt_pct),
            sub["rd_intensity"].apply(_fmt_rd_hover),
            sub["Q_Cash"].apply(_fmt_money) if "Q_Cash" in sub.columns else pd.Series(["—"] * len(sub), index=sub.index),
            sub["Market_Cap_USD_M"].apply(_fmt_money),
        ))
        fig.add_trace(
            go.Scatter(
                x=sub["cash_to_mktcap"],
                y=sub["plotted_rd_intensity"],
                mode="markers",
                name=pos,
                marker=dict(
                    size=sub["bubble_size"],
                    sizemode="diameter",
                    color=positioning_colors.get(pos, fallback_color),
                    symbol=sub["marker_symbol"],
                    line=dict(width=1, color="rgba(255,255,255,0.3)"),
                ),
                customdata=custom_data,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Positioning: %{customdata[1]}<br>"
                    "Lifecycle: %{customdata[2]}<br>"
                    "Cash / Market Cap: %{customdata[3]}<br>"
                    "R&D Intensity: %{customdata[4]}<br>"
                    "Cash: %{customdata[5]}<br>"
                    "Market Cap: %{customdata[6]}<extra></extra>"
                ),
            )
        )

    # Selected-company outline.
    if selected_uid:
        sel_row = df[df["Unique_ID"] == selected_uid]
        if not sel_row.empty:
            row = sel_row.iloc[0]
            fig.add_trace(
                go.Scatter(
                    x=[row["cash_to_mktcap"]],
                    y=[row["plotted_rd_intensity"]],
                    mode="markers",
                    name="Selected",
                    marker=dict(
                        size=[row["bubble_size"]],
                        sizemode="diameter",
                        color="rgba(0,0,0,0)",
                        symbol="triangle-up" if row["rd_intensity"] > 1.0 else "circle",
                        line=dict(width=3, color="#FFFFFF"),
                    ),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

    x_max = max(df["cash_to_mktcap"].max() * 1.12, median_cash * 1.8, 0.10)
    y_max = 1.0

    fig.update_layout(
        height=410,
        margin=dict(l=10, r=10, t=35, b=10),
        xaxis=dict(
            title="Cash / Market Cap",
            tickformat=".0%",
            range=[0, x_max],
            showgrid=True,
            gridcolor="#2A2E3A",
            zeroline=False,
        ),
        yaxis=dict(
            title="R&D Intensity",
            tickformat=".0%",
            range=[-0.05, y_max],
            showgrid=True,
            gridcolor="#2A2E3A",
            zeroline=False,
        ),
        shapes=[
            dict(
                type="line", x0=median_cash, x1=median_cash, y0=-0.05, y1=y_max,
                line=dict(color="rgba(255,255,255,0.35)", width=1, dash="dash"),
            ),
            dict(
                type="line", x0=0, x1=x_max, y0=plotted_median_rd, y1=plotted_median_rd,
                line=dict(color="rgba(255,255,255,0.35)", width=1, dash="dash"),
            ),
        ],
        annotations=[
            dict(x=x_max * 0.98, y=y_max * 0.95, text="R&D firepower", showarrow=False,
                 font=dict(size=11, color="#8A91A0"), xanchor="right"),
            dict(x=x_max * 0.02, y=y_max * 0.95, text="Funding pressure", showarrow=False,
                 font=dict(size=11, color="#8A91A0"), xanchor="left"),
            dict(x=x_max * 0.98, y=0.02, text="Capital reserve", showarrow=False,
                 font=dict(size=11, color="#8A91A0"), xanchor="right"),
            dict(x=x_max * 0.02, y=0.02, text="Commercial / valuation dependent", showarrow=False,
                 font=dict(size=11, color="#8A91A0"), xanchor="left"),
        ],
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
        "Strategic Posture compares R&D intensity with cash buffer relative to "
        "market value. Dashed lines show the median of companies currently in "
        "view, so quadrants are relative to the selected lifecycle filter. Bubble "
        "size is log-scaled market cap. Companies above 100% R&D intensity are "
        "shown clamped at the top edge (100%). This highlights financial capacity "
        "and research commitment, not valuation upside or clinical success probability."
    )
