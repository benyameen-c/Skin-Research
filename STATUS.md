# Status

Last updated: 2026-11-27, post-batch corrections (PRs 1 and 2 merged into main).

## Open module

**1-hypopigmentation.** Modules 2 to 4 are closed until Module 1 passes Gate B.

## Done

- Evidence ledger: 31 rows, 13 studies (9 extracted, 4 leads); 7 studies carry verbatim quotes in `data/evidence_quotes.jsonl` (216 quote lines). `tools/ledger.py check` reports 0 `lasting_color_match` rows. It reports the longest months after final treatment on IGH rows as 1.0; the IGH rows at that value are deepadarshan2023 (quoted: "followed up for a duration of 1 month") and arbache2023 (no verbatim quotes, BLOCKED record, old abstract rows). rerknimitr2015's old unquoted rows also still read 0.9. Extracted studies still without verbatim quotes: arbache2023, rerknimitr2015 (both BLOCKED). The earlier 4-month figure is not supported by any quoted row.
- Update search: three dated PubMed queries, one ClinicalTrials.gov query (see `data/search_log.csv`).
- Dataset audit and three-path comparison (`data/datasets.csv`, `data/paths.csv`).
- Experiments: alignment simulation with pixel-model check; clustering sensitivity; denominator audit.
- Static site builds from `content/` and `data/`. Not rebuilt since session 1. `content/home.md` durability line corrected 2026-11-27 to the ledger check (1 month, deepadarshan2023, quoted); `dist/` still shows the old four-month line until a rebuild (Gate B). The home page lede still says colour returns "within four months"; that sentence has no ledger quote and needs Ben's review.
- Batch 2 (2026-11-27): six records merged with `tools/ledger.py merge`, each replacing the study's old rows whole: rerknimitr2013 2 -> 2 rows, deoson2025 2 -> 2, deepadarshan2023 2 -> 4, elhoshy2025 2 -> 10, suvanprakorn1985 1 -> 1, gordon2017 1 -> 1. Ledger 21 -> 31 rows. arbache2023 and rerknimitr2015 BLOCKED, not merged (see Blocked). `verification_status` fixed 2026-11-27: `tools/ledger.py merge` now writes `PASS (verifier <date>; <access>)` from the record's verifier block (tests in `tests/test_ledger.py`). The 7 PASS records were re-merged; only that column changed. deoson2025 and deepadarshan2023 read "date not recorded" because their verifier notes carry no date.
- Data-repository search (2026-11-27): GEO, BioImage Archive, Zenodo, Figshare, eight logged query lines. No public raw IGH tissue, omics or image dataset found.
- Batch 1 (2026-11-27): laosakul2017 merged (verifier PASS on second check; 2 old abstract rows replaced by 3 quoted rows). nct01956435 not merged, BLOCKED (see Blocked).

## To close Module 1

- [ ] Re-extract the remaining extracted studies as staging records with verbatim quotes. After batch 2, `tools/ledger.py check` lists 2: arbache2023 and rerknimitr2015, both BLOCKED after two verifier FAILs (Ben decides on a further attempt or supplies PDFs).
- [ ] Read the full text of laosakul2017 and resolve the 82.3% denominator and the patient count. Abstract-based record merged 2026-11-27 (ABSTRACT_ONLY). Full text still needs a PDF from Ben (paywall list). Note: the merged rows' `verification_status` cell still reads `PENDING (abstract only)` although the record's verifier status is PASS; the record was merged unedited.
- [ ] Extract the registry-posted results of NCT01956435. BLOCKED 2026-11-27 after two verifier FAILs; not merged. Record `data/staging/nct01956435.json` carries the second FAIL and its notes. Ben decides whether a third extraction is allowed. Same cohort as gordon2017: reconcile before any future merge.
- [ ] Extract or exclude the 4 leads: chitvanich2016, arbache2018, wambier2018, rajegowda2021 (check for duplicate cohort).
- [ ] Search Web of Science and Scopus if access exists.
- [x] Search GEO, BioImage Archive, Zenodo, Figshare (2026-11-27, two quoted queries each, APIs): 0 IGH datasets or image deposits. 4 repository hits plus 2 BioStudies literature records, all excluded. Awaiting Gate A review of `data/screening_log.csv`.
- [x] First real run of `tools/pubmed.py` (2026-11-27, cloud thread): tool works unchanged. Four queries, 17/20/4/96 hits, 100 unique PMIDs, 80 newly screened (see `data/search_log.csv`, `data/screening_log.csv`). Abstracts in `papers/excerpts/pmid_*.txt` and copied to the project files folder.
- [ ] **Gate A, waiting for Ben:** review 14 newly included IGH treatment records from the PubMed run (PMIDs 10429990, 10594616, 15187317, 20232585, 2229495, 22646755, 23656568, 24616848, 29547020, 31396960, 32360719, 34084020, 34409340, 34409366) and 9 leads before any extraction. Six of the 14 are letters or reports with no abstract (full text needed).

## Paywall list (Ben: drop PDFs into `papers/pdfs/`, named `<study_id>.pdf`)

| study_id | Reference | Why it matters |
|---|---|---|
| review2025 | Aravindakshan et al., Clin Exp Dermatol 2025, doi:10.1093/ced/llaf134 | list of the 20 included studies, for citation tracking |
| laosakul2017 | J Dermatolog Treat 2017, doi:10.1080/09546634.2016.1221498 (PubMed links a free icon, but Europe PMC says subscription required; not in PMC; tandfonline.com returned HTTP 403 to /doi/full/ and /doi/pdf/ on 2026-11-27) | denominators; patient count; whether any assessment after the single session is timed from that session |
| arbache2023 | Dermatol Surg 2023, doi:10.1097/DSS.0000000000003793 (Europe PMC: subscription required; journals.lww.com and doi.org HTTP 403, 2026-11-27) | sessions, assessor, any later visit; confirms whether 30 days is from the final session |
| rerknimitr2015 | J Eur Acad Dermatol Venereol 2015, doi:10.1111/jdv.12763 (Wiley /doi/full and /doi/pdf HTTP 403; Europe PMC: subscription required, 2026-11-27) | counts behind 83.34% and 18.34% |
| rerknimitr2013 | J Eur Acad Dermatol Venereol 2013, doi:10.1111/j.1468-3083.2012.04462.x (Europe PMC: subscription required; Wiley /doi/full and /doi/pdf HTTP 403, 2026-11-27) | the 11% denominator |
| gordon2017 | Dermatol Surg 2017, doi:10.1097/DSS.0000000000000996 | numbers absent from abstract; 2026-11-27 Europe PMC 'Subscription required', https://doi.org/10.1097/DSS.0000000000000996 -> journals.lww.com HTTP 403 |
| wambier2018 | J Am Acad Dermatol 2018 Apr, 5-FU tattooing letter | no abstract |
| elhoshy2025 | Dermatol Surg 2025, doi:10.1097/DSS.0000000000004447 (Europe PMC: subscription required; journals.lww.com returned HTTP 403; not in PMC) | lesion counts, unit of the medians, between-arm statistics, adverse events |
| suvanprakorn1985 | J Am Acad Dermatol 1985, doi:10.1016/s0190-9622(85)70247-2 (Europe PMC: subscription required, not in PMC) | patient and lesion counts, IGH-specific result, follow-up after grafting |
| shin2013 | J Eur Acad Dermatol Venereol 2013;27(2):e243-6, doi:10.1111/j.1468-3083.2012.04597.x (Europe PMC 2026-11-27: subscription required, not in PMC; https://onlinelibrary.wiley.com/doi/full/10.1111/j.1468-3083.2012.04597.x and /doi/pdf/ HTTP 403) | grading scale, lesion counts, laser settings, sites, any visit later than 2 months |
| kim2023 | J Eur Acad Dermatol Venereol 2023, PMID 36394380 | no abstract; senescence claim rests on title |

## Human gates

- **Gate A (after any search):** Ben reviews the screening list and supplies PDFs before extraction starts.
- **Gate B (before anything is public):** Ben reviews the ledger diff, sets the contact route in `site.json`, approves launch and any email.

## Blocked

| unit | status | tried |
|---|---|---|
| laosakul2017 full text | BLOCKED (abstract extracted and merged instead) | https://www.tandfonline.com/doi/full/10.1080/09546634.2016.1221498 and /doi/pdf/ (HTTP 403, 2026-11-27); Europe PMC: subscription required |
| nct01956435 record | BLOCKED: verifier FAIL twice (2026-11-27) | Second check failed 3 cells: months_after_final_tx in rows 1 and 3 should be NOT_DERIVABLE (gap after the last treatment never stated); row 2 patient_noticeability should read `not reported`, not `not measured`. Full notes in the record's `verifier.notes`. |
| arbache2023 record | BLOCKED: verifier FAIL twice (2026-11-27) | Second check failed 2 cells, both `uncertainty`: author-sponsor link ('Clinica Dermatologica Arbache ltda') and registry 'PARALLEL' vs abstract 'split-body' not recorded. Not merged; the old unquoted abstract rows stay in the ledger. Needs a fresh extraction or Ben's PDF. Record `data/staging/arbache2023.json` carries the second FAIL. |
| rerknimitr2015 record | BLOCKED: verifier FAIL twice (2026-11-27) | First check 7 cells; second check 1 cell: row 1 `uncertainty` omits the '120 lesions ... were treated' denominator conflict. Not merged; the old unquoted abstract rows stay in the ledger. Needs full text (paywall list) or Ben's decision. Record `data/staging/rerknimitr2015.json` carries the second FAIL (from the second verifier's saved record; its commit could not be pushed). |

## Verification log

- 2026-11-27, nct01956435 (staging record from claude/project-thread-1wkpky): verifier **FAIL, attempt 1 of 2**, 4 cells (row 2 control arm: treatment_class, time_from_last_treatment, months_after_final_tx; row 3: comparator). Details in the record's `verifier.notes`. Needs a re-extraction pass, then a fresh verifier. Not merged.
- 2026-11-27, nct01956435: re-extracted after FAIL 1. Control row now treatment_class `control`, time from last treatment `not applicable`, months `NOT_APPLICABLE`; self-report row comparator `none`. Also added quotes for evaluable and attrition counts, Fitzpatrick limitation in skin_tone. Validator ok, verifier PENDING. A second FAIL makes it BLOCKED.
- 2026-11-27, nct01956435: verifier **FAIL, attempt 2 of 2**, 3 cells. BLOCKED, not merged.
- 2026-11-27, laosakul2017: verifier FAIL (5 cells), corrected, verifier PASS on second check. Merged with `tools/ledger.py merge`: the 2 abstract rows were replaced whole by the record's 3 rows and 9 quotes.

## Verification log (batch 2, 2026-11-27)

- rerknimitr2013: verifier PASS. Merged.
- deoson2025 (FULL_TEXT): verifier PASS, 0 failed cells. Merged.
- deepadarshan2023 (FULL_TEXT): verifier 1 FAIL (4 cells), corrected, verifier 2 PASS. Merged. Open issue: the paper's follow-up length conflicts (Methods 1 month after treatment vs Results "4-month follow-up", likely counted from baseline); week 16 recorded as 1 month after final treatment per Methods.
- elhoshy2025 (ABSTRACT_ONLY, diagnosis ADJACENT, not IGH): verifier 1 FAIL (16 cells), corrected, verifier 2 PASS. Merged.
- suvanprakorn1985: verifier 1 FAIL (1 cell), corrected, verifier 2 PASS. Merged.
- gordon2017: verifier 1 FAIL (1 cell), corrected, verifier 2 PASS. Merged. Same cohort as NCT01956435 (BLOCKED); reconcile before any merge of that record.
- arbache2023: FAIL twice. BLOCKED.
- rerknimitr2015: FAIL twice. BLOCKED.

## Batch 3 extraction log

- 2026-11-27, shin2013 (PMID 22646755, fractional CO2 laser, single session): extractor wrote `data/staging/shin2013.json`, ABSTRACT_ONLY, 1 row, validator ok, verifier PENDING. Full text on the paywall list.
- 2026-11-27, shin2013: verifier **FAIL, attempt 1 of 2**, 2 cells (row 1 patient_noticeability uses "not reported" in an abstract-only record; row 1 uncertainty omits that erythema and hyperpigmentation were still present at the 2-month assessment). Details in the record's `verifier.notes`. Needs a correction pass, then a fresh verifier. Not merged.

## Next session

Close Module 1 (list above). Then extend the simulation: lighting and white-balance drift, brown spot on mottled background, 2 to 8 mm, tests written before the code.
