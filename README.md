# Biopharma Command Center

A single-page Streamlit dashboard that turns two biopharma datasets into an
interactive company intelligence map. It opens on a sector-wide overview and
sector trend, then lets you drill into any of 50 companies — lifecycle
footprint, latest financial snapshot, financial trend, and data provenance.

This is **MVP-1**. The relationship/network map and the strategic posture
quadrant are planned later passes and are intentionally not built yet.

## Data discipline

The dataset behind this dashboard is small but the rules behind it are
strict. Every value comes from an official company source (annual reports,
quarterly results PDFs, regulatory filings). Every production change
follows a four-step pattern — staging, diagnostic, preview, controlled
rewrite — and every cell change is recorded with both the old and new
value in a per-pass audit log.

Where a company doesn't disclose a metric (Sun Pharma's SG&A, Otsuka's
quarterly breakdown), the dashboard shows a blank rather than a proxy.
Where reporting cadence is genuinely half-yearly or annual-only, the
dashboard labels it rather than fabricating quarters. Sector-level quarterly
views use Q1-Q4 rows only and group by Calendar_Quarter, so fiscal-quarter
labels land in the correct market-time bucket. The principle is: honest gaps
over confident guesses.

See [`audit/`](audit/) for the full methodology and the audit trail of
the Japan / India coverage batch.

## Features

- **Lifecycle filter** (sidebar) — show All companies, Full-cycle only, or
  Non-full-cycle only. Defaults to All.
- **Sector Overview** — companies in view, combined market cap, and combined
  broad-coverage calendar-quarter revenue. Updates with the lifecycle filter.
- **Sector Trend** — dollar-weighted sector ratio trends for R&D Intensity,
  Cash / Market Cap, and SG&A Intensity. Uses Q1-Q4 rows only, grouped by
  Calendar_Quarter, with coverage badges showing metric contributors,
  quarterly reporters, and companies in the active lifecycle filter.
- **Lifecycle Footprint** — the 5-stage pipeline (Discovery → Preclinical →
  Clinical Trials → FDA Review → Commercial) as a connected chip strip.
- **Strategic Posture Quadrant** — compares R&D Intensity with Cash /
  Market Cap to show whether companies combine scientific reinvestment with
  financial firepower. Median lines are relative to the active lifecycle filter;
  the chart is not a valuation or clinical-success signal.
- **Financial Snapshot** — latest Revenue, R&D, SG&A, Cash, Market Cap, plus
  R&D intensity and Cash / Market Cap, with the reporting period shown clearly.
- **Financial Trend** — pick a metric; the chart plots it over time with each
  reporting cadence (quarterly vs FY) drawn as its own line.
- **Data Sources** — profile source, financial data sources, reporting
  standard, and currency for the selected company.

The app reads two committed CSV files only. It makes **no external API calls**.

## Questions the dashboard answers

- **Sector Overview** — What is the aggregate size and latest broad-coverage revenue base of the selected biopharma universe?
- **Sector Trend** — Is the selected universe becoming more research-intensive, more cash-rich, or more SG&A-heavy over time?
- **Intelligence Map** — How does this company position commercially and scientifically against the rest of the industry?
- **Strategic Posture Quadrant** — Does this company have enough financial firepower to support its scientific investment?
- **Financial Snapshot** — What is this company’s latest reported financial position?
- **Financial Trend** — How has this company’s reported financial profile changed over time without mixing reporting cadences?
- **Data Sources** — Can I trace where the company’s financial and profile data came from?

## Project structure

```
.
├── app.py                  # page layout + module calls
├── data.py                 # CSV loading + derived tables (all cached)
├── charts.py               # lifecycle strip + company financial/intelligence charts
├── requirements.txt        # pinned dependencies
├── .gitignore
├── .streamlit/
│   └── config.toml         # dark theme
└── data/
    ├── Company_Master.csv
    └── Quarterly_Financials.csv
```

`app.py` must be at the repository root, and the `data/` folder and
`.streamlit/config.toml` must be committed — the app reads them at runtime.

## Run locally

Requires Python 3.11 or 3.12 (3.13 can cause dependency wheel issues).

```bash
python -m venv .venv

# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

The app opens at https://pharmabiotechmapping-ewsetptbhsm3npjygtssc5.streamlit.app/

## Deploy to Streamlit Community Cloud (private GitHub repo)

Streamlit Community Cloud **can deploy from a private repository** — you grant
it access during sign-in. Steps:

1. **Create a private GitHub repository** and push this project. Confirm
   `app.py` is at the repo root and that `data/`, `.streamlit/config.toml`,
   and `requirements.txt` are all committed.
2. Make sure a `.gitignore` is present so local files are not pushed:
   ```
   .venv/
   __pycache__/
   *.pyc
   .DS_Store
   .streamlit/secrets.toml
   ```
3. Go to **https://share.streamlit.io** and sign in with your GitHub account.
4. When prompted by GitHub, **authorize Streamlit and grant access to private
   repositories** (or grant access to this specific repo). This is required —
   without it, Streamlit cannot see a private repo.
5. In Streamlit Community Cloud, choose **Create app → deploy from a GitHub
   repo**, then select:
   - Repository: your private repo
   - Branch: `main`
   - Main file path: `app.py`
6. Click **Deploy**. Streamlit installs `requirements.txt` and builds the app
   (first build takes a few minutes).

Notes:
- The deployed app is private to your account by default. Add viewers under the
  app's **Settings → Sharing**.
- To update the live app, push a new commit to `main` — Streamlit redeploys
  automatically.

## Scope

MVP-1 only. Not built in this version:

- **MVP-2** — relationship/network map (edges driven by financial similarity).
- **MVP-3** — strategic posture quadrant (firepower vs R&D intensity).
