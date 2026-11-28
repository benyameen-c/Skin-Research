# Search: long-term colour match after cell or graft transplantation

Module 5-damage-repair, searcher role, 2026-11-28. **Leads only.** Nothing here is evidence until Ben opens Gate A for a paper and it passes extractor, validator and verifier. No data were extracted. Quotes are copied verbatim from the saved PubMed abstracts (`papers/excerpts/pmid_<id>.txt`, also in the project files excerpts folder) and were string-checked against them.

## Question screened for

Human studies of melanocyte or epidermal cell transplantation (cultured or non-cultured cell suspension, mini-punch, suction blister, thin or ultrathin grafts, hair-follicle units) for stable hypo- or depigmentation (vitiligo, piebaldism, post-burn or post-traumatic leukoderma, IGH), where the abstract names colour match of the repigmented skin as an outcome **and** states follow-up of six months or longer.

Caveat that matters for our core question: every follow-up below is counted from the procedure, and several studies add phototherapy after it. None of these abstracts says follow-up is counted from the final treatment, so none can yet answer the six-month-after-final-treatment test. Every colour match below is judged by eye or by patient questionnaire except Wang 2021, which uses a melanin index against adjacent skin.

## Queries (PubMed E-utilities via `tools/pubmed.py`, logged in `data/search_log.csv`)

| # | Query (abbreviated; exact text in the log) | Hits |
|---|---|---|
| Q1 | cell transplant / suspension / ReCell terms AND condition terms AND colour-match terms | 32 |
| Q2 | graft terms (suction blister, punch, minigraft, split-thickness, epidermal graft) AND condition AND colour match | 19 |
| Q3 | (transplant* OR graft*) AND condition AND colour match AND follow-up terms | 35 |
| Q4 | autologous skin cell suspension / spray-on skin / epidermal cell suspension AND repigmentation or condition terms (no colour-match filter) | 87 |

122 unique records. Decisions in `data/screening_log.csv` (found_by `pubmed_transplant_cm_q1` to `_q4`): **19 leads**, **20 not screened in full**, **1 review kept for citation tracking**, **82 excluded** (most common reasons: colour match not in abstract; follow-up under six months, typically 12 to 24 weeks).

Not run: Europe PMC full-text search, ClinicalTrials.gov, Embase. Colour match is often reported only in full text, so this abstract search undercounts.

## Overlap with work already done

No PMID returned by these queries is in the ledger, the frontier scan or the checked Gemini repair report. Related items already covered elsewhere, not repeated here: mulekar2007 (PMID 17927795, ledger), hirobe2018 (ledger, IGH mini-grafts), lin2024 (ledger), Mulekar 2005 (PMID 16207186, Gemini report check, 142 patients up to 6 years; its abstract does not name colour match, so these queries did not return it), RECELL pivotal trial PMIDs 39182674 and 40158537 and the economic model 40042162 (colour-match trials check, PR 21).

## Leads (19)

All are ABSTRACT_ONLY in this project. "Open copy" means Europe PMC reports a PMC full text, which was not fetched. Items without one are not in PMC and are added to the paywall list in `STATUS.md`; no publisher site was tried.

| PMID | Study | Condition | Method | Open copy | Why it matches (abstract, verbatim) |
|---|---|---|---|---|---|
| 39679850 | Hoang Van 2025, J Cosmet Dermatol | vitiligo | NCES plus excimer lamp | PMC11845954 | "Both groups demonstrated a similar rate of good color match" / "All patients were followed up 18 months after the procedure." |
| 37317740 | Savant 2023, Indian J Dermatol Venereol Leprol | vitiligo, 192 patients, 410 lesions | ultrathin skin graft after CO2 ablation, plus excimer | none (not in PMC) | "394 (96.1%) lesions had achieved excellent colour match, and 16 lesions (3.9%) had poor or no colour match at 1-year follow-up." |
| 26288405 | Ashique 2015, Indian J Dermatol | vitiligo, 30 patients | suction blister epidermal grafting | PMC4533535 | "The face and lips showed an excellent result and color match and persistent pigment retention." / "a variable follow-up period ranging from 2 to 62 months" |
| 26247842 | Bao 2015, J Dermatolog Treat | vitiligo | blister roof graft vs cultured melanocytes vs NCES | none (not in PMC) | "The results were evaluated 12-month post-surgery for the extent of repigmentation and color match." |
| 25851083 | Vyas 2015, J Cutan Med Surg | mechanical or chemical leukodermic scars, 10 patients | MKTP (NCES) | none (not in PMC) | "followed for at least 6 months, with monitoring of repigmentation and colour matching." / "Nine patients attended at least 6 months of follow-up." |
| 20804490 | van Geel 2010, Br J Dermatol | vitiligo, halo naevi, piebaldism, naevus depigmentosus | NCES | none (not in PMC) | "a perfect colour match was seldom obtained." / "Long-term results were evaluated by 54 patients using a questionnaire up to 7·7 years after treatment (mean 4 years)." |
| 11074702 | Guerra 2000, Arch Dermatol | stable vitiligo | cultured epidermal autografts | none (not in PMC) | "Color matching was good and scar formation was not observed." / "evaluated after 12 to 36 months of follow-up" |
| 38681944 | Ali 2023, Ann Burns Fire Disasters | post-burn leucoderma, 20 patients | suction blister epidermal grafting | PMC11042015 | "After a mean follow up period of 8.5±1.73 months, repigmentation percentage ranged from 40 to 100% with good color matching." |
| 33326964 | Wang 2021, Dermatology | head and neck vitiligo, 10 patients | pixel array epidermal grafting plus phototherapy | none (not in PMC) | "The color matching index of repigmentation was evaluated by measuring the melanin index in the grafted area and the juxta non-vitiliginous area." / "The patients were evaluated 1, 3, and 6 months post grafting" |
| 22390674 | Lu 2014, J Dermatolog Treat | vitiligo, 282 patients | autologous epidermal sheet transplants | none (not in PMC) | "We investigated the long-term percentage of repigmentation and colour matching up to 13 years after treatment (mean 1.87 years)." |
| 18093203 | Babu 2008, Dermatol Surg | lip vitiligo | punch grafting vs suction blister grafting | none (not in PMC) | "PSG gives a better color match than SBEG." / "The results were evaluated after a follow-up period of 6 months." |
| 11455144 | Gupta 2001, Dermatology | depigmentation after discoid lupus | epidermal (blister) grafting | none (not in PMC) | "The color match was good." / "during the follow-up of 6 months to 1 year." |
| 7728478 | Agrawal 1995, Dermatol Surg | vitiligo | dermabrasion plus thin split-thickness graft | none (not in PMC) | "The patients have been followed up for 1-6 years." / "resulting in an excellent color match on a long-term follow-up." |
| 24470722 | Sacchidanand 2013, J Cutan Aesthet Surg | vitiligo, 1 case | follicular unit extraction | PMC3884890 | "No recurrence was noted at the end of 6 months follow-up with excellent colour match." |
| 21572681 | Kumaresan 2011, J Cutan Aesthet Surg | vitiligo, 1 case | single-hair follicular unit transplant | PMC3081484 | "No recurrence was noted at the end of 6-month follow-up with excellent colour match." |
| 21507039 | Sahni 2011, Clin Exp Dermatol | vitiligo, children, 19 lesions | NCES | none (not in PMC) | "The colour match at the final visit was excellent for 16 of the 19 lesions (84.2%)." / "Patients were followed up for at least 1 year." |
| 12621204 | Acikel 2003, Plast Reconstr Surg | vitiligo, 7 patients | CO2 laser resurfacing plus thin skin graft | none (not in PMC) | "The follow-up period for these patients ranged from 6 to 18 months" / "the color match was good or excellent in all patients." |
| 8909758 | Kahn 1996, Burns | post-burn depigmentation | dermabrasion plus epithelial sheet grafts | none (not in PMC) | "The colour match has been good or excellent in all but one patient." / "The follow-up period for these patients has ranged from 2 weeks to 94 months with an average of 17 months." |
| 1752883 | Kahn 1991, J Burn Care Rehabil | post-burn depigmentation | dermabrasion plus epithelial grafts | none (not in PMC) | "The color match ranges from good to excellent." / "The follow-up period for these patients has ranged from 0.5 months to 94 months, with an average of 14 months." |

Pointers for whoever opens Gate A, not conclusions:

- Longest colour-match follow-up named in an abstract: Lu 2014 (up to 13 years, mean 1.87), van Geel 2010 (questionnaire up to 7.7 years, mean 4), Agrawal 1995 (1 to 6 years). van Geel 2010 is the only abstract that names stability, sun reaction and colour match together, and it says "a perfect colour match was seldom obtained."
- Wang 2021 is the only one that measures colour match with an instrument (melanin index, grafted vs adjacent skin), which bears directly on the project's measurement plan.
- Post-burn and post-traumatic leukoderma (Vyas 2015, Ali 2023, Kahn 1991 and 1996) are the closest non-vitiligo analogues to IGH, [our inference, not from these abstracts: no autoimmune attack on the graft is expected there].

## Not screened in full (20)

Colour match is named but follow-up length is not in the abstract, the record has no abstract, or (burn-scar and long-follow-up items) pigment or follow-up is long but colour match against surrounding skin is not named. Full text needed to decide.

| PMID | Reason |
|---|---|
| 39937279 | follicular plus epidermal cell suspension, vitiligo; colour match mentioned in general terms; follow-up length not in abstract |
| 38742750 | trypsinized vs plasma-gel epidermal grafts, vitiligo; colour matching compared; follow-up length not in abstract |
| 36331844 | epidermal harvesting vs NCES, vitiligo; colour match observation; follow-up length not in abstract |
| 31997482 | NCES from blister roofs vs epidermal cuts, vitiligo; colour match compared; follow-up length not in abstract |
| 21122997 | MKTP for post-burn leucoderma; colour matching reported; follow-up length not in abstract |
| 20021980 | ReCell in stable vitiligo; colour match graded; follow-up length not in abstract |
| 9537012 | ultra-thin grafts, vitiligo; final colour match named; follow-up length not in abstract |
| 39483660 | Jodhpur technique with blister membrane, vitiligo; colour match reported; follow-up length not in abstract |
| 21572680 | split-thickness grafting, vitiligo; colour match named; follow-up length not in abstract |
| 9892949 | split-skin plus minigrafting, piebaldism; colour match named; follow-up length not in abstract |
| 30280485 | MKTP at two donor ratios, vitiligo; colour matching assessed; NB-UVB for 6 months but follow-up length not in abstract |
| 7673499 | epithelial sheet grafting, vitiligo; final colour match named; follow-up length not in abstract |
| 42732550 | blister roof grafting vs epidermal cell suspension, vitiligo; no abstract in PubMed |
| 40700783 | ASCS via fractional laser for hypopigmented scar; instrument pigment readout; colour match and follow-up length not clear in abstract |
| 33040441 | NCES to correct colour mismatch in vitiligo; no abstract in PubMed |
| 29103774 | autologous epidermal cell transplant, vitiligo, 30-month follow-up; colour match not named in abstract |
| 28149233 | ReNovaCell for hypopigmented burn scars in children; melanin at 12 months; colour match not named in abstract |
| 27835917 | cell transplantation for depigmented burn scars (German); melanin at 1 year; colour match not named in abstract |
| 27156803 | ReNovaCell cell transplant for hypopigmented burn scars; melanin measured at 12 months; colour match vs surrounding skin not named in abstract |
| 21572677 | basal-cell-enriched suspension, vitiligo, follow-up at least 2 years; colour match not named in abstract |

## Review kept for citation tracking

- PMID 33428279, donor-to-recipient ratios in vitiligo and piebaldism surgery, systematic review (J Eur Acad Dermatol Venereol 2021). Abstract: "Less than half of our included studies stated the colour match between different expansion ratios, and results were variable."
