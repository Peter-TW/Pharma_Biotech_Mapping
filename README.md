# Biopharma Command Center

**A live intelligence dashboard that reconciles what the Top 50 biopharma companies *report* spending on R&D with what they're actually *running* in ClinicalTrials.gov — with M&A-aware sponsor attribution and reporting-cadence handling that survives the messiness of real disclosure data.**

🔗 **[Live demo →](https://pharmabiotechmapping-ewsetptbhsm3npjygtssc5.streamlit.app/)** &nbsp;·&nbsp; 🐍 Python · Streamlit · Pandas · ClinicalTrials.gov API v2 &nbsp;·&nbsp; Status: MVP-2 dashboard live

![Clinical Productivity vs. R&D Spend](docs/screenshots/01_bridge_chart.png)

*The headline chart: annualized reported R&D spend against owned active Phase III trial exposure, bubble-sized by log market cap. A strategic-posture overlay separates companies running lean clinical operations from those paying for late-stage runway.*

---

## TL;DR

Cross-company biopharma comparison is hard to do honestly. Companies disclose on different fiscal calendars (Q1–Q4, H1, 9M, FY). Subsidiary names break sponsor search on ClinicalTrials.gov, so Genentech trials look unrelated to Roche. Naive mean-of-ratios lets a $50M biotech outweigh Pfizer in sector aggregates. This dashboard solves those problems with **dollar-weighted aggregation**, **calendar-quarter alignment**, an **M&A-aware sponsor alias map**, and a **snapshot-diff change feed**. Every visible number has a defensible answer to *"where did this come from?"*

## Why I built this

I wanted to demonstrate end-to-end data craft on a domain I find genuinely interesting, under constraints that mirror real industry data engineering: heterogeneous sources, evolving entities (M&A), cadence mismatches, and the constant tension between *fast answer* and *honest answer*. The project deliberately picks the hard-mode default at each fork — dollar-weighted ratios over means-of-ratios, snapshot-based diffs over update-date heuristics, explicit expected-zero documentation over silent blanks — rather than the shortcut that would still render a chart.

## Skills demonstrated

| Area | What's in the repo |
|---|---|
| **Data engineering** | ClinicalTrials.gov API v2 extraction · sponsor alias resolution · snapshot-based change-feed architecture · auditable ETL |
| **Data modeling** | Calendar-quarter normalization across mixed cadences (Q/H/9M/FY) · M&A-aware entity resolution · ownership/participation filter contracts |
| **Statistics & methodology** | Dollar-weighted aggregation · coverage floors (50% trend, 80% headline) · mean-of-ratios pitfall avoidance · snapshot-diff event classification |
| **Product** | Live Streamlit deployment · mobile-first overview / desktop full-detail modes · KPI cards · NCT-level drill-through · stakeholder-facing limitation disclosures |
| **Domain** | Top 50 biopharma universe across NYSE/NASDAQ/TSE/HKEX/EU exchanges · ClinicalTrials.gov registry semantics · M&A history (Roche/Genentech, BMS/Celgene, Pfizer/Seagen, AbbVie/Allergan, GSK/ViiV, Takeda/Shire, Sanofi/Genzyme) |
| **Tech stack** | Python · Pandas · Streamlit · ClinicalTrials.gov API v2 · committed CSV data layer · Git/GitHub deployment |

## How to evaluate this in 5 minutes

If you're hiring and short on time, three things to look at:

1. **The bridge chart** (screenshot above, live in the dashboard) — does the financial × clinical comparison hold up against companies you know well?
2. **[Methodology in three points](#methodology-in-three-points)** — the three rules that drive every number on the dashboard, especially *"Dollar-weighted aggregation, not means-of-ratios"* and *"Honest gaps over confident guesses."*
3. **[`Sponsor_Alias_Map.csv`](data/clinical_trials/Sponsor_Alias_Map.csv)** and **[`ClinicalTrials_Alias_Reconciliation.csv`](data/clinical_trials/ClinicalTrials_Alias_Reconciliation.csv)** — the M&A-aware sponsor attribution layer with per-alias API yield tracking. This is where data engineering meets domain knowledge.

---

## More screenshots

### Mobile-first overview mode

![Mobile overview mode](docs/screenshots/02_mobile_overview.png)

Overview mode prioritizes summary cards and ranked context for quick review on narrow screens. Full detail mode (desktop) keeps the complete analytical charts.

### Company clinical drill-through

![Clinical Trial Footprint](docs/screenshots/03_clinical_footprint_nct_table.png)

KPI cards summarize owned and participated ClinicalTrials.gov exposure. The NCT table links back to the underlying registry records.

### Change feed and recent registry updates

![Clinical Change Feed and Recent Registry Updates](docs/screenshots/04_change_feed_recent_updates.png)

True status/phase/attribution change detection waits for the next monthly snapshot. Recent registry updates provide near-term visibility without mislabeling administrative edits as clinical events.

---

## What the dashboard answers

| Section | Question it answers |
|---|---|
| Sector Overview | What is the aggregate size and latest broad-coverage revenue base of the selected universe? |
| Sector Trend | Is the universe becoming more research-intensive, more cash-rich, or more SG&A-heavy over time? |
| Intelligence Map | How does this company compare commercially and scientifically with peers? |
| Strategic Posture Quadrant | Does this company have the cash buffer to support its R&D intensity? |
| Clinical Productivity vs. R&D Spend | Which companies show the largest late-stage clinical footprint relative to reported R&D investment? |
| Lifecycle Footprint | Where does this company participate across the therapeutic product lifecycle? |
| Financial Snapshot | What is this company's latest reported financial position? |
| Clinical Trial Footprint | What active, late-stage, and risk-flagged ClinicalTrials.gov records support this company's clinical footprint? |
| Clinical Change Feed | What changed recently in this company's ClinicalTrials.gov footprint? |
| Recent Registry Updates | Which ClinicalTrials.gov records for this company were recently updated in the registry? |
| Financial Trend | How has this company's reported financial profile changed over time without mixing reporting cadences? |
| Data Sources panel | Can I trace where the company's financial and profile data came from? |

---

## Methodology in three points

Three rules drive the charts, tables, and KPIs. Each is a deliberate choice over a more convenient alternative.

### 1. Dollar-weighted aggregation, not means-of-ratios

Sector-level ratios are computed as `Σ numerator ÷ Σ denominator` across paired rows where both parts are disclosed — never as the arithmetic mean of per-company ratios. A simple mean over R&D Intensity values would weight a $50M biotech equally with Pfizer; dollar-weighting reflects the sector's actual capital and revenue composition.

Coverage floors prevent one-company leading-edge periods from being misread as sector trends:

- **50% minimum** reporters per metric per quarter for sector trends
- **80% broad-coverage rule** for the headline revenue base

### 2. Calendar-quarter alignment for mixed cadences

Companies disclose financials on different fiscal calendars and cadences. Sector trends use Q1–Q4 rows only and group by `Calendar_Quarter`, not the company's fiscal `Period_Type`. FY, H1, and 9M reporters are surfaced in per-company views as separate cadence lines; they are not blended into quarterly sector trends.

Where a disclosed fiscal quarter differs from the normalized calendar quarter, both labels are shown.

### 3. Honest gaps over confident guesses

Where a company does not disclose a metric, the dashboard shows a blank rather than a proxy. Where a trial is registered under a subsidiary name not yet in the alias map, the gap is documented rather than silently papered over.

The operating principle: *every visible number should have a defensible answer if someone asks, "where did this come from?"*

---

## Data layers

### Financial layer

Two committed CSVs cover 2024–2026 reported periods for 50 companies across NYSE, NASDAQ, TSE, HKEX, and major European exchanges.

| File | Purpose |
|---|---|
| `data/Company_Master.csv` | Company identity, exchange, lifecycle flags, positioning inputs, source metadata |
| `data/Quarterly_Financials.csv` | Reported revenue, R&D, SG&A, cash, and market cap by disclosed period |
| `data/Dashboard_Data_Notes.csv` | Notes and caveats surfaced in selected dashboard views |

Periods are stored as disclosed (`Q1`–`Q4`, `H1`, `9M`, `FY`). Values are normalized to USD millions for cross-company comparison.

### Clinical-trial layer

Clinical data is built from ClinicalTrials.gov API v2 with an M&A-aware sponsor matching overlay.

| Layer | Purpose |
|---|---|
| `data/clinical_trials/ClinicalTrials_Inventory.csv` | Raw one-row-per-company-NCT match table |
| `data/clinical_trials/ClinicalTrials_Inventory_Normalized.csv` | Adds status buckets, phase buckets, phase weights, and filter-contract booleans |
| `data/clinical_trials/ClinicalTrials_Status_Summary.csv` | One-row-per-company KPI summary used by the dashboard |
| `data/clinical_trials/ClinicalTrials_Change_Feed.csv` | Append-only status/phase/attribution event log; currently cold-start |
| `data/clinical_trials/Expected_Zero_Companies.csv` | Explicit expected-zero documentation for Zoetis, Royalty Pharma, Danaher, and Elanco |
| `data/clinical_trials/Sponsor_Alias_Map.csv` | M&A-aware sponsor/subsidiary/acquired-entity alias map |
| `data/clinical_trials/ClinicalTrials_Alias_Reconciliation.csv` | Per-alias API yield and matching reconciliation |

The deployed app reads committed CSVs only. It does **not** call ClinicalTrials.gov live at runtime.

---

## What makes this defensible

### M&A-aware sponsor attribution

ClinicalTrials.gov sponsor search treats entities like `Pfizer` and `Seagen` as separate sponsors. The dashboard uses an M&A-aware alias layer so acquired or subsidiary-sponsored trials can be attributed to the current parent when the ownership rule supports it.

Examples in the alias map: Roche/Genentech, Pfizer/Seagen, AbbVie/Allergan, BMS/Celgene, Takeda/Shire, GSK/ViiV, Sanofi/Genzyme, and regional Japanese pharma subsidiaries.

### Spot-check reconciliation

Nine major companies were reconciled against ClinicalTrials.gov sponsor exports: Pfizer, Roche, Lilly, Vertex, Daiichi Sankyo, J&J, AbbVie, GSK, and Astellas. Where material gaps were found, alias-map rows were added with iteration notes and reviewer rationale.

### Snapshot-based change detection

The change feed is designed as a snapshot diff, not a guessed feed from update dates. It compares the current normalized inventory against the prior monthly snapshot and emits typed events:

- New trial
- Removed from match
- Status changed
- Phase changed
- Attribution changed
- Record updated

The first run is intentionally a cold start. The dashboard says so rather than inventing change events.

### Lifecycle classification with edge-case rules

Lifecycle flags mean meaningful participation in the human therapeutic product lifecycle. For infrastructure companies, flags reflect enabling role rather than asset ownership. For animal-health companies, human therapeutic stages are set to `FALSE` in the current MVP scope. Partnered/co-commercialized products and branded generics/biosimilars are handled through documented edge-case rules in the lifecycle audit trail.

---

## Known limitations

The dashboard surfaces these in-app so a reader is never misled about what a number represents.

- **Not an investment recommendation.** No fair-value estimates, price targets, or valuation upside calculations are produced.
- **ClinicalTrials.gov scope only.** Trials registered exclusively on jRCT, CTIS/EUCTR, ChiCTR, or other regional registries may be absent.
- **Registry exposure is not clinical quality.** Active Phase III count is a registry-derived exposure measure, not a probability-of-approval forecast or asset-quality score.
- **R&D Intensity is not pipeline quality.** It measures spending commitment relative to revenue.
- **Cash / Market Cap is not valuation upside.** It measures balance-sheet buffer relative to public market value.
- **Change feed is cold-start.** True status/phase/attribution changes appear only after at least two dated snapshots exist.
- **Alias coverage is iterative.** The largest sponsor attribution risks are documented and spot-checked, but smaller residual alias gaps may remain.

---

## Repository structure

```text
.
├── app.py
├── charts.py
├── data.py
├── README.md
├── requirements.txt
├── .streamlit/
│   └── config.toml
├── data/
│   ├── Company_Master.csv
│   ├── Quarterly_Financials.csv
│   ├── Dashboard_Data_Notes.csv
│   └── clinical_trials/
│       ├── ClinicalTrials_Inventory.csv
│       ├── ClinicalTrials_Inventory_Normalized.csv
│       ├── ClinicalTrials_Status_Summary.csv
│       ├── ClinicalTrials_Change_Feed.csv
│       ├── Expected_Zero_Companies.csv
│       ├── Sponsor_Alias_Map.csv
│       └── snapshots/
├── audit/
│   └── lifecycle_column_fix_audit.md
├── docs/
│   └── screenshots/
│       ├── 01_bridge_chart.png
│       ├── 02_mobile_overview.png
│       ├── 03_clinical_footprint_nct_table.png
│       └── 04_change_feed_recent_updates.png
└── scripts/
    ├── fetch_clinicaltrials_v2.py
    ├── build_clinical_signals.py
    ├── build_status_summary.py
    └── build_change_feed.py
```

---

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app expects all CSVs to be committed under `data/` and `data/clinical_trials/`. Large clinical detail files should be uploaded through Git/GitHub Desktop rather than GitHub's browser editor.

---

## Build phases

<details>
<summary><strong>MVP-1 — Financial intelligence layer</strong></summary>

| Phase | Status | Output | Purpose |
|---|---|---|---|
| P1 — Company universe setup | Complete | `Company_Master.csv` | Top 50 universe, identifiers, exchanges, lifecycle flags, source metadata, dashboard filter fields |
| P2 — Financial data extraction | Complete | `Quarterly_Financials.csv` | Reported revenue, R&D, SG&A, cash, and market cap across 2024–2026 reported periods |
| P3 — Cadence and calendar-quarter handling | Complete | Period/cadence logic in CSV + loaders | Keeps Q1–Q4, H1, 9M, and FY reporters comparable without creating synthetic quarters |
| P4 — Financial validation and audit | Complete | Validation checks + `Dashboard_Data_Notes.csv` | Captures data caveats, sparse periods, duplicate checks, missing values, latest-period selection logic |
| P5 — Dashboard integration | Complete | Streamlit financial dashboard | Sector Overview, Sector Trend, Intelligence Map, Strategic Posture, Lifecycle Footprint, Financial Snapshot, Financial Trend, Data Sources |

</details>

<details>
<summary><strong>MVP-2 — Clinical-trial intelligence layer</strong></summary>

| Phase | Status | Output | Purpose |
|---|---|---|---|
| P1 — ClinicalTrials.gov fetch | Complete | `ClinicalTrials_Inventory.csv` | One row per company-NCT match with sponsor alias and M&A-aware attribution |
| P2 — Trial normalization | Complete | `ClinicalTrials_Inventory_Normalized.csv` | Status buckets, phase buckets, phase weights, owned/participated filter flags |
| P3 — Company clinical summary | Complete | `ClinicalTrials_Status_Summary.csv` | Aggregates row-level trial data into one-row-per-company KPI inputs |
| P4 — Snapshot change feed | Cold-start | `ClinicalTrials_Change_Feed.csv` | Detects new/status/phase/attribution changes once at least two snapshots exist |
| P5a — Bridge chart | Complete | Clinical Productivity vs. R&D Spend | Connects annualized R&D spend to owned active Phase III / phase-weighted clinical exposure |
| P5b — Clinical detail panel | Complete | Clinical Trial Footprint | Company KPI cards, owned/participated scope, NCT-level table, registry links |
| P5c — Lifecycle audit | Complete / reviewable | `lifecycle_column_fix_audit.md` | Documents lifecycle edge-case rules; validates lifecycle filter behavior |
| P5d — Change-feed scaffold | Complete | Clinical Change Feed + Recent Registry Updates | Shows cold-start state honestly while surfacing recent registry update context |
| P5e — README polish | Complete | Portfolio-facing documentation | Screenshots, project narrative, deployment checks, roadmap |

</details>

---

## Deployment verification

Before treating a deployment as final:

- [ ] Streamlit app loads from the live URL
- [ ] Sidebar `Overview mode` works on mobile-width layout
- [ ] `Full detail mode` shows full bubble charts on desktop
- [ ] `ClinicalTrials_Inventory_Normalized.csv` is committed under `data/clinical_trials/`
- [ ] Clinical Trial Footprint table shows clickable NCT links
- [ ] Change Feed shows cold-start placeholder when no true diff events exist
- [ ] Recent Registry Updates panel displays selected-company registry updates
- [ ] No external API calls required at app runtime

---

## Roadmap

| Phase | Status | Notes |
|---|---|---|
| MVP-1 financial dashboard | Complete | Sector overview, trends, intelligence map, strategic posture, company financial detail |
| MVP-2 clinical intelligence | Complete | API v2 inventory, normalization, summary, bridge chart, clinical detail, lifecycle audit, change-feed scaffold |
| MVP-3 network map | Future | Asset, indication, and partnership graph |
| MVP-3 multi-registry expansion | Future | WHO ICTRP / CTIS / jRCT / ChiCTR integration |

---

*Built as a portfolio piece to demonstrate end-to-end data craft against real-world disclosure data — heterogeneous sources, evolving entities, cadence mismatches, and the constant choice between fast and honest.*
