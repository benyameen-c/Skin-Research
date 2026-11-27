# Status

Last updated: 2026-11-27 23:30 UTC, batch 3 merge (PRs 1 to 3 merged into main; batch 3 PR from claude/project-thread-1i49rl); then drift simulation implemented, PR "Drift simulation: tests and implementation".

## Open module

**1-hypopigmentation.** Modules 2 to 4 are closed until Module 1 passes Gate B.

## Done

- Evidence ledger (after batch 3): 54 rows, 21 studies (19 extracted, 2 leads: arbache2018, wambier2018); 574 quote lines in `data/evidence_quotes.jsonl`. `tools/ledger.py check` prints: `rows 54 | studies 21 | blank cells 0`, `longest months after final treatment, IGH rows: 2.0`, `lasting_color_match rows: 0`, `extracted studies still without verbatim quotes (0): none`. The IGH rows at 2.0 are shin2013 (quoted: "Two months after a single treatment, physicians' clinical assessments were performed") and goldust2013 (quoted: "Two months after a single treatment session, 115 patients (47.9%) exhibited more than 75% clinical improvement."), both a single fractional CO2 laser session, both partial repigmentation counted in patients. elhoshy2025 rows read 3.0 but are ADJACENT (not IGH), so check excludes them. pagnoni1999 has one row at 12 months, also ADJACENT (macular hypomelanosis, not IGH): the quoted regression "to the original state" a year after stopping tretinoin, recorded as `unquantified`.
- Batch 3 (2026-11-27, Ben's go-ahead 23:04 UTC): twelve verifier-PASS records merged with `tools/ledger.py merge`, each replacing the study's rows whole. Rows before -> after: arbache2023 2 -> 2 (fresh record, now quoted), rerknimitr2015 2 -> 5 (fresh record, now quoted), chitvanich2016 1 -> 3 (lead row replaced), rajegowda2021 1 -> 2 (lead row replaced), rambhia2020 0 -> 1, kreeshan2021 0 -> 3, shin2013 0 -> 1, koh2018 0 -> 3, ravikiran2014 0 -> 2, goldust2013 0 -> 1, ploysangam1990 0 -> 2, pagnoni1999 0 -> 4. Ledger 31 -> 54 rows, 13 -> 21 studies. Validator ok on all 23 staging records; 6 tests pass.
- Batch 3 held: nct01956435, **verified, held: same cohort as gordon2017, awaiting Ben's decision on how to reconcile.** Third extraction (Ben approved 2026-11-27 23:04 UTC), 3 rows, FULL_TEXT, verifier PASS 0 failed cells (claude/project-thread-82j76h 86c0768). Record committed in `data/staging/nct01956435.json`, not merged.
- Batch 3 excluded: arbache2021 (PMID 34409366), a letter with no IGH patients and no clinical outcome (ex vivo black-ink histology only). Staged and read in full on claude/project-thread-ch99nh f0f2d70; not committed to staging or the ledger. `data/screening_log.csv` line changed to excluded.
- Batch 3 BLOCKED 0-row stubs, committed in `data/staging/` but never to be merged (a 0-row merge deletes a study's rows): arbache2018, eun2020, vedamurthy2022 (see Blocked and paywall list).
- Update search: three dated PubMed queries, one ClinicalTrials.gov query (see `data/search_log.csv`).
- Dataset audit and three-path comparison (`data/datasets.csv`, `data/paths.csv`).
- Experiments: alignment simulation with pixel-model check; clustering sensitivity; denominator audit.
- Static site builds from `content/` and `data/`. Not rebuilt since session 1. `content/home.md` durability line updated in batch 3 to the ledger check (2 months, shin2013 and goldust2013, quoted); `dist/` still shows the old four-month line until a rebuild (Gate B). The home page lede still says colour returns "within four months"; that sentence has no ledger quote and needs Ben's review.
- Batch 2 (2026-11-27): six records merged with `tools/ledger.py merge`, each replacing the study's old rows whole: rerknimitr2013 2 -> 2 rows, deoson2025 2 -> 2, deepadarshan2023 2 -> 4, elhoshy2025 2 -> 10, suvanprakorn1985 1 -> 1, gordon2017 1 -> 1. Ledger 21 -> 31 rows. arbache2023 and rerknimitr2015 BLOCKED, not merged (see Blocked). `verification_status` fixed 2026-11-27: `tools/ledger.py merge` now writes `PASS (verifier <date>; <access>)` from the record's verifier block (tests in `tests/test_ledger.py`). The 7 PASS records were re-merged; only that column changed. deoson2025 and deepadarshan2023 read "date not recorded" because their verifier notes carry no date.
- Data-repository search (2026-11-27): GEO, BioImage Archive, Zenodo, Figshare, eight logged query lines. No public raw IGH tissue, omics or image dataset found.
- Batch 1 (2026-11-27): laosakul2017 merged (verifier PASS on second check; 2 old abstract rows replaced by 3 quoted rows). nct01956435 not merged, BLOCKED (see Blocked).

## To close Module 1

- [x] Re-extract the remaining extracted studies as staging records with verbatim quotes. Done in batch 3: fresh arbache2023 and rerknimitr2015 records passed and were merged; check lists 0 studies without quotes.
- [ ] Read the full text of laosakul2017 and resolve the 82.3% denominator and the patient count. Abstract-based record merged 2026-11-27 (ABSTRACT_ONLY). Full text still needs a PDF from Ben (paywall list). Note: the merged rows' `verification_status` cell still reads `PENDING (abstract only)` although the record's verifier status is PASS; the record was merged unedited.
- [ ] Extract the registry-posted results of NCT01956435. Third extraction verifier PASS 2026-11-27; held, not merged. **Ben decides** how to reconcile it with gordon2017 (same six patients) before it enters the ledger.
- [ ] Extract or exclude the 4 leads: chitvanich2016 and rajegowda2021 extracted and merged (batch 3); arbache2018 BLOCKED (no abstract, full text 403; lead row stays); wambier2018 on the paywall list. Open cohort checks: chitvanich2016 may share patients with rerknimitr2015; rajegowda2021 may share phenol-arm patients with a 2022 paper by the same group (deepadarshan2023 ref 15).
- [ ] Search Web of Science and Scopus if access exists.
- [x] Search GEO, BioImage Archive, Zenodo, Figshare (2026-11-27, two quoted queries each, APIs): 0 IGH datasets or image deposits. 4 repository hits plus 2 BioStudies literature records, all excluded. Awaiting Gate A review of `data/screening_log.csv`.
- [x] First real run of `tools/pubmed.py` (2026-11-27, cloud thread): tool works unchanged. Four queries, 17/20/4/96 hits, 100 unique PMIDs, 80 newly screened (see `data/search_log.csv`, `data/screening_log.csv`). Abstracts in `papers/excerpts/pmid_*.txt` and copied to the project files folder.
- [ ] **Gate A list** (Ben's go-ahead 2026-11-27 23:04 UTC) for the 14 PubMed records:
  - extracted and merged: 10429990 (pagnoni1999; only 1 of 4 treated women had IGH, results pooled with macular hypomelanosis), 2229495 (ploysangam1990), 22646755 (shin2013), 23656568 (goldust2013), 24616848 (ravikiran2014), 29547020 (koh2018), 34084020 (kreeshan2021), 34409340 (rambhia2020)
  - blocked: 31396960 (eun2020), 32360719 (vedamurthy2022)
  - excluded: 34409366 (arbache2021, letter with no IGH patients)
  - not started: 10594616, 15187317, 20232585
  - 9 leads without a treatment arm, not to extract: PMIDs 2508572, 29516488, 29864462, 29864463, 31823346, 33894101, 35114009, 36394380, 9765023.
- [ ] Possible text reuse: shin2013 and goldust2013 abstracts share the sentence "Two months after a single treatment, physicians' clinical assessments were performed and the patients' overall satisfaction was evaluated." Both are single-session fractional CO2 laser studies. Ben may want this checked before either is cited as independent.

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
| kim2023 | J Eur Acad Dermatol Venereol 2023, PMID 36394380 | no abstract; senescence claim rests on title |
| chitvanich2016 | J Dermatolog Treat 2016;27(5):456-60, doi:10.3109/09546634.2015.1133883 (Europe PMC: subscription required, not in PMC; tandfonline.com /doi/full/ and /doi/pdf/ returned HTTP 403 on 2026-11-27) | patient count, whether 120 lesions includes controls, control-side result, final-visit timing, cohort overlap with rerknimitr2015 |
| rajegowda2021 | Clin Dermatol Rev 2021;5(1):49-53, doi:10.4103/CDR.CDR_50_20 (open access, CC BY-NC-SA, but full text not served to the cloud: Ovid PDF link returned the abstract page; journals.lww.com HTTP 403, 2026-11-27; not in Europe PMC) | allocation of macules, assessor and blinding, number of applications per macule, timing of the final visit, side-effect counts, study dates for the cohort check |
| shin2013 | J Eur Acad Dermatol Venereol 2013;27(2):e243-6, doi:10.1111/j.1468-3083.2012.04597.x (Europe PMC 2026-11-27: subscription required, not in PMC; Wiley /doi/full and /doi/pdf HTTP 403) | grading scale, lesion counts, laser settings, sites, any visit later than 2 months |
| koh2018 | J Cosmet Laser Ther 2018;20(7-8):405-409, doi:10.1080/14764172.2018.1444771, PMID 29547020 (Europe PMC: subscription required, not in PMC; tandfonline /doi/full and /doi/pdf HTTP 403, 2026-11-27) | VAS, IGA and PSS values per arm; sessions and interval; time from final treatment; per-patient allocation of the 122 lesions |
| goldust2013 | J Cosmet Laser Ther 2013, PMID 23656568, doi:10.3109/14764172.2013.803369 (Europe PMC: subscription required, not in PMC; tandfonline /doi/full HTTP 403, 2026-11-27) | laser settings, lesion counts, assessors, the missing <25% grade, adverse events |
| ploysangam1990 | J Am Acad Dermatol 1990;23(4 Pt 1):681-4, PMID 2229495, doi:10.1016/0190-9622(90)70273-k (Europe PMC: subscription required, not in PMC; jaad.org /fulltext and /pdf HTTP 403, 2026-11-27) | lesion and biopsy counts, number of freezing sessions, follow-up after the final freeze, completeness of repigmentation |
| arbache2018 | J Am Acad Dermatol 2018;78(1):212-215, doi:10.1016/j.jaad.2017.08.019, PMID 29241792 (no abstract on PubMed; Europe PMC: subscription required, no PMC copy; jaad.org PDF and fulltext HTTP 403 Cloudflare challenge, 2026-11-27) | preliminary split-body placebo-controlled trial of 5-FU tattoo-machine infusion; likely same trial as arbache2023 |
| eun2020 | Br J Dermatol 2020;182(2):485-486, PMID 31396960, doi:10.1111/bjd.18427, low-fluence fractional CO2 laser pilot (research letter, no abstract; Europe PMC: subscription required, not in PMC; academic.oup.com HTTP 403, 2026-11-27) | every number: patients, lesions, sessions, result, any follow-up after the final session |
| vedamurthy2022 | J Am Acad Dermatol 2022;86(1):e11-e12, PMID 32360719, doi:10.1016/j.jaad.2020.04.110 (letter, no abstract; Europe PMC subscription required; jaad.org HTTP 403, 2026-11-27) | 50% trichloroacetic acid for IGH: every count, result and follow-up interval |

## Simulation extension (tests 2026-11-27; code 2026-11-27, PR open, not merged)

- `experiments/tests/test_drift_sim.py`: 35 tests for `experiments/drift_sim.py` (lighting and white-balance drift, brown spot on mottled background, 2 to 8 mm). The contract is in the file's docstring. `experiments/drift_sim.py` written 2026-11-27: all 35 pass, tests unedited (`git diff --exit-code 42fc125 -- experiments/tests` clean). `tests/` still 6 passed.
- Results: `data/drift_sim_results.csv` (720 rows, 100 trials each, seed 20261127, 20 px/mm, about 12 minutes). Section 4 added to `content/experiments.md` with line references into the CSV. Site not rebuilt (Gate B).
- Builder's defaults: diameters 2, 3, 4, 5, 6, 8 mm; mottle SD 5 %, correlation length 1 mm (Gaussian-spectrum random Fourier texture, scaled to mean 1 and SD 5 % over the unshifted field); noise SD 0.01 linear RGB; blur 0.1 mm in `run()`; drifts: exposure x0.8, x1.25, white balance warmer (1.10, 1, 0.85) and cooler (0.90, 1, 1.15). CSV reports channel L only.
- The builder may not edit the tests: `git diff --exit-code <tests commit> -- experiments/tests` must stay clean.
- Run with `python3 -m pytest experiments/tests -q` (the command in CLAUDE.md covers `tests/` only).
- Assumptions Ben may want to change: lighting drift is a uniform exposure gain only (no gradient across the field); the correction tested is ring-based per-channel normalisation; measurement is per-pixel CIELAB D65, then averaged; the experiment simulates an unchanged spot only, so every error is a false change; mottle is a multiplicative luminance texture (SD and correlation length set by the builder's defaults).

## Human gates

- **Gate A (after any search):** Ben reviews the screening list and supplies PDFs before extraction starts.
- **Gate B (before anything is public):** Ben reviews the ledger diff, sets the contact route in `site.json`, approves launch and any email.

## Blocked

| unit | status | tried |
|---|---|---|
| arbache2018 record | BLOCKED: source unreachable (2026-11-27) | https://www.jaad.org/article/S0190962217322089/pdf and /fulltext (both HTTP 403, Cloudflare challenge); PubMed record has no abstract. `data/staging/arbache2018.json` has 0 rows. Do not merge: a 0-row merge would delete the existing lead row. Needs Ben's PDF. |
| eun2020 (PMID 31396960) | BLOCKED at extraction (2026-11-27) | No abstract, no open full text after two attempts (Europe PMC subscription required; https://doi.org/10.1111/bjd.18427 -> academic.oup.com HTTP 403). 0-row stub `data/staging/eun2020.json`. Do not merge; needs Ben's PDF. |
| vedamurthy2022 (PMID 32360719) | BLOCKED: letter with no abstract, no open full text (2026-11-27) | Europe PMC REST: subscription required, not in PMC; https://doi.org/10.1016/j.jaad.2020.04.110 -> linkinghub redirect, no text; https://www.jaad.org/article/S0190-9622(20)30726-X/fulltext HTTP 403. 0-row stub `data/staging/vedamurthy2022.json` (thread push refused; committed from the saved patch). Do not merge; needs Ben's PDF. |
| laosakul2017 full text | BLOCKED (abstract extracted and merged instead) | https://www.tandfonline.com/doi/full/10.1080/09546634.2016.1221498 and /doi/pdf/ (HTTP 403, 2026-11-27); Europe PMC: subscription required |
| nct01956435 record | earlier record BLOCKED after two FAILs; third extraction PASS 2026-11-27, held (see Done) | Earlier second check failed 3 cells (months_after_final_tx rows 1 and 3; row 2 patient_noticeability). |
| arbache2023 record | earlier record BLOCKED after two FAILs; fresh record PASS and merged in batch 3 | Earlier FAILs were `uncertainty` cells (author-sponsor link, registry 'PARALLEL' vs 'split-body'). |
| rerknimitr2015 record | earlier record BLOCKED after two FAILs; fresh record PASS (second check) and merged in batch 3 | Earlier FAIL: row 1 `uncertainty` omitted the '120 lesions' denominator conflict. |

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

## Verification log (batch 3, 2026-11-27)

- arbache2023 (fresh, ABSTRACT_ONLY): verifier PASS first check, 0 failed cells (claude/project-thread-cxup2b be30a5f). Merged.
- rerknimitr2015 (fresh, ABSTRACT_ONLY): verifier 1 FAIL (3 `analysis_unit` cells), corrected, verifier 2 PASS (claude/project-thread-ehx8ue b9058ec). Merged.
- chitvanich2016 (ABSTRACT_ONLY): verifier PASS first check (claude/project-thread-95irtm f4584d1). Merged.
- rambhia2020 (PMID 34409340, FULL_TEXT PMC8361927): verifier PASS first check (claude/project-thread-d89t73 ea43591). Merged. Text says 2 sittings, Fig 1 caption a single sitting.
- rajegowda2021 (ABSTRACT_ONLY): verifier 1 FAIL (2 `uncertainty` cells), corrected, verifier 2 PASS (claude/project-thread-yz2d8x f39770c). Merged.
- kreeshan2021 (PMID 34084020, FULL_TEXT PMC8149992, one patient): verifier 1 FAIL (3 `patient_noticeability` cells), corrected, verifier 2 PASS (claude/project-thread-klrn4v 2b49638). Merged.
- shin2013 (PMID 22646755, ABSTRACT_ONLY): verifier 1 FAIL (2 cells), corrected, verifier 2 PASS (claude/project-thread-09rp96 28dda73). Merged.
- koh2018 (PMID 29547020, ABSTRACT_ONLY): verifier 1 FAIL (6 enrolled/evaluable cells), corrected, verifier 2 PASS (claude/project-thread-2f5rb4 2a0b7b1). Merged.
- ravikiran2014 (PMID 24616848, FULL_TEXT PMC3937479, tables are images and were not read): verifier 1 FAIL (6 cells), corrected, verifier 2 PASS (claude/project-thread-oir71p 1c18b69). Merged.
- goldust2013 (PMID 23656568, ABSTRACT_ONLY): verifier PASS first check (claude/project-thread-stewh6 739af95). Merged.
- ploysangam1990 (PMID 2229495, ABSTRACT_ONLY): verifier 1 FAIL (3 cells), corrected, verifier 2 PASS (claude/project-thread-uge79q 1e072ef). Merged.
- pagnoni1999 (PMID 10429990, FULL_TEXT open-access PDF): verifier PASS first check, 0 failed cells (claude/project-thread-s0m95g 9884523). Merged.
- nct01956435 (third extraction, FULL_TEXT): verifier PASS (claude/project-thread-82j76h 86c0768). Held for Ben.
- arbache2021 (PMID 34409366): excluded, not verified for the ledger.

## Next session

- Measurement tool plan (2026-11-27, PR "Plan: spot colour-match measurement tool", branch claude/project-thread-fm8afm, based on PR #5's branch): `content/measurement-tool-plan.md`, planning only, not in `site.json`, not built. Proposes signed ΔL* of a fixed inner disc minus a reference ring as the measurand, with Δb*, ΔE, area and absolute ring colour beside it. First tasks T1 (test-author: drift-sim v2 tests), T2 (test-author: placement-sim tests), T3 (searcher: prior-art query set) can start without Ben. Awaiting Ben's answers to the plan's open questions (section 8). Not merged.

Close Module 1 (list above). Drift simulation PR ("Drift simulation: tests and implementation") awaits Ben's review; possible follow-up: report the b* (yellowness) channel, where white-balance drift matters more.
