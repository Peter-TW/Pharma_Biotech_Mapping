# Biopharma Command Center

An intelligence layer for the Top 50 biopharma companies, bridging reported
financial discipline with clinical-trial reality. Built on committed CSV
datasets with strict attribution rules, hybrid reporting-cadence handling,
and a fully auditable data trail.

The project is intentionally small in surface area and high in methodology
density. Every value comes from an official source (SEC filings, company
annual reports, ClinicalTrials.gov registry). Every data change is recorded
in per-pass audit logs. Every cross-company comparison applies a single
documented rule — dollar-weighted ratios, calendar-quarter alignment, and
M&A-aware sponsor attribution.

> **Live app:** _(deploy link to be added)_
>
> **Status:** MVP-1 financial dashboard is live. MVP-2 clinical data layer
> is complete and committed (62,551 trial records across 50 companies,
> 5 alias-map iterations, 9-company spot-check reconciliation, P4 change
> feed in cold-start state awaiting next monthly snapshot). MVP-2
> dashboard integration is in progress. The Clinical Productivity vs.
> R&D Spend bridge chart is live (P5a). Company detail panel, change
> feed, and lifecycle column fix are next (P5b–P5d).

---

## Methodology in three points

This dashboard exists because cross-company biopharma comparison is
unreasonably hard to do honestly. Three rules drive every chart, table,
and KPI.

### 1. Dollar-weighted aggregation, not means-of-ratios

Sector-level ratios are computed as `Σ numerator ÷ Σ denominator` across
paired rows where both parts are disclosed, not as the average of
per-company ratios. A simple mean over R&D Intensity values would weight
a $50M biotech equally with Pfizer; dollar-weighting reflects the true
sector composition. Coverage floors (50% minimum reporters per metric per
quarter, 80% for the headline revenue base) prevent one-company
leading-edge periods from being mistaken for sector trends.

### 2. Calendar-quarter alignment for mixed cadences

Companies disclose financials on different fiscal calendars (Pfizer's
calendar-aligned quarters, Daiichi Sankyo's March year-end, Roche's
half-year cadence). The dashboard separates Q1–Q4 rows from H1, 9M, and
FY rows. Quarterly sector trends group by `Calendar_Quarter`, never by
`Period_Type`, so Daiichi's fiscal Q1 (April–June) lands in Calendar Q2.
FY and H1 reporters never get annualized-then-divided to fake quarters.
Where the disclosed fiscal quarter differs from the normalized calendar
quarter, both labels are shown.

### 3. Honest gaps over confident guesses

Where a company doesn't disclose a metric — Sun Pharma's SG&A,
Astellas's some-period R&D breakdown — the dashboard shows a blank, not
a proxy. Where a clinical trial is registered under a regional
subsidiary name not yet in the alias map, that gap is documented rather
than papered over. The principle: an interviewer can probe any cell and
get a defensible answer about why it shows what it shows.

---

## What's in the project

### Financial layer (MVP-1 — live)

Two committed CSVs (`Company_Master.csv`, `Quarterly_Financials.csv`)
covering 2024–2026 reported periods for 50 companies across NYSE,
NASDAQ, TSE, HKEX, and major European exchanges. Periods stored as
disclosed (Q1–Q4, H1, 9M, FY). FX-normalized to USD millions at
period-end rates.

**Dashboard sections currently rendering:**

| Section | Question it answers |
|---|---|
| Sector Overview | Aggregate size and latest broad-coverage revenue base of the selected universe |
| Sector Trend | Is the universe becoming more research-intensive, more cash-rich, or more SG&A-heavy over time? |
| Intelligence Map | How does this company position commercially and scientifically against the rest of the industry? |
| Strategic Posture Quadrant | Does this company have enough financial firepower to support its scientific investment? |
| Lifecycle Footprint | Where does this company participate across the therapeutic product lifecycle? |
| Financial Snapshot | What is this company's latest reported financial position? |
| Financial Trend | How has this company's reported financial profile changed over time without mixing reporting cadences? |
| Data Sources panel | Can I trace where the company's financial and profile data came from? |

### Clinical-trial layer (MVP-2 data — complete; dashboard integration in progress)

Five committed CSV layers built from ClinicalTrials.gov API v2 with an
M&A-aware sponsor matching overlay:

| Layer | Rows | Purpose |
|---|---:|---|
| `ClinicalTrials_Inventory.csv` | 62,551 | One row per company-NCT match; raw values preserved |
| `ClinicalTrials_Inventory_Normalized.csv` | 62,551 | Adds status buckets, phase buckets (exclusive + inclusive), filter-contract booleans |
| `ClinicalTrials_Status_Summary.csv` | 50 × 62 cols | Per-company KPI aggregates with Active × Phase cross-tabs |
| `ClinicalTrials_Change_Feed.csv` | 0 (cold start) | Append-only event log of status/phase/attribution changes between monthly snapshots |
| `snapshots/<YYYY-MM-DD>/` | 1 archive | Dated copies of the normalized inventory for change-feed diff comparison |

Supporting infrastructure:
- `Sponsor_Alias_Map.csv` — 328 sponsor aliases across 5 iterations, each with `Added_In_Iteration` and `Iteration_Reason` for audit
- `ClinicalTrials_Alias_Reconciliation.csv` — per-alias yield (API total → rows written), for spot-check validation
- `ClinicalTrials_Fetch_Audit.csv`, `ClinicalTrials_Normalize_Audit.csv`, `ClinicalTrials_Summary_Audit.csv`, `ClinicalTrials_Change_Feed_Audit.csv` — append-only run logs
- `Expected_Zero_Companies.csv` — explicit zero-trial documentation for Zoetis, Royalty Pharma, Cytiva, Elanco (non-pharma businesses)

### The bridge chart (MVP-2 visualization — next)

The headline visualization wires the financial layer to the clinical
layer: a "Clinical Productivity vs. R&D Spend" bubble chart with R&D
spend on X (log scale), Active Phase III trial count on Y, market cap
as bubble size, and the financial-discipline + M&A-aware-attribution
machinery underwriting both axes. This is what the layered data work
above was built for.

---

## What makes this defensible

A small biopharma intelligence dashboard is not a novel concept. What
matters is whether the data underneath it survives scrutiny. The
methodology choices below are the things to probe during an interview.

### M&A-aware sponsor attribution

ClinicalTrials.gov's sponsor search treats "Pfizer" and "Seagen" as
different entities. The dashboard's M&A overlay correctly attributes
inherited Seagen trials to Pfizer (acquired December 2023) using a
documented rule: trials count under the parent for snapshots after the
ownership-effective date. The same logic applies to Roche/Genentech
(1,562 inherited trials), AbbVie/Allergan (728), AbbVie/Pharmacyclics
(111), BMS/Celgene (478), Lilly/Loxo, Takeda/Shire/Baxalta/Millennium,
GSK/ViiV/Stiefel/HGS, Sanofi/Pasteur/Genzyme, Astellas regional
subsidiaries, and 30+ other documented acquisitions across the alias
map's 5 iterations.

The overlay surfaces approximately 3,035 trials across the 9
spot-checked companies that ClinicalTrials.gov's naive sponsor search
does not — Roche/Genentech alone is the largest single example.

### Spot-check reconciliation against ClinicalTrials.gov

Nine of the 50 Top-50 companies (Pfizer, Roche, Lilly, Vertex, Daiichi
Sankyo, J&J, AbbVie, GSK, Astellas) were directly reconciled against
ClinicalTrials.gov sponsor exports. For each, the dashboard's Lead
Sponsor count was confirmed within ±1 trial of the registry; the M&A
overlay's added trials were independently validated. Where alias gaps
were found (Janssen verbose names, regional subsidiaries for Japanese
pharma, GSK's ViiV / Stiefel / HGS / Sirtris, Sanofi's Pasteur /
Genzyme / Kadmon), they were fixed via iterative alias-map additions
with each iteration tagged in the data.

The reconciliation methodology is documented; the remaining 41
companies use seed alias map only, with bounded expected gap per
company.

### Hybrid reporting-cadence handling

Sector trends use Q1–Q4 rows only, grouped by `Calendar_Quarter`. FY
and H1 reporters are surfaced in per-company views as separate cadence
lines, never blended into a quarterly trend. The cadence pre-scan
identifies each company's actual filing frequency rather than assuming
based on exchange. Determinism in latest-snapshot selection is enforced
via period-priority tie-breaking (FY beats Q4 on same end-date),
preventing CSV-row-order dependencies.

### Per-pass audit trail

Every data change — a corrected ticker mapping, a newly added
subsidiary alias, a M&A ownership-effective-date update — is recorded
in per-layer audit CSVs with run ID, timestamp, input/output row counts,
and validation status. Five alias-map iterations are fully traceable
via `Added_In_Iteration` / `Iteration_Reason` columns.

### Idempotent snapshot-based change detection

The change feed compares the current normalized inventory against the
prior month's archived snapshot. Each detected event (status change,
phase change, attribution change, new trial, removed trial) is
identified by a SHA-1 hash of `Snapshot_Date_Current + Unique_ID +
NCT_ID + Change_Type`, making the diff process idempotent — re-running
the same snapshot pair produces zero new events. The event log is
append-only across all runs; the dashboard surfaces 30-day and 90-day
windows as filter expressions over the same underlying data.

---

## Known data attribution limitations

Honesty about what isn't covered.

**Sponsor alias coverage spot-check scope.** Nine of 50 Top-50
companies were systematically reconciled. Material alias gaps were
found and fixed in 6 of those 9 — driven by two recurring patterns:

- **Japanese pharma regional subsidiaries** (Astellas, Otsuka, Takeda)
  register US, EU, and Asia operations under distinct legal entities
  (e.g., "Astellas Pharma Global Development, Inc.", "Otsuka
  Pharmaceutical Development & Commercialization", "Millennium
  Pharmaceuticals, Inc.").
- **Western pharma historical acquisitions** (GSK's ViiV / Stiefel /
  HGS, Sanofi's Pasteur / Genzyme / Kadmon, Novartis Vaccines /
  Sandoz, BMS Karuna) register with verbose ClinicalTrials.gov
  annotations of the form "X, a Y Company".

Both patterns were closed via iterative alias-map additions. The
41 unspot-checked Top-50 companies use the seed alias map only;
expected materiality of remaining gaps is bounded by the per-company
impact of audited cases (typically <100 active-status trials).

**Spinoff and divestiture cases.** Five known spinoff cases are
attributed by Option A — trials count under the entity that was the
legal sponsor at registration, which is the more defensible choice for
historical and time-series attribution:

| Spinoff | Effective date | Pre-spinoff trials attributed to |
|---|---|---|
| Abbott → AbbVie | January 2013 | Abbott Laboratories |
| Pfizer Upjohn → Viatris | November 2020 | Pfizer |
| J&J Consumer → Kenvue | August 2023 | J&J |
| Novartis → Sandoz | October 2023 | Novartis |
| Novartis Vaccines → GSK | March 2015 | Novartis |

**Non-US registry scope.** The clinical-trial layer sources from
ClinicalTrials.gov only. Trials registered exclusively on jRCT (Japan),
CTIS / EUCTR (EU), or ChiCTR (China) are not included. This
particularly affects Japanese and European companies for region-only
late-stage programs.

**Verbose-annotation residual gap.** ClinicalTrials.gov prepends
strings like "Wyeth is now a wholly owned subsidiary of Pfizer" to
inherited-trial sponsor names. The dashboard's M&A overlay matches the
bare entity names; verbose variants caught roughly 85% of these across
spot-checks. Residual gap is approximately 800 trials across the
Top-50 universe (~1.3% of inventory), predominantly Completed status.

**Phase IV and observational trials.** Phase IV (post-approval) and
non-phased / observational studies are correctly normalized but
excluded from the bridge chart's Y-axis. They appear in the company
detail panel for completeness.

**Change feed cold-start.** The 30-day and 90-day change feed populates
only when two or more dated snapshots exist. The first snapshot
(2026-05-24) is archived; the next monthly refresh will trigger the
first diff events. Until then, the change feed widget shows
"Awaiting next snapshot."

---

## What this dashboard does NOT claim

- Not a stock recommendation tool. No fair-value estimates, no price
  targets, no valuation upside calculation.
- R&D Intensity measures spending commitment, not pipeline quality or
  clinical probability of success.
- Cash / Market Cap measures balance-sheet buffer relative to valuation,
  not whether a stock is undervalued.
- Active Phase III count is a registry-derived exposure measure, not a
  probability-of-approval forecast. Differences in trial size, indication,
  and outsourcing model make cross-company productivity ratios indicative
  only.
- Trial counts are not asset counts. A single drug program may run
  multiple trials. The dashboard treats each NCT as one unit.

---

## Project structure

```
.
├── app.py                          # Streamlit page layout + section text
├── data.py                         # Financial CSV loading + derived tables (cached)
├── charts.py                       # Sector and company chart code
├── requirements.txt                # Pinned dependencies
├── .gitignore
├── .streamlit/
│   └── config.toml                 # Dark theme
├── implementation_plan.md          # Full methodology spec (v4.3 + iter 5 notes)
├── data/
│   ├── Company_Master.csv          # Entity anchor
│   ├── Quarterly_Financials.csv    # Financial layer
│   ├── Dashboard_Data_Notes.csv    # Optional row-level reviewer notes
│   └── clinical_trials/
│       ├── Sponsor_Alias_Map.csv             # 328 aliases, 5 iterations
│       ├── ClinicalTrials_Inventory.csv      # 62,551 raw matched trials
│       ├── ClinicalTrials_Inventory_Normalized.csv
│       ├── ClinicalTrials_Status_Summary.csv # 50 × 62 KPIs
│       ├── ClinicalTrials_Change_Feed.csv    # event log (cold-start)
│       ├── ClinicalTrials_Alias_Reconciliation.csv
│       ├── ClinicalTrials_Fetch_Audit.csv
│       ├── ClinicalTrials_Normalize_Audit.csv
│       ├── ClinicalTrials_Summary_Audit.csv
│       ├── ClinicalTrials_Change_Feed_Audit.csv
│       ├── Expected_Zero_Companies.csv
│       └── snapshots/
│           └── 2026-05-24/                   # archived prior inventory
│               └── ClinicalTrials_Inventory_Normalized.csv
└── scripts/
    ├── fetch_clinicaltrials_v2.py          # P1: ClinicalTrials.gov fetch
    ├── archive_snapshot.py                 # P0: snapshot archival (run BEFORE P1)
    ├── build_clinical_signals.py           # P2: status/phase normalization
    ├── build_status_summary.py             # P3 + P3.1: per-company aggregation
    ├── build_change_feed.py                # P4: change detection
    └── update_seed_phase_*.py              # Iterations 2-5 alias-map patches
```

The app reads committed CSV files only — **no external API calls at
runtime.** Clinical data is refreshed via the monthly cadence below;
the live app serves the most recent committed snapshot.

---

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

---

## Monthly clinical data refresh workflow

The clinical data layer refreshes on a monthly cadence. **Run scripts
in the exact order below** — the archive step must happen before P1
overwrites the live inventory, otherwise the prior snapshot is lost
and the next change-feed diff falls back to cold-start mode.

### Required order

```bash
# Step 0 — Archive the current normalized inventory BEFORE re-fetching.
# This locks the prior month's snapshot into data/clinical_trials/snapshots/
# so the change feed has a baseline to diff against.
python scripts/archive_snapshot.py

# Step 1 — Re-fetch from ClinicalTrials.gov API v2 and rebuild the inventory.
# Will overwrite ClinicalTrials_Inventory.csv with new data.
python scripts/fetch_clinicaltrials_v2.py

# Step 2 — Re-normalize status and phase columns from the new inventory.
python scripts/build_clinical_signals.py

# Step 3 — Re-aggregate per-company KPIs into the status summary.
python scripts/build_status_summary.py

# Step 4 — Detect changes vs. the prior archived snapshot and append
# events to the change feed.
python scripts/build_change_feed.py
```

Each script appends to its own audit CSV with run ID, validation
status, and row-count diff. After running, verify the four audit logs
show `Validation_Status = "PASS"` (the change feed audit will show
`COLD_START` only on the very first run; on subsequent runs it should
show `PASS` with a non-zero event count in `Events_Written`).

### Suggested cadence

Monthly. The 30-day and 90-day change-feed windows assume monthly
snapshots; running more frequently produces larger event volumes
(useful for active investigation), running less frequently degrades
the 30-day window's usefulness.

### Future automation note

`archive_snapshot.py` is currently a standalone step that must be
invoked manually before P1. For full automation, add a one-line
`subprocess.run` call near the top of `fetch_clinicaltrials_v2.py`
that invokes `archive_snapshot.py` before any inventory write. The
script is idempotent — invoking it twice in one session is safe
(it will not re-archive a snapshot directory that already exists).

### Recovery from missed archive

If a monthly refresh ran without invoking `archive_snapshot.py` first:
- The prior month's snapshot is lost
- The next change-feed run will detect this and fall back to cold-start
  state for one cycle
- The two-snapshot cadence resumes naturally on the following month
- No corruption to the inventory or any prior audit logs

This is a soft failure, not a hard one. Document it in `Reviewer_Notes`
in the audit log if it happens.

---

## Deploy to Streamlit Community Cloud

1. Push to GitHub. Confirm `app.py` is at the repo root and that
   `data/`, `data/clinical_trials/`, `.streamlit/config.toml`, and
   `requirements.txt` are committed.
2. Add to `.gitignore`:
   ```
   .venv/
   __pycache__/
   *.pyc
   .DS_Store
   .streamlit/secrets.toml
   ```
3. Connect Streamlit Community Cloud to the GitHub repo, select the
   branch, and set the main file path to `app.py`.
4. Deploy. Future pushes redeploy automatically.

Note: the deployed app reads committed data files only. It does NOT
trigger the monthly refresh — that is a separate operational task run
locally by the maintainer, with the regenerated CSVs committed and
pushed for the deployed app to pick up.

---

## Roadmap

| Stage | Status |
|---|---|
| MVP-1 financial dashboard | Complete |
| MVP-2 P1 — clinical inventory | Complete |
| MVP-2 P2 — status/phase normalization | Complete |
| MVP-2 P3 — per-company status summary | Complete |
| MVP-2 P3.1 — Active × Phase cross-tab columns | Complete |
| MVP-2 P4 — 30/90-day change feed | Cold-start; activates on next monthly refresh |
| MVP-2 P5a — bridge chart (Clinical Productivity vs. R&D Spend) | Complete |
| MVP-2 P5b — company clinical KPI cards + NCT detail panel | Pending |
| MVP-2 P5c — lifecycle column fix | Pending |
| MVP-2 P5d — change feed scaffold + recent registry updates | Pending |
| MVP-2 P5e — README polish + screenshot + deploy verification | Pending |
| MVP-2 P6 — auto-integrate archive into P1 fetch | Pending; manual workaround documented above |
| MVP-3 relationship/network map | Future |
| MVP-3 WHO ICTRP integration for non-US registries | Future |
| MVP-3 asset-level pipeline depth (Phase × indication × modality) | Future |

---

## Acknowledgements and references

Data sources:
- Company financials: SEC EDGAR, company investor relations,
  Tokyo Stock Exchange disclosure, Hong Kong Stock Exchange disclosure,
  Euronext / SIX / LSE disclosure
- Clinical trials: ClinicalTrials.gov API v2 (modern REST API, OpenAPI 3.0)
- FX rates: period-end historical rates (EUR 1.08, JPY 0.00685, HKD 0.128)

Reference works that shaped the methodology choices:
- Citeline Pharmaprojects / Trialtrove (industry-standard pipeline tracker,
  benchmark for sponsor matching discipline)
- ClinicalTrials.gov API v2 documentation
- SEC 8-K filings for M&A ownership-effective-date verification
