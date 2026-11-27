# Status

Last updated: 2026-11-27, session 2 (batch 1 merge); chitvanich2016 staged (batch 3).

## Open module

**1-hypopigmentation.** Modules 2 to 4 are closed until Module 1 passes Gate B.

## Done

- Evidence ledger: 21 rows, 13 studies (9 extracted, 4 leads); 1 study (laosakul2017) carries verbatim quotes in `data/evidence_quotes.jsonl`. No row measures a lasting colour match. **Longest interval after a final treatment needs recomputing.** The earlier 4-month figure came from laosakul2017, whose merged rows now read `NOT_DERIVABLE`. `tools/ledger.py check` now reports its maximum from arbache2023 rows, which have no verbatim quotes yet, so no quoted figure supports any longest interval at present.
- Update search: three dated PubMed queries, one ClinicalTrials.gov query (see `data/search_log.csv`).
- Dataset audit and three-path comparison (`data/datasets.csv`, `data/paths.csv`).
- Experiments: alignment simulation with pixel-model check; clustering sensitivity; denominator audit.
- Static site builds from `content/` and `data/`. Not rebuilt after batch 1. `content/home.md` still states the four-month gap, which the ledger no longer supports; it needs rewording before any rebuild (Gate B).
- Batch 1 (2026-11-27): laosakul2017 merged (verifier PASS on second check; 2 old abstract rows replaced by 3 quoted rows). nct01956435 not merged, BLOCKED (see Blocked).

## To close Module 1

- [ ] Re-extract the 8 remaining extracted studies as staging records with verbatim quotes (`tools/ledger.py check` lists them).
- [ ] Read the full text of laosakul2017 and resolve the 82.3% denominator and the patient count. Abstract-based record merged 2026-11-27 (ABSTRACT_ONLY). Full text still needs a PDF from Ben (paywall list). Note: the merged rows' `verification_status` cell still reads `PENDING (abstract only)` although the record's verifier status is PASS; the record was merged unedited.
- [ ] Extract the registry-posted results of NCT01956435. BLOCKED 2026-11-27 after two verifier FAILs; not merged. Record `data/staging/nct01956435.json` carries the second FAIL and its notes. Ben decides whether a third extraction is allowed. Same cohort as gordon2017: reconcile before any future merge.
- [ ] Extract or exclude the 4 leads: chitvanich2016, arbache2018, wambier2018, rajegowda2021 (check for duplicate cohort).
  - chitvanich2016: staged 2026-11-27 as `data/staging/chitvanich2016.json` (ABSTRACT_ONLY, 3 rows, validator ok, verifier PASS 2026-11-27, not yet merged). Possible shared cohort with rerknimitr2015 (same authors, laser, schedule, lesion layout); abstract's 120-lesion count is ambiguous.
- [ ] Search Web of Science and Scopus if access exists; search GEO, BioImage Archive, Zenodo, Figshare.
- [ ] First real run of `tools/pubmed.py` (never executed).

## Paywall list (Ben: drop PDFs into `papers/pdfs/`, named `<study_id>.pdf`)

| study_id | Reference | Why it matters |
|---|---|---|
| review2025 | Aravindakshan et al., Clin Exp Dermatol 2025, doi:10.1093/ced/llaf134 | list of the 20 included studies, for citation tracking |
| laosakul2017 | J Dermatolog Treat 2017, doi:10.1080/09546634.2016.1221498 (PubMed links a free icon, but Europe PMC says subscription required; not in PMC; tandfonline.com returned HTTP 403 to /doi/full/ and /doi/pdf/ on 2026-11-27) | denominators; patient count; whether any assessment after the single session is timed from that session |
| arbache2023 | Dermatol Surg 2023, doi:10.1097/DSS.0000000000003793 | sessions, assessor, any later visit |
| rerknimitr2015 | J Eur Acad Dermatol Venereol 2015, doi:10.1111/jdv.12763 | counts behind 83.34% and 18.34% |
| rerknimitr2013 | J Eur Acad Dermatol Venereol 2013, doi:10.1111/j.1468-3083.2012.04462.x | the 11% denominator |
| gordon2017 | Dermatol Surg 2017, doi:10.1097/DSS.0000000000000996 | numbers absent from abstract |
| wambier2018 | J Am Acad Dermatol 2018 Apr, 5-FU tattooing letter | no abstract |
| chitvanich2016 | J Dermatolog Treat 2016;27(5):456-60, doi:10.3109/09546634.2015.1133883 (Europe PMC: subscription required, not in PMC; tandfonline.com /doi/full/ and /doi/pdf/ returned HTTP 403 on 2026-11-27) | patient count, whether 120 lesions includes controls, control-side result, final-visit timing, cohort overlap with rerknimitr2015 |
| kim2023 | J Eur Acad Dermatol Venereol 2023, PMID 36394380 | no abstract; senescence claim rests on title |

## Human gates

- **Gate A (after any search):** Ben reviews the screening list and supplies PDFs before extraction starts.
- **Gate B (before anything is public):** Ben reviews the ledger diff, sets the contact route in `site.json`, approves launch and any email.

## Blocked

| unit | status | tried |
|---|---|---|
| laosakul2017 full text | BLOCKED (abstract extracted and merged instead) | https://www.tandfonline.com/doi/full/10.1080/09546634.2016.1221498 and /doi/pdf/ (HTTP 403, 2026-11-27); Europe PMC: subscription required |
| nct01956435 record | BLOCKED: verifier FAIL twice (2026-11-27) | Second check failed 3 cells: months_after_final_tx in rows 1 and 3 should be NOT_DERIVABLE (gap after the last treatment never stated); row 2 patient_noticeability should read `not reported`, not `not measured`. Full notes in the record's `verifier.notes`. |

## Verification log

- 2026-11-27, nct01956435 (staging record from claude/project-thread-1wkpky): verifier **FAIL, attempt 1 of 2**, 4 cells (row 2 control arm: treatment_class, time_from_last_treatment, months_after_final_tx; row 3: comparator). Details in the record's `verifier.notes`. Needs a re-extraction pass, then a fresh verifier. Not merged.
- 2026-11-27, nct01956435: re-extracted after FAIL 1. Control row now treatment_class `control`, time from last treatment `not applicable`, months `NOT_APPLICABLE`; self-report row comparator `none`. Also added quotes for evaluable and attrition counts, Fitzpatrick limitation in skin_tone. Validator ok, verifier PENDING. A second FAIL makes it BLOCKED.
- 2026-11-27, nct01956435: verifier **FAIL, attempt 2 of 2**, 3 cells. BLOCKED, not merged.
- 2026-11-27, laosakul2017: verifier FAIL (5 cells), corrected, verifier PASS on second check. Merged with `tools/ledger.py merge`: the 2 abstract rows were replaced whole by the record's 3 rows and 9 quotes.

- 2026-11-27, chitvanich2016 (staging record from claude/project-thread-m788xq): verifier **PASS** on first check, 0 failed cells. Ready for `tools/ledger.py merge` by the collector. Cohort overlap with rerknimitr2015 still to reconcile.

## Next session

Close Module 1 (list above). Then extend the simulation: lighting and white-balance drift, brown spot on mottled background, 2 to 8 mm, tests written before the code.
