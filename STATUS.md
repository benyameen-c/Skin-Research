# Status

Last updated: 2026-11-27, end of session 1.

## Open module

**1-hypopigmentation.** Modules 2 to 4 are closed until Module 1 passes Gate B.

## Done

- Evidence ledger: 20 rows, 13 studies (9 extracted, 4 leads). No row measures a lasting colour match. Longest interval after a final treatment: 4 months.
- Update search: three dated PubMed queries, one ClinicalTrials.gov query (see `data/search_log.csv`).
- Dataset audit and three-path comparison (`data/datasets.csv`, `data/paths.csv`).
- Experiments: alignment simulation with pixel-model check; clustering sensitivity; denominator audit.
- Static site builds from `content/` and `data/`.

## To close Module 1

- [ ] Re-extract the 9 extracted studies as staging records with verbatim quotes (`tools/ledger.py check` lists them).
- [ ] Read the free full text of laosakul2017 and resolve the 82.3% denominator and the patient count.
- [ ] Extract the registry-posted results of NCT01956435.
- [ ] Extract or exclude the 4 leads: chitvanich2016, arbache2018, wambier2018, rajegowda2021 (check for duplicate cohort).
- [ ] Search Web of Science and Scopus if access exists; search GEO, BioImage Archive, Zenodo, Figshare.
- [ ] First real run of `tools/pubmed.py` (never executed).

## Paywall list (Ben: drop PDFs into `papers/pdfs/`, named `<study_id>.pdf`)

| study_id | Reference | Why it matters |
|---|---|---|
| review2025 | Aravindakshan et al., Clin Exp Dermatol 2025, doi:10.1093/ced/llaf134 | list of the 20 included studies, for citation tracking |
| laosakul2017 | J Dermatolog Treat 2017, doi:10.1080/09546634.2016.1221498 (PubMed says free) | denominators; longest follow-up found |
| arbache2023 | Dermatol Surg 2023, doi:10.1097/DSS.0000000000003793 | sessions, assessor, any later visit |
| rerknimitr2015 | J Eur Acad Dermatol Venereol 2015, doi:10.1111/jdv.12763 | counts behind 83.34% and 18.34% |
| rerknimitr2013 | J Eur Acad Dermatol Venereol 2013, doi:10.1111/j.1468-3083.2012.04462.x | the 11% denominator |
| gordon2017 | Dermatol Surg 2017, doi:10.1097/DSS.0000000000000996 | numbers absent from abstract |
| wambier2018 | J Am Acad Dermatol 2018 Apr, 5-FU tattooing letter | no abstract |
| kim2023 | J Eur Acad Dermatol Venereol 2023, PMID 36394380 | no abstract; senescence claim rests on title |

## Human gates

- **Gate A (after any search):** Ben reviews the screening list and supplies PDFs before extraction starts.
- **Gate B (before anything is public):** Ben reviews the ledger diff, sets the contact route in `site.json`, approves launch and any email.

## In progress

- rerknimitr2015 (2026-11-27): fresh extraction from the saved PubMed abstract, written from scratch after the earlier record was BLOCKED on batch-2 branches (Ben approved a fresh attempt). `data/staging/rerknimitr2015.json`, ABSTRACT_ONLY, 5 rows (physician grading treated and control; colourimetry weeks 8, [12], 16), validator ok, verifier PENDING. All rows `NOT_DERIVABLE`/`NOT_APPLICABLE` for months after final treatment: the abstract never states the week of the final session. Full text still on the paywall list.
  - Verifier #1 on the fresh record (2026-11-27): FAIL, 3 cells, all `analysis_unit` on the colourimetry rows (3 to 5): the abstract does not say whether colour was analysed per lesion, side or patient. Next: one extractor fix round, then a fresh verifier; a second FAIL means BLOCKED.

## Blocked

Nothing yet.

## Next session

Close Module 1 (list above). Then extend the simulation: lighting and white-balance drift, brown spot on mottled background, 2 to 8 mm, tests written before the code.
