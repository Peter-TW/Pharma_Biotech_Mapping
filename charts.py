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

def render_lifecycle_strip(company_lifecycle, compact=False):
    """Render the 5-stage drug-development pipeline strip for one company.
    
    If compact is True, renders a two-column grid optimized for mobile/small screens.
    """
    active = set(company_lifecycle["active_stages"])
    profile = company_lifecycle["lifecycle_profile"]

    if compact:
        base = (
            "text-align:center; padding:10px 6px; border-radius:8px; "
            "font-size:12px; min-width:0;"
        )
        chips = []
        for stage in LIFECYCLE_STAGES:
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
        
        st.markdown(
            '<div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; '
            'margin:4px 0 10px 0;">' + "".join(chips) + "</div>",
            unsafe_allow_html=True,
        )
    else:
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
    # Display reporting periods in the same compact order as Sector Trend
    # (e.g. 2026 Q1). For fiscal-quarter reporters, append the normalized
    # Calendar Quarter when it differs from the disclosed Period_Type.
    df["year_str"] = df["Calendar_Year"].astype("Int64").astype(str)
    df["reported_label"] = df["year_str"] + " " + df["Period_Type"].astype(str)

    def _period_display(row):
        reported = row["reported_label"]
        cal_q = str(row.get("Calendar_Quarter", "")).strip().upper()
        period_type = str(row.get("Period_Type", "")).strip().upper()
        quarters = {"Q1", "Q2", "Q3", "Q4"}
        # Only annotate when both labels refer to a single quarter — FY, H1
        # and 9M rows must not be equated to a calendar quarter.
        if (period_type in quarters
                and cal_q in quarters
                and period_type != cal_q):
            return f"{reported} · Calendar Quarter {row['year_str']} {cal_q}"
        return reported

    df["plabel"] = df.apply(_period_display, axis=1)

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


def render_intelligence_map(plot_df, selected_uid, compact=False):
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
    if not compact:
        st.caption(
            "Bubble size: log-scaled market cap. X-axis uses reported quarterly "
            "revenue where available; FY reporters are visually annualised ÷4 for "
            "map placement only and are not written back as synthetic quarters. "
            "Companies above 100% R&D intensity are shown clamped at the top edge "
            "(100%)."
        )



# ── Strategic Posture Quadrant ───────────────────────────────────────

def render_strategic_posture_quadrant(plot_df, selected_uid, compact=False):
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
    if not compact:
        st.caption(
            "Strategic Posture compares R&D intensity with cash buffer relative to "
            "market value. Dashed lines show the median of companies currently in "
            "view, so quadrants are relative to the selected lifecycle filter. Bubble "
            "size is log-scaled market cap. Companies above 100% R&D intensity are "
            "shown clamped at the top edge (100%). This highlights financial capacity "
            "and research commitment, not valuation upside or clinical success probability."
        )


def render_bridge_chart(df_bridge, y_axis_choice, selected_unique_id=None):
    """Render a bubble scatter chart linking R&D spend and clinical pipeline exposure."""
    # Ensure there is enough data
    if len(df_bridge) < 3:
        st.info("Not enough data to plot the bridge chart.")
        return

    # 1. Determine Y-axis variables
    if y_axis_choice == "phase_iii_count":
        y_col = "Phase_III_Count_Active"
        y_title = "Owned active Phase III trials"
    else:
        y_col = "Phase_Weighted_Score_Active"
        y_title = "Owned active phase-weighted exposure"

    # 2. Bubble size scaling based on log10(Market_Cap)
    log_mcap = np.log10(df_bridge["Market_Cap_USD_M"].clip(lower=1.0))
    min_log = log_mcap.min()
    max_log = log_mcap.max()
    if min_log == max_log:
        df_bridge["bubble_size"] = 15.0
    else:
        df_bridge["bubble_size"] = 8.0 + (log_mcap - min_log) / (max_log - min_log) * (34.0 - 8.0)

    # 3. Categorical colors (matching posture colors)
    positioning_colors = {
        "Full-cycle leader": "#00B4D8",
        "R&D-driven commercial": "#2ECC71",
        "Commercial-led": "#F39C12",
        "Pipeline-stage challenger": "#FF758F",
    }
    fallback_color = "#888888"

    fig = go.Figure()

    # Draw companies grouped by positioning
    for pos in sorted(df_bridge["Positioning"].fillna("Unclassified").unique()):
        sub = df_bridge[df_bridge["Positioning"].fillna("Unclassified") == pos]
        if sub.empty:
            continue

        custom_data = list(zip(
            sub["Company_Name"],                         # 0
            sub["Positioning"],                          # 1
            sub["RD_Annualized_USD_M"],                  # 2
            sub["Latest_Period_Label"],                  # 3
            sub["Market_Cap_USD_M"],                     # 4
            sub["Active_Pipeline_Count"],                # 5
            sub["Operational_Risk_Count"],               # 6
            sub["Phase_I_Active_Count"],                 # 7
            sub["Phase_II_Active_Count"],                # 8
            sub["Phase_III_Active_Count"],               # 9
            sub["Participated_Phase_III_Active_Count"]  # 10
        ))

        fig.add_trace(
            go.Scatter(
                x=sub["RD_Annualized_USD_M"],
                y=sub[y_col],
                mode="markers",
                name=pos,
                marker=dict(
                    size=sub["bubble_size"],
                    sizemode="diameter",
                    color=positioning_colors.get(pos, fallback_color),
                    line=dict(width=1, color="rgba(255,255,255,0.3)"),
                ),
                customdata=custom_data,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Positioning: %{customdata[1]}<br>"
                    "Latest financial period: %{customdata[3]}<br>"
                    "Market Cap: $%{customdata[4]:,.0f}M<br>"
                    "───────────────────────────<br>"
                    "Latest R&D spend, annualized USD M: $%{customdata[2]:,.0f}M<br>"
                    "───────────────────────────<br>"
                    "Owned active Phase III trials: %{customdata[9]}<br>"
                    "Owned active Phase II trials: %{customdata[8]}<br>"
                    "Owned active Phase I trials: %{customdata[7]}<br>"
                    "Owned active pipeline count: %{customdata[5]}<br>"
                    "Owned operational risk count: %{customdata[6]}<br>"
                    "───────────────────────────<br>"
                    "Participated active Phase III count: %{customdata[10]}<extra></extra>"
                ),
            )
        )

    # 4. Draw selection highlight (matching strategic posture selection highlight style)
    if selected_unique_id:
        sel_row = df_bridge[df_bridge["Unique_ID"] == selected_unique_id]
        if not sel_row.empty:
            row = sel_row.iloc[0]
            fig.add_trace(
                go.Scatter(
                    x=[row["RD_Annualized_USD_M"]],
                    y=[row[y_col]],
                    mode="markers",
                    name="Selected",
                    marker=dict(
                        size=[row["bubble_size"]],
                        sizemode="diameter",
                        color="rgba(0,0,0,0)",
                        line=dict(width=3, color="#FFFFFF"),
                    ),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

    # Median lines calculation
    median_x = df_bridge["RD_Annualized_USD_M"].median()
    median_y = df_bridge[y_col].median()

    x_min = 1
    x_max = 10 ** (np.ceil(np.log10(df_bridge["RD_Annualized_USD_M"].max())))

    # X-axis ticks (log scale)
    tickvals = [1, 3, 10, 30, 100, 300, 1000, 3000, 10000, 30000]
    ticktext = ["$1M", "$3M", "$10M", "$30M", "$100M", "$300M", "$1B", "$3B", "$10B", "$30B"]

    y_max = df_bridge[y_col].max() * 1.15
    y_range = [0, y_max]

    fig.update_layout(
        height=480,
        margin=dict(l=70, r=30, t=35, b=50),
        xaxis=dict(
            title="Latest R&D spend, annualized USD M",
            type="log",
            range=[np.log10(x_min), np.log10(x_max)],
            tickvals=tickvals,
            ticktext=ticktext,
            showgrid=True,
            gridcolor="rgba(255,255,255,0.15)",
            zeroline=False,
        ),
        yaxis=dict(
            title=y_title,
            range=y_range,
            showgrid=True,
            gridcolor="rgba(255,255,255,0.15)",
            zeroline=False,
        ),
        shapes=[
            # Median R&D
            dict(
                type="line",
                x0=median_x, x1=median_x,
                y0=0, y1=y_max,
                line=dict(color="rgba(128,128,128,0.5)", width=1, dash="dash"),
            ),
            # Median Y value
            dict(
                type="line",
                x0=x_min, x1=x_max,
                y0=median_y, y1=median_y,
                line=dict(color="rgba(128,128,128,0.5)", width=1, dash="dash"),
            ),
        ],
        annotations=[
            # Median R&D label
            dict(
                x=median_x, y=y_max * 0.98,
                text="Median R&D Spend",
                showarrow=False,
                xref="x", yref="y",
                xanchor="center",
                font=dict(size=10, color="rgba(255,255,255,0.6)"),
                bgcolor="#0E1117",
            ),
            # Median Y label
            dict(
                x=x_max * 0.9, y=median_y,
                text=f"Median {y_title.replace('Owned active ', '')}",
                showarrow=False,
                xref="x", yref="y",
                xanchor="right",
                font=dict(size=10, color="rgba(255,255,255,0.6)"),
                bgcolor="#0E1117",
            ),
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

