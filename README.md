# Biopharma Command Center

A single-page Streamlit dashboard that turns two biopharma datasets into an
interactive intelligence map for the Top 50 biopharma companies. It opens with
sector-level context, then lets you drill into a selected company through
lifecycle footprint, positioning, financial snapshot, financial trend, and data
provenance.

This is **MVP-1**. It focuses on high-integrity sector/company comparison using
committed CSV data. The relationship/network map remains a later pass.

## Data discipline

The dataset behind this dashboard is small, but the rules behind it are strict.
Every value is intended to come from an official company source such as annual
reports, quarterly results PDFs, regulatory filings, or investor materials.
Every production data change should follow the project audit workflow: staging,
diagnostic, preview, controlled rewrite, and an audit log of cell-level changes.

The dashboard follows a conservative data principle:

- **Actual reported periods only.** `Quarterly_Financials.csv` stores periods as
  disclosed: Q1, Q2, Q3, Q4, H1, 9M, or FY.
- **No synthetic quarters.** Annual, half-year, and 9M values are not divided or
  forced into quarter-level sector trends.
- **Honest blanks over proxies.** Where a company does not separately disclose a
  metric, the dashboard shows a blank rather than estimating from a broader line
  item.
- **Snapshot integrity.** Cash and Market Cap are point-in-time values. They are
  not averaged across periods.
- **Calendar Quarter sector logic.** Sector-level quarterly views use Q1-Q4 rows
  only and group by `Calendar_Quarter`, so fiscal-quarter reporters land in the
  correct market-time bucket.
- **Company-level cadence integrity.** Company financial trends split quarterly,
  half-year, 9M, and FY rows into separate lines so different-length reporting
  periods are not plotted as if they were equivalent.

The app reads committed CSV files only and makes **no external API calls** at
runtime.

## Features

- **Lifecycle filter** — sidebar control for All companies, Full-cycle only, or
  Non-full-cycle only. Sector, map, and company views update with this filter.
- **Data Freshness Summary** — shows the latest broad-coverage Calendar Quarter,
  the latest eligible sector trend point, and whether sparse leading-edge
  quarters are hidden until coverage improves.
- **Sector Overview** — companies in view, combined latest market cap, and
  combined broad-coverage Calendar Quarter revenue. The revenue reference period
  uses the latest Calendar Quarter with at least 80% revenue coverage for the
  active lifecycle filter.
- **Sector Trend** — dollar-weighted sector ratio trends for R&D Intensity,
  Cash / Market Cap, and SG&A Intensity. Uses Q1-Q4 rows only, grouped by
  `Calendar_Quarter`, with coverage badges for metric contributors, quarterly
  reporters, and companies in the active lifecycle filter. Includes Focus range
  and Full range y-axis views; Focus range auto-expands when data would otherwise
  fall outside the preset band.
- **Intelligence Map** — compares companies by revenue scale, R&D Intensity,
  market-cap scale, and commercial/pipeline status. Bubble size is log-scaled
  market cap. FY reporters are visually annualised ÷4 for map placement only;
  this is not written back as synthetic quarterly data.
- **Strategic Posture Quadrant** — compares R&D Intensity with Cash / Market Cap
  to show whether companies combine scientific reinvestment with financial
  firepower. Median lines are relative to the active lifecycle filter. This is
  not a valuation-upside or clinical-success signal.
- **Company Header** — selected company metadata with latest reported period.
  When the disclosed fiscal quarter differs from the normalized Calendar Quarter,
  both labels are shown.
- **Lifecycle Footprint** — the 5-stage pipeline view: Discovery → Preclinical →
  Clinical Trials → FDA Review → Commercial.
- **Financial Snapshot** — latest reported Revenue, R&D, SG&A, Cash, Market Cap,
  R&D Intensity, and Cash / Market Cap.
- **Financial Trend** — selected-company metric trend over time, with reporting
  cadences drawn as separate series. Hover labels use year-first period labels
  and only add Calendar Quarter annotations for true quarterly fiscal/calendar
  mismatches.
- **Data Sources** — profile source, financial sources, reporting standard,
  reporting currency, row status, derived-row count, and manual-review count.

## Questions the dashboard answers

- **Sector Overview** — What is the aggregate size and latest broad-coverage
  Calendar Quarter revenue base of the selected biopharma universe?
- **Sector Trend** — Is the selected universe becoming more research-intensive,
  more cash-rich, or more SG&A-heavy over time?
- **Intelligence Map** — How does this company position commercially and
  scientifically against the rest of the industry?
- **Strategic Posture Quadrant** — Does this company have enough financial
  firepower to support its scientific investment?
- **Lifecycle Footprint** — Where does this company participate across the
  therapeutic product lifecycle?
- **Financial Snapshot** — What is this company’s latest reported financial
  position?
- **Financial Trend** — How has this company’s reported financial profile changed
  over time without mixing reporting cadences?
- **Data Sources** — Can I trace where the company’s financial and profile data
  came from?

## What the dashboard does not claim

- It is **not** a stock recommendation tool.
- It does **not** estimate fair value, price targets, or valuation upside.
- R&D Intensity measures spending commitment, not pipeline quality or clinical
  probability of success.
- Cash / Market Cap measures balance-sheet buffer relative to valuation, not
  whether a stock is undervalued.
- Strategic Posture highlights financial capacity and research commitment, not
  clinical success probability.
- Lifecycle stages are high-level company participation flags, not asset-level
  pipeline depth.

## Core calculation rules

### Sector Overview

- Uses Q1-Q4 rows only.
- Groups by `Calendar_Year + Calendar_Quarter`.
- Selects the latest Calendar Quarter with at least 80% revenue coverage for the
  active lifecycle filter.
- Uses `math.ceil()` for the 80% threshold so the displayed period truly meets
  or exceeds the stated coverage rule.
- Excludes FY, H1, and 9M rows from the quarterly sector view.

### Sector Trend

- Uses Q1-Q4 rows only.
- Groups by `Calendar_Year + Calendar_Quarter`.
- Applies a 50% coverage floor so one-company leading-edge periods do not appear
  as sector trends.
- Calculates ratios as dollar-weighted aggregate ratios:
  - R&D Intensity = `Σ R&D ÷ Σ Revenue`
  - Cash / Market Cap = `Σ Cash ÷ Σ Market Cap`
  - SG&A Intensity = `Σ SG&A ÷ Σ Revenue`
- Uses paired non-null numerator/denominator rows only.
- Excludes zero denominators.
- Does not treat missing values as zero.
- Provides Focus range and Full range y-axis views. Full range starts from zero;
  Focus range narrows the visual field and auto-expands if the data falls outside
  the preset focus band.

### Company latest financials

- Uses the latest row by `Quarter_End_Date`.
- Where Q4 and FY share the same end date, FY receives higher priority so the
  latest snapshot is deterministic and not dependent on CSV row order.
- R&D Intensity and Cash / Market Cap use non-zero denominators only.

### Financial Trend

- Quarterly, H1, 9M, and FY rows are plotted as separate cadence series.
- A full-year figure is never plotted as if it were a single quarter.
- Calendar Quarter annotation appears only when both the disclosed period and the
  normalized calendar period are true single-quarter labels.

## Project structure

```
.
├── app.py                  # page layout, filters, section text, sector charts
├── data.py                 # CSV loading + derived tables (all cached)
├── charts.py               # lifecycle strip + company/map/quadrant charts
├── requirements.txt        # pinned dependencies
├── .gitignore
├── .streamlit/
│   └── config.toml         # dark theme
└── data/
    ├── Company_Master.csv
    ├── Quarterly_Financials.csv
    └── Dashboard_Data_Notes.csv   # optional; app falls back gracefully if missing
```

`app.py` must be at the repository root, and the `data/` folder and
`.streamlit/config.toml` must be committed. The app reads these files at runtime.

## Run locally

Requires Python 3.11 or 3.12.

```bash
python -m venv .venv

# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

The app opens at http://localhost:8501.

## Deploy to Streamlit Community Cloud

1. Push this project to GitHub. Confirm `app.py` is at the repo root and that
   `data/`, `.streamlit/config.toml`, and `requirements.txt` are committed.
2. Make sure `.gitignore` excludes local/runtime files, for example:
   ```
   .venv/
   __pycache__/
   *.pyc
   .DS_Store
   .streamlit/secrets.toml
   ```
3. Go to Streamlit Community Cloud and create an app from the GitHub repo.
4. Select the correct branch and set the main file path to `app.py`.
5. Deploy. Future pushes to the selected branch redeploy the app automatically.

## Current scope and future work

Built in this MVP:

- Sector Overview
- Sector Trend
- Intelligence Map
- Strategic Posture Quadrant
- Lifecycle Footprint
- Financial Snapshot
- Financial Trend
- Data Sources / provenance panel

Planned later:

- Relationship/network map using reliable relationship edges such as shared
  indication, modality, partnership, or competitive overlap.
- Asset-level pipeline depth, clinical catalysts, and product-level revenue
  concentration.
- Valuation lens such as EV/Sales, revenue growth, FCF, or forward estimates,
  if reliable inputs are added.
