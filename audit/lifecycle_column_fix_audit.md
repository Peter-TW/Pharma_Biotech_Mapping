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

## 1.1 Lifecycle Edge-Case Rules Added After Review

The following edge-case rules were added after a second-pass review of partnered-asset and branded-generic companies (CMP-037 BioNTech, CMP-038 Abbott Laboratories). They apply on top of the rules in Section 1 and resolve cases the core rules did not cover explicitly.

### Rule 1 — Partnered / co-commercialized approved assets
> If a company originates or co-develops an approved therapeutic product and shares regulatory responsibility, product revenue, profit share, or commercialization economics, FDA Review and Commercial are TRUE even if another partner leads field distribution.

### Rule 2 — Branded generics / biosimilars / complex generics
> Branded-generics, biosimilar, and complex-generic companies are not automatically Discovery-stage companies. However, Preclinical, Clinical Trials, FDA Review, and Commercial may be TRUE when the company performs formulation, comparability, bioequivalence, CMC, clinical/regulatory, or commercialization work for therapeutic products.

### Rule 3 — FDA Review means global regulatory review
> The FDA Review column is used as shorthand for major regulatory review / approval / registration. It includes FDA, EMA, PMDA, MHRA, NMPA, CDSCO, and other material national or regional health authorities. It should not be interpreted as U.S. FDA-only.

---

## 2. Before vs. After Summary Stats

| Metric / Stage | Before Baseline Count | Corrected After Count | Net Change |
|---|---|---|---|
| **Total Companies** | 50 | 50 | 0 |
| **Discovery = TRUE** | 44 | 39 | -5 |
| **Preclinical = TRUE** | 45 | 45 | 0 |
| **Clinical Trials = TRUE** | 46 | 45 | -1 |
| **FDA Review = TRUE** | 45 | 42 | -3 |
| **Commercial = TRUE** | 47 | 45 | -2 |
| **Full-cycle profile (all 5 TRUE)** | 41 | 38 | -3 |
| **Non-full-cycle profile** | 9 | 12 | +3 |
| **Non-pharma / infrastructure / other** | 0 | 4 | +4 |

- **Unique_ID Integrity:** Handled as strictly unique with zero blank values across exactly 50 rows.
- **Lifecycle Column Values:** Coerced to contain only case-insensitive `"TRUE"` or `"FALSE"` values in the raw CSV.
- **Total lifecycle cell changes after this correction (from baseline):** **25 cell changes** (affecting 10 companies).

---

## 3. Complete Change Log Table (From Baseline)

The following table documents the 25 cell modifications applied to the baseline master sheet to arrive at the corrected state:

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
| CMP-037 | BioNTech | FDA Review | False | True | Rule 1 (partnered approved assets): BioNTech is Marketing Authorization Holder for COMIRNATY (FDA-approved BLA, Aug 2021) and co-sponsors regulatory filings with Pfizer. |
| CMP-037 | BioNTech | Commercial | False | True | Rule 1 (partnered approved assets): COMIRNATY is commercialized with shared revenue economics; BioNTech holds the marketing authorization in US/EU/UK and other countries. |
| CMP-038 | Abbott Laboratories | Preclinical | False | True | Rule 2 (branded generics / biosimilars): Abbott's Established Pharmaceuticals Division (EPD) performs formulation, comparability, and CMC work for branded-generic and biosimilar products in emerging markets. |
| CMP-038 | Abbott Laboratories | Clinical Trials | False | True | Rule 2 (branded generics / biosimilars): EPD runs bioequivalence and biosimilar clinical work to support emerging-market registrations (Rule 3 confirms non-US filings count). |

---

## 4. Key Case Clarifications

### Lonza (CMP-035) Clarification:
Lonza is a CDMO and not a therapeutic discovery-to-candidate originator, which makes **Discovery = FALSE** and classifies it as a **Non-full-cycle** company. However, under the revised CDMO/infrastructure rule, it remains an active, enabling lifecycle participant across the remaining stages: **Preclinical = TRUE**, **Clinical Trials = TRUE**, **FDA Review = TRUE**, and **Commercial = TRUE**. There are 0 net cell changes for Lonza from the baseline data.

### Summit Therapeutics (CMP-044) Clarification:
Summit Therapeutics has owned clinical candidates (e.g. Ivonescimab) and commercial/regulatory operations in its pipeline, and regularly originates/licenses assets, and remains classified as a **Full-cycle company** (Discovery, Preclinical, Clinical Trials, FDA Review, and Commercial all TRUE) and is excluded from the non-full-cycle listings.

### BioNTech (CMP-037) Clarification:
BioNTech is the Marketing Authorization Holder for COMIRNATY in the U.S., EU, U.K., and other countries; COMIRNATY received full U.S. FDA approval in August 2021. The vaccine was co-developed with Pfizer, and BioNTech shares the global commercialization economics. Under Section 1.1 Rule 1 (partnered / co-commercialized approved assets), this makes **FDA Review = TRUE** and **Commercial = TRUE** despite Pfizer leading field distribution in many regions. BioNTech is therefore reclassified as a **Full-cycle company** (Discovery, Preclinical, Clinical Trials, FDA Review, and Commercial all TRUE) and is excluded from the non-full-cycle listings.

### Abbott Laboratories (CMP-038) Clarification:
Abbott's Established Pharmaceuticals Division (EPD) commercializes a branded-generics portfolio in emerging markets (India, Brazil, Russia, Southeast Asia) and is actively expanding into biosimilars. Under Section 1.1 Rule 2 (branded generics / biosimilars) and Rule 3 (global regulatory review), this development and registration activity makes **Preclinical = TRUE**, **Clinical Trials = TRUE**, **FDA Review = TRUE**, and **Commercial = TRUE**. Abbott does not perform novel target discovery — the proprietary pipeline transferred to AbbVie in the 2013 spinoff — so **Discovery = FALSE** and Abbott remains a **Non-full-cycle** company.

### Non-Full-Cycle Company List After Correction (12 companies):
- CMP-022 (Zoetis Inc.)
- CMP-030 (Haleon plc)
- CMP-032 (Sun Pharmaceutical Industries)
- CMP-035 (Lonza)
- CMP-036 (LabCorp)
- CMP-038 (Abbott Laboratories)
- CMP-039 (CVS Health Corporation)
- CMP-042 (Viatris Inc.)
- CMP-043 (Royalty Pharma plc)
- CMP-046 (Revolution Medicines)
- CMP-047 (Danaher)
- CMP-049 (Elanco Animal Health Incorporated)
