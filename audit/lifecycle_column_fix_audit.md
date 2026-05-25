# P5c Lifecycle Column Fix Audit

**Audit date:** 2026-05-25 15:07:37 UTC  
**Scope:** `data/Company_Master.csv` lifecycle classification columns only.  
**Files changed:** `data/Company_Master.csv` and this audit file.  
**Files intentionally not changed:** `Quarterly_Financials.csv`, clinical-trial CSVs, `app.py`, `data.py`, `charts.py`.

## Purpose

P5c fixes the five lifecycle columns used by the dashboard sidebar filter, lifecycle footprint strip, company positioning logic, and clinical-financial bridge cohort interpretation:

- `Discovery`
- `Preclinical`
- `Clinical Trials`
- `FDA Review`
- `Commercial`

The goal is to avoid forcing animal-health, CDMO/tools, diagnostics, retail/pharmacy, consumer OTC, and generic-heavy business models into the same full human therapeutic lifecycle model as integrated biopharma companies.

## Classification rules used

A lifecycle flag is `TRUE` only when there is a defensible company-level reason.

| Lifecycle stage | Rule |
|---|---|
| Discovery | Internal discovery / research platform capability, or regular origination of therapeutic candidates, targets, or modalities. |
| Preclinical | Company advances candidates through preclinical development, toxicology, IND-enabling work, or equivalent early development. |
| Clinical Trials | Company sponsors, owns, or materially operates therapeutic clinical trials. Collaborator-only participation is not sufficient by itself. |
| FDA Review | Company is responsible for regulatory approval, submissions, label expansions, or therapeutic product regulatory strategy. |
| Commercial | Company markets, sells, distributes, or monetizes approved therapeutic / healthcare products directly as therapeutic product owner. |

## Before / after lifecycle counts

| Lifecycle column | Before TRUE count | After TRUE count |
|---|---:|---:|
| Discovery | 44 | 41 |
| Preclinical | 45 | 41 |
| Clinical Trials | 46 | 41 |
| FDA Review | 45 | 43 |
| Commercial | 47 | 44 |

## Full-cycle count

| Metric | Before | After |
|---|---:|---:|
| Full-cycle companies | 41 | 37 |
| Non-full-cycle companies | 9 | 13 |

## Cell-level changes

**Total lifecycle cell changes:** 17  
**Companies changed:** 9

| Unique_ID | Company Name | Column | Before | After | Reason |
|---|---|---|---|---|---|
| CMP-022 | Zoetis Inc. | Clinical Trials | TRUE | FALSE | Animal-health company in this MVP's human ClinicalTrials.gov scope; do not mark as human therapeutic clinical-trial lifecycle participant. |
| CMP-030 | Haleon plc | Clinical Trials | TRUE | FALSE | Consumer OTC / wellness portfolio; not treated as an integrated human therapeutic clinical-trial operator for this dashboard. |
| CMP-032 | Sun Pharmaceutical Industries | Discovery | TRUE | FALSE | Generics and specialty-branded model; clinical/commercial activity retained, but discovery-stage originator capability not assumed at company level. |
| CMP-032 | Sun Pharmaceutical Industries | Preclinical | TRUE | FALSE | Generics and specialty-branded model; preclinical-originator capability not assumed at company level. |
| CMP-035 | Lonza | Preclinical | TRUE | FALSE | CDMO / manufacturing-services business; not a therapeutic product sponsor progressing assets through preclinical development. |
| CMP-035 | Lonza | Clinical Trials | TRUE | FALSE | CDMO / manufacturing-services business; may support trials operationally but is not counted as a therapeutic clinical-trial lifecycle owner. |
| CMP-035 | Lonza | FDA Review | TRUE | FALSE | CDMO / manufacturing-services business; not counted as the regulatory owner of therapeutic product submissions. |
| CMP-035 | Lonza | Commercial | TRUE | FALSE | CDMO / manufacturing-services business; not counted as commercializing approved therapeutic products directly. |
| CMP-036 | LabCorp | FDA Review | TRUE | FALSE | Diagnostics / clinical laboratory business; not counted as a therapeutic-product regulatory owner. |
| CMP-036 | LabCorp | Commercial | TRUE | FALSE | Diagnostics / clinical laboratory business; not counted as commercializing approved therapeutic products directly in this therapeutic lifecycle model. |
| CMP-039 | CVS Health Corporation | Commercial | TRUE | FALSE | Retail pharmacy / healthcare services business; not treated as therapeutic product commercialization owner in this lifecycle model. |
| CMP-042 | Viatris Inc. | Discovery | TRUE | FALSE | Generics / biosimilars model; discovery-stage originator capability not assumed at company level. |
| CMP-042 | Viatris Inc. | Preclinical | TRUE | FALSE | Generics / biosimilars model; preclinical-originator capability not assumed at company level. |
| CMP-047 | Danaher | Discovery | TRUE | FALSE | Life-sciences tools / Cytiva-related infrastructure company; not counted as therapeutic discovery-stage operator. |
| CMP-047 | Danaher | Preclinical | TRUE | FALSE | Life-sciences tools / manufacturing infrastructure company; not counted as therapeutic preclinical operator. |
| CMP-047 | Danaher | Clinical Trials | TRUE | FALSE | Life-sciences tools / manufacturing infrastructure company; not counted as therapeutic clinical-trial sponsor/operator. |
| CMP-049 | Elanco Animal Health Incorporated | Clinical Trials | TRUE | FALSE | Animal-health company in this MVP's human ClinicalTrials.gov scope; do not mark as human therapeutic clinical-trial lifecycle participant. |

## Correct non-full-cycle company list after P5c

There are **13** non-full-cycle companies after the lifecycle fix:

- CMP-022 — Zoetis Inc.
- CMP-030 — Haleon plc
- CMP-032 — Sun Pharmaceutical Industries
- CMP-035 — Lonza
- CMP-036 — LabCorp
- CMP-037 — BioNTech
- CMP-038 — Abbott Laboratories
- CMP-039 — CVS Health Corporation
- CMP-042 — Viatris Inc.
- CMP-043 — Royalty Pharma plc
- CMP-046 — Revolution Medicines
- CMP-047 — Danaher
- CMP-049 — Elanco Animal Health Incorporated

**Note:** Summit Therapeutics Inc. remains **full-cycle** in the updated `Company_Master.csv`. It should not be listed as non-full-cycle in the P5c documentation.

## Full-cycle company list after P5c

There are **37** full-cycle companies after the lifecycle fix:

- CMP-001 — Ono Pharmaceutical Co., Ltd.
- CMP-002 — Eli Lilly & Co.
- CMP-003 — Johnson & Johnson
- CMP-004 — AbbVie
- CMP-005 — Roche
- CMP-006 — AstraZeneca
- CMP-007 — Novartis AG
- CMP-008 — Merck & Co
- CMP-009 — Novo Nordisk
- CMP-010 — Amgen Inc.
- CMP-011 — Gilead Sciences
- CMP-012 — Pfizer
- CMP-013 — Bristol Myers Squibb
- CMP-014 — Vertex Pharmaceuticals
- CMP-015 — Sanofi
- CMP-016 — Regeneron Pharmaceuticals
- CMP-017 — Remegen
- CMP-018 — Merck KGaA
- CMP-019 — Takeda Pharmaceutical
- CMP-020 — Bayer
- CMP-021 — Otsuka Holdings Co., Ltd.
- CMP-023 — BeOne Medicines
- CMP-024 — Daiichi Sankyo
- CMP-025 — Biogen
- CMP-026 — Astellas Pharma
- CMP-027 — Chugai Pharmaceutical
- CMP-028 — Moderna, Inc.
- CMP-029 — CSL Limited
- CMP-031 — Alnylam Pharmaceuticals
- CMP-033 — United Therapeutics Corporation
- CMP-034 — GlaxoSmithKline
- CMP-040 — Neurocrine Biosciences
- CMP-041 — Incyte Corporation
- CMP-044 — Summit Therapeutics Inc.
- CMP-045 — Jazz Pharmaceuticals plc
- CMP-048 — BioMarin Pharmaceutical
- CMP-050 — Insmed

## Future review item

- **CMP-038 — Abbott Laboratories:** remains classified as `FDA Review = TRUE` and `Commercial = TRUE`, with `Discovery`, `Preclinical`, and `Clinical Trials` set to `FALSE`. This reflects its established pharmaceuticals / medical-device commercialization profile in the current dashboard model. Review again if the project later enforces a pure human NME therapeutic-developer constraint.

## Validation checklist

| Check | Result |
|---|---|
| `Company_Master.csv` has exactly 50 rows | PASS |
| `Unique_ID` remains unique | PASS |
| No blank `Unique_ID` values | PASS |
| Lifecycle columns contain TRUE/FALSE-compatible values only | PASS |
| No lifecycle column names changed | PASS |
| Updated full-cycle count is 37 | PASS |
| Updated non-full-cycle count is 13 | PASS |
| Expected-zero clinical companies are not incorrectly marked as full-cycle human therapeutic operators | PASS |
| `data.py` / `app.py` syntax compatibility checked by Antigravity | PASS |

## Commit guidance

Commit:

- `data/Company_Master.csv`
- `audit/lifecycle_column_fix_audit.md`

Do **not** commit the local backup file `Company_Master.csv.bak_p5c` to the production repo unless it is intentionally placed in a clearly marked audit/backup archive.
