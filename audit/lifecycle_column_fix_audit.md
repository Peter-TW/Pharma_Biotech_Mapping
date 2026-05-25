# Audit Trail: Lifecycle Column Corrections (Revised)

**Audit Date/Time:** 2026-05-25T16:20:00Z
**Files Changed:** `Company_Master.csv`

---

## 1. Executive Summary & Revised Decision Rules

This audit documents the systematic correction of the five lifecycle stage columns (`Discovery`, `Preclinical`, `Clinical Trials`, `FDA Review`, `Commercial`) in `Company_Master.csv`.

### Revised Core Rule:
> **“Lifecycle flags mean meaningful participation in the human therapeutic product lifecycle. For infrastructure companies, flags reflect enabling role, not asset ownership. For animal-health companies, human therapeutic stages are set to FALSE in MVP scope.”**

- **Therapeutic Asset Owners:** Flags represent owned/sponsored drug discovery, clinical development, regulatory approval, and commercial sales.
- **Development/Manufacturing Enablers (CDMOs & Tools):** Flags represent enabling/supporting roles (e.g. bioprocess supply, clinical trial manufacturing, regulatory process packages, or diagnostics CRO services) rather than asset ownership.
- **Animal Health Providers:** Sourced veterinary drugs are excluded from the human therapeutic scope. Under this MVP framework, animal health companies are classified as FALSE across all five human-therapeutic stages.
- **Retail/Pharmacy/Insurance Service Providers:** Sourced activities do not represent therapeutic drug commercialization and are classified as FALSE across all stages.

---

## 2. Before vs. After Summary Stats

| Metric / Stage | Before Baseline Count | Corrected After Count | Net Change |
|---|---|---|---|
| **Total Companies** | 50 | 50 | 0 |
| **Discovery = TRUE** | 44 | 41 | -3 |
| **Preclinical = TRUE** | 45 | 41 | -4 |
| **Clinical Trials = TRUE** | 46 | 41 | -5 |
| **FDA Review = TRUE** | 45 | 43 | -2 |
| **Commercial = TRUE** | 47 | 44 | -3 |
| **Full-cycle profile (all 5 TRUE)** | 41 | 37 | -4 |
| **Non-full-cycle profile** | 9 | 13 | +4 |
| **Non-pharma / infrastructure / other** | 0 | 4 | +4 |

- **Unique_ID Integrity:** Handled as strictly unique with zero blank values across exactly 50 rows.
- **Lifecycle Column Values:** Coerced to contain only case-insensitive `"TRUE"` or `"FALSE"` values in the raw CSV.
- **Total lifecycle cell changes after this correction (from baseline):** **21 cell changes** (affecting 8 companies).

---

## 3. Complete Change Log Table (From Baseline)

The following table documents the 21 cell modifications applied to the baseline master sheet to arrive at the corrected state:

| Unique_ID | Company Name | Column | Before | After | Reason |
|---|---|---|---|---|---|
| CMP-047 | Danaher | Discovery | True | False | Danaher/Cytiva is tools provider enabling preclinical/clinical dev and commercial manufacturing, but no FDA review role. |
| CMP-047 | Danaher | Commercial | False | True | Danaher/Cytiva is tools provider enabling preclinical/clinical dev and commercial manufacturing, but no FDA review role. |
| CMP-036 | LabCorp | Preclinical | False | True | LabCorp is diagnostics/CRO provider enabling preclinical and clinical research, but no FDA review or commercial drug role. |
| CMP-036 | LabCorp | Clinical Trials | False | True | LabCorp is diagnostics/CRO provider enabling preclinical and clinical research, but no FDA review or commercial drug role. |
| CMP-036 | LabCorp | FDA Review | True | False | LabCorp is diagnostics/CRO provider enabling preclinical and clinical research, but no FDA review or commercial drug role. |
| CMP-036 | LabCorp | Commercial | True | False | LabCorp is diagnostics/CRO provider enabling preclinical and clinical research, but no FDA review or commercial drug role. |
| CMP-039 | CVS Health Corporation | Commercial | True | False | CVS Health is pharmacy retail/insurance player with no role in drug development or commercialization. |
| CMP-022 | Zoetis Inc. | Discovery | True | False | Zoetis is animal-health company. Set FALSE under human-scoped therapeutic lifecycle. |
| CMP-022 | Zoetis Inc. | Preclinical | True | False | Zoetis is animal-health company. Set FALSE under human-scoped therapeutic lifecycle. |
| CMP-022 | Zoetis Inc. | Clinical Trials | True | False | Zoetis is animal-health company. Set FALSE under human-scoped therapeutic lifecycle. |
| CMP-022 | Zoetis Inc. | FDA Review | True | False | Zoetis is animal-health company. Set FALSE under human-scoped therapeutic lifecycle. |
| CMP-022 | Zoetis Inc. | Commercial | True | False | Zoetis is animal-health company. Set FALSE under human-scoped therapeutic lifecycle. |
| CMP-049 | Elanco Animal Health Incorporated | Discovery | True | False | Elanco is animal-health company. Set FALSE under human-scoped therapeutic lifecycle. |
| CMP-049 | Elanco Animal Health Incorporated | Preclinical | True | False | Elanco is animal-health company. Set FALSE under human-scoped therapeutic lifecycle. |
| CMP-049 | Elanco Animal Health Incorporated | Clinical Trials | True | False | Elanco is animal-health company. Set FALSE under human-scoped therapeutic lifecycle. |
| CMP-049 | Elanco Animal Health Incorporated | FDA Review | True | False | Elanco is animal-health company. Set FALSE under human-scoped therapeutic lifecycle. |
| CMP-049 | Elanco Animal Health Incorporated | Commercial | True | False | Elanco is animal-health company. Set FALSE under human-scoped therapeutic lifecycle. |
| CMP-030 | Haleon plc | Clinical Trials | True | False | Haleon is consumer OTC company. Set FALSE for biopharma stages, Commercial=TRUE for OTC retail. |
| CMP-030 | Haleon plc | FDA Review | True | False | Haleon is consumer OTC company. Set FALSE for biopharma stages, Commercial=TRUE for OTC retail. |
| CMP-032 | Sun Pharmaceutical Industries | Discovery | True | False | Sun Pharma specialty/generic dev involves preclinical comparability, bioequivalence clinicals, FDA filings, and commercial sales. |
| CMP-042 | Viatris Inc. | Discovery | True | False | Viatris biosimilar/generic dev involves preclinical comparability, bioequivalence clinicals, FDA filings, and commercial sales. |

---

## 4. Key Case Clarifications

### Lonza (CMP-035) Clarification:
Lonza is a CDMO and not a therapeutic discovery-to-candidate originator, which makes **Discovery = FALSE** and classifies it as a **Non-full-cycle** company. However, under the revised CDMO/infrastructure rule, it remains an active, enabling lifecycle participant across the remaining stages: **Preclinical = TRUE**, **Clinical Trials = TRUE**, **FDA Review = TRUE**, and **Commercial = TRUE**. There are 0 net cell changes for Lonza from the baseline data.

### Summit Therapeutics (CMP-044) Clarification:
Summit Therapeutics has owned clinical candidates (e.g. Ivonescimab) and commercial/regulatory operations in its pipeline, and regularly originates/licenses assets, and remains classified as a **Full-cycle company** (Discovery, Preclinical, Clinical Trials, FDA Review, and Commercial all TRUE) and is excluded from the non-full-cycle listings.

### Non-Full-Cycle Company List After Correction (13 companies):
- CMP-022 (Zoetis Inc.)
- CMP-030 (Haleon plc)
- CMP-032 (Sun Pharmaceutical Industries)
- CMP-035 (Lonza)
- CMP-036 (LabCorp)
- CMP-037 (BioNTech)
- CMP-038 (Abbott Laboratories)
- CMP-039 (CVS Health Corporation)
- CMP-042 (Viatris Inc.)
- CMP-043 (Royalty Pharma plc)
- CMP-046 (Revolution Medicines)
- CMP-047 (Danaher)
- CMP-049 (Elanco Animal Health Incorporated)
