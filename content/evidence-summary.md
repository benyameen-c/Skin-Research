## Evidence summary: Module 1, IGH white spots

<p class="notice">This page is research notes, not medical advice. It does not recommend any treatment. Whether a spot is IGH, and whether to treat it, is a question for a dermatologist.</p>

<p><span class="tag human">Published human finding</span> Every result below is a number recorded in <code>data/evidence.csv</code> with a verbatim quote in <code>data/evidence_quotes.jsonl</code>, and each one names its study. <span class="tag calc">Calculation on published counts</span> Counts of studies and rows come from the script <code>tools/evidence_summary.py</code>, whose output is pasted in the appendix. No result is pooled, averaged or added up across studies, because the studies count different things (patients, spots, limbs or body sides), stop at different outcome tiers and time their visits differently.</p>

Ledger state for this page: `main` after arbache2018 was merged, 66 rows from 23 studies (count, appendix).

### The question

Which treatments help a small white spot match the surrounding skin, and does the match last at least six months after the final treatment?

### What the ledger supports today

The ledger holds 20 studies with rows for IGH itself (count, appendix). Treatments based on cold, chemical wounding, light and lasers, topical creams, needle delivery of 5-fluorouracil and small skin grafts from the scalp all report that some colour came back in some spots during the study. No row in the ledger measures a lasting colour match, and no row is recorded as complete area coverage (count, appendix).
Only 4 of those 20 studies have a result row with a stated interval after the final treatment (count, appendix).
The longest of those intervals is 2 months, in two single-session fractional CO2 laser series (shin2013, goldust2013).
The six-month question therefore cannot be answered from the published work found so far: the measurement it needs has not been reported. What the ledger does support is narrower. Several treatments produce partial repigmentation by the end of a study, usually graded as a share of the spot, mostly by graders whose blinding is not stated, often counting spots from the same person as if they were independent, and in the controlled studies that report their control side, the untreated or sham-treated spots changed too.

### Three outcomes, kept apart

- **Partial repigmentation**: some colour returned. "More than 75% improved", the top grade in several of these papers, is partial (for example laosakul2017).
- **Complete area coverage**: the whole spot has pigment again, which can still be the wrong shade.
- **Lasting colour match**: colour and texture blend with nearby skin at least six months after the last treatment.

On IGH rows the ledger records 23 rows of partial repigmentation, 6 rows of instrument colour readings, 2 rows of lesion counts and 20 unquantified rows (count, appendix). Instrument readings (colorimeter lightness or luminosity) and counts of white spots are kept as their own tiers: neither shows that a spot matches the skin around it.

### Treatments and what each study reached (IGH rows only)

"Access" is what was read: full text, or the abstract only. Abstract-only rows are weaker, because the abstract usually leaves out denominators, timing and side effects. "Longest gap after final treatment" is the ledger's `months_after_final_tx`: a number only when the source states the interval or it follows from a single session; `NOT_DERIVABLE` when the paper gives time from the start only.

| Ledger treatment class | Study | Access | Design (as recorded) | Unit counted | Highest tier | Result as quoted | Longest gap after final treatment |
|---|---|---|---|---|---|---|---|
| cryotherapy | laosakul2017 | abstract | randomized, evaluator-blinded; treated versus untreated spots | spots | partial | 82.3% of treated spots versus 2% of untreated spots more than 75% improved "at the fourth month" | NOT_DERIVABLE (single session, date of session not stated) |
| cryotherapy versus 50% TCA peel | deoson2025 | full text | two parallel groups, allocated by alternate patients | spots (5 per patient) | partial | more than 75%: 29 of 75 cryotherapy spots (38.7%) versus 15 of 75 TCA spots (20%), at 4 months from start | NOT_DERIVABLE (up to 3 monthly sittings, sittings per spot not reported) |
| cryotherapy versus 88% phenol | rajegowda2020 | full text | within-patient comparison, 5 spots per arm per patient; no untreated spots | spots | partial | excellent (more than 75%): 75 of 125 cryotherapy spots (60%) versus 37 of 125 phenol spots (29.6%), "at the end of the treatment period" | NOT_DERIVABLE (up to 3 monthly applications; follow-up not timed from the last) |
| cryotherapy | ploysangam1990 | abstract | treatment series with histology | spots | unquantified | frozen spots "repigmented in 6 to 8 weeks"; share that repigmented not in abstract | NOT_DERIVABLE |
| chemical peel (88% phenol) | ravikiran2014 | full text | single arm | spots | partial | 89 of 139 spots (64%) repigmented at 3 months from start; more than 75% improvement in 45% of the repigmented spots (the abstract gives 45% of all spots) | NOT_DERIVABLE |
| energy device (308 nm excimer) | deepadarshan2023 | full text | single arm, twice weekly for 12 weeks | spots | partial | excellent (more than 75%) in 83 of 200 spots (41.5%) at week 16 | 1 month (Methods: "further followed up for a duration of 1 month") |
| energy device (excimer) | gordon2017 | abstract | split-body, single-blinded pilot | spots | partial | treated spots had "significantly higher repigmentation"; no numbers in abstract | NOT_DERIVABLE |
| energy device (1550 nm non-ablative fractional) | rerknimitr2015 | abstract | treated versus control spots in the same patients | spots | partial | "some improvement" in 83.34% of treated versus 18.34% of control spots | NOT_DERIVABLE |
| energy device (fractional CO2) | goldust2013 | abstract | single arm, one session | patients | partial | 115 patients (47.9%) more than 75% improved | 2 months |
| laser (fractional CO2) | shin2013 | abstract | single-arm pilot, one session, mostly facial spots | patients | partial | more than 50% improvement in 36 patients (90%) | 2 months |
| energy device (CO2 and Er:YAG fractional) versus topical tretinoin | koh2018 | abstract | three groups; 122 spots from 18 patients | spots | unquantified | both lasers superior to tretinoin (p < 0.01); no values in abstract | NOT_DERIVABLE |
| energy device plus topical (1550 nm laser plus tacrolimus) | chitvanich2016 | abstract | treated versus control spots in the same patients | spots | partial | 91.67% of treated spots "showed an improvement"; control result not in abstract | NOT_DERIVABLE |
| energy device, alone and with topical bimatoprost | kreeshan2021 | full text | single case report | one patient | unquantified | "better improvement" on the combination patch; no grade | NOT_APPLICABLE or NOT_DERIVABLE (still on treatment at the last report) |
| topical (0.1% tacrolimus) | rerknimitr2013 | abstract | double-blind, placebo-controlled, split-body | patients | partial | 11% of patients improved on the treated side; not significant on clinical assessment | NOT_DERIVABLE |
| topical (tretinoin) | pagnoni1999 | full text | split-forearm, 4 women of whom 1 had IGH | one IGH spot | partial | "recovery of pigmentation" after 4 months in the illustrated IGH spot; text calls it partial | NOT_DERIVABLE |
| topical (1% pimecrolimus) | asawanonda2010 | abstract | not in abstract (publisher files it as a case report) | not in abstract | unquantified | authors report "the success of 1% pimecrolimus cream in inducing repigmentation"; no count or degree | NOT_DERIVABLE |
| 5-fluorouracil by tattoo machine versus saline | arbache2018 | full text | interim analysis of a randomized, split-body, single-blinded, placebo-controlled trial; first 8 patients who completed | limbs | partial | 75.3% repigmentation with 5-fluorouracil versus 33.8% with saline, P < .001, by Antera 3D imaging; the blinded dermatologists' limb choice is described but its result is not reported | NOT_DERIVABLE (number of sessions and time point not reported) |
| 5-fluorouracil by tattoo machine versus saline | arbache2023 | abstract | split-body, single-blinded (registry says parallel) | limbs | lesion count | median white spots per limb 32 to 12 with 5-fluorouracil versus 31 to 21 with saline | 1 month ("30 days after treatment"; number of sessions not in abstract) |
| 5-fluorouracil by hand needle | rambhia2020 | full text | technique report, no patient count | not reported | unquantified | 2 sittings "yielded complete uniform repigmentation"; no count, no follow-up interval | NOT_DERIVABLE |
| grafting (machine mini-punch grafts from hairless scalp, then NB-UVB) | hirobe2018 | full text | uncontrolled case series, "Four of ﬁve patients underwent this treatment", reported one by one; no comparator | patients | unquantified | "excellent color-matched repigmentation" after 1 or 2 months from grafting, the authors' visual judgement with no scale, extent or instrument | NOT_DERIVABLE (NB-UVB after grafting "three times a week for 1e2 months" [1 to 2 months; the PDF prints the dash as "e"], end date per patient not reported) |

The ledger files shin2013 under `laser` and goldust2013 under `energy_device` for the same treatment (a single fractional CO2 session). That is a labelling difference in the ledger, not a difference in the treatments.

### Durability: the direct answer to the six-month question

- **No study in the ledger reports a lasting colour match.** There are no `lasting_color_match` rows and no `complete_area_coverage` rows (count, appendix).
- **Most results cannot be placed after the final treatment.** On IGH rows, 38 of 46 treated-arm rows are `NOT_DERIVABLE` (count, appendix). These papers time their visits from the start of treatment ("at the fourth month", "at the end of 3 months of initiation of therapy", "at the end of the treatment period"), and several let the number of sittings vary by spot. A result read at month 4 from the start could be months after the last treatment or only weeks after it, and the paper does not say which. That is why the ledger never converts time from the start into time from the final treatment.
- **Where an interval is stated, it is short.**
    - 2 months after a single fractional CO2 session (shin2013, goldust2013).
    - 1 month after a 12-week excimer course, by the Methods (deepadarshan2023). The same paper's Results speak of a "4-month follow-up", which matches 16 weeks counted from baseline, so the ledger keeps the Methods figure.
    - 30 days "after treatment" for 5-fluorouracil by tattoo machine (arbache2023), with the number of sessions not in the abstract, so it is recorded as [1] month on the assumption that "after treatment" means after the final session.
- **A follow-up with no stated starting point.** rajegowda2020 reports that no spot in either arm "showed reappearance in depigmentation at the end of 3months follow up", but applications were monthly for up to 3 and varied by spot, so the ledger records it as unquantified and `NOT_DERIVABLE`, not as an interval after the final treatment.
- **A long follow-up timed from grafting, not from the final treatment.** In hirobe2018 the authors state that in "our two patients that were followed up to 8 (patient 1B) and 12 (patient 1C) months, the color-matched repigmentation was maintained". That is their own statement, judged by eye with no scale or instrument, and the months are counted from grafting. Every grafted patient then had NB-UVB "three times a week for 1e2 months" with no end date reported, so the ledger records these rows as unquantified and `NOT_DERIVABLE`, not as a lasting colour match or a result six months after the final treatment. The same paper cites earlier work in which "minigrafts of normal skin into IGH skin sites became depigmented 18 months after grafting" (hirobe2018).
- **IGH rows at six months or more after the final treatment: 0** (count, appendix).
- **The only long follow-up timed from a final treatment is not IGH, and it shows loss.** In pagnoni1999, 2 patients with macular hypomelanosis seen "a year after stopping tretinoin" had "clinical regression of the macules to the original state". That row is recorded as an adjacent diagnosis and never counted as IGH, but it is the only assessment in the ledger recorded as more than 3 months after a final treatment, and its direction is against lasting benefit.
- **Darker than the surroundings is also an outcome.** Post-inflammatory hyperpigmentation persisted in 18 of 200 spots (9%) "at 4th month of follow up" after excimer (deepadarshan2023). ravikiran2014 notes that its phenol method "is based on post inflammatory hyperpigmentation induced by chemical wounding", so pigment seen at 3 months may be inflammatory pigment rather than a lasting match.

### Weaknesses that recur

These come from the `uncertainty`, `design` and `comparator` fields. The script finds them by keyword and lists the matching studies in the appendix; each match was read against its row before it is used here.

- **Spots counted as if independent.** In 9 of 20 IGH studies the uncertainty field notes several spots per patient, clustered or analysed as independent (count, appendix).
    - For example, 5 spots per patient with a chi-square test on 75 spots per arm (deoson2025).
    - 122 spots from 18 patients, with no statement of how clustering was handled (koh2018).
- **No untreated, placebo or sham comparison.** 12 of 20 IGH studies have none: single-arm series, case reports, or active treatments compared only with each other (count, appendix). Without one, natural change and seasonal tanning cannot be separated from treatment.
- **Untreated and sham spots improved.** Where a comparison exists, the control side often moved.
    - Saline by tattoo machine took the median from 31 to 21 white spots per limb (arbache2023).
    - In the interim report of a placebo-controlled tattoo-machine trial, saline limbs reached 33.8% repigmentation against 75.3% for 5-fluorouracil limbs, by Antera 3D imaging (arbache2018).
    - Graders called 18.34% of control spots improved (rerknimitr2015).
    - 2% of untreated spots reached more than 75% improvement (laosakul2017).
    - In the adjacent-diagnosis microneedling trial, the abstract reports peripheral tanning in 85% of untreated lesions against 80% of treated ones, in wording that is ambiguous (elhoshy2025).
- **Blinding.** Only 5 of 20 IGH studies state that grading was blinded (count, appendix); in the rest the abstract or paper does not say.
- **Single sessions.** 3 of 20 IGH studies give a single session (count, appendix). This is why their gap after the final treatment is known, and also why their follow-up is short.
- **Denominators that do not fit.** In 6 of 20 IGH studies a printed percentage does not fit the stated count, or the stated count conflicts with the design (count, appendix).
    - For example, 82.3% is not a whole-number share of 43 treated spots (laosakul2017).
    - 11% is not a whole-number share of 26 patients (rerknimitr2013).
    - "120 lesions" conflicts with two treated spots per patient in 30 patients (rerknimitr2015).
- **Patients versus spots.** The two single-session fractional CO2 series count patients, not spots (goldust2013, shin2013), and the grafting series reports each patient's grafted spots as a whole (hirobe2018). Most others count spots. arbache2023 counts white spots per limb, and arbache2018 reports repigmentation per limb. These numbers are not comparable with each other.
- **Face versus off-face.** The only study whose ledger row names the face says it was the most commonly treated area (shin2013), while its authors note that IGH most often affects the extremities. Studies that name a site report shins, legs, forearms, arms, the back, limbs or extremities (deoson2025, deepadarshan2023, ravikiran2014, kreeshan2021, pagnoni1999, arbache2023, arbache2018, rerknimitr2015, hirobe2018). Most abstracts do not say.
- **Possible shared cohort.** arbache2018 and arbache2023 cite the same trial registration, so the 8 patients in the interim letter may be among the later paper's patients. They are listed as two studies, and they should not be counted as independent evidence (arbache2018, arbache2023).
- **Abstract only.** 11 of 20 IGH studies were read from the abstract only (count, appendix); their missing counts, timing and side effects are recorded as `not in abstract`, never guessed.

### Reported separately: not IGH, or IGH not separated

These rows are in the ledger but are never counted as IGH evidence above.

| Study | Why it is separate | Access | What the row records |
|---|---|---|---|
| elhoshy2025 | adjacent diagnosis: localized acquired hypomelanosis | abstract | single microneedling session, assessed at 3 months; [untreated halves improved about as much as treated halves on the reported medians]; no between-arm statistics in the abstract |
| pagnoni1999 (macular hypomelanosis rows) | 3 of the 4 treated women had macular hypomelanosis, and most results are pooled with the 1 IGH patient | full text | tretinoin; loss of effect a year after stopping in 2 macular hypomelanosis patients |
| suvanprakorn1985 | mixed: vitiligo, IGH and postinflammatory leukoderma, results not separated | abstract | melanocyte grafting; "successful repigmentation" with no counts |

### What is missing

- **Paywalled full texts** (Ben supplies PDFs into `papers/pdfs/`; the list with links is in `STATUS.md`): review2025, laosakul2017, arbache2023, rerknimitr2015, rerknimitr2013, gordon2017, wambier2018, elhoshy2025, suvanprakorn1985, kim2023, chitvanich2016, shin2013, koh2018, goldust2013, ploysangam1990, eun2020, vedamurthy2022. Ten of the twenty IGH studies above are on it; asawanonda2010 is abstract-only but not yet listed there.
- **Blocked records with no rows yet**: eun2020 (PMID 31396960), vedamurthy2022 (PMID 32360719). No abstract and no open full text.
- **Held record**: nct01956435, the registry-posted results of the gordon2017 cohort. It passed verification but is not in the ledger until Ben decides how to reconcile the two.
- **Leads not yet extracted**: wambier2018 (no abstract); PMIDs 10594616 and 15187317 from the Gate A list.
- **Excluded**: arbache2021 (PMID 34409366), a letter with no IGH patients. The retracted duplicate of rajegowda2020 (the same authors' later article in another journal) was removed from the ledger; the original, read in full, replaces it. The retraction notice is cited in `STATUS.md`.
- **Not in any ledger row**: a colour match with the surrounding skin that is graded or measured (the "color-matched" wording in hirobe2018 is the authors' visual statement), a visit six months or more after the final treatment, and how noticeable the spot is to the patient (the patient measures recorded are satisfaction scores).

### Appendix: counts

Rerun with `python3 tools/evidence_summary.py`. Check this page with `python3 tools/evidence_summary.py --check content/evidence-summary.md`, which fails if a number above is not in a quote of the study named on its line, or, on a line marked "(count, appendix)", not in this output.

    ledger rows: 66; studies: 23

    A. Rows and studies by diagnosis group (a study can sit in more than one group)
      IGH       rows  51  studies 20: arbache2018, arbache2023, asawanonda2010, chitvanich2016, deepadarshan2023, deoson2025, goldust2013, gordon2017, hirobe2018, koh2018, kreeshan2021, laosakul2017, pagnoni1999, ploysangam1990, rajegowda2020, rambhia2020, ravikiran2014, rerknimitr2013, rerknimitr2015, shin2013
      mixed     rows   3  studies  2: pagnoni1999, suvanprakorn1985
      adjacent  rows  11  studies  2: elhoshy2025, pagnoni1999
      lead      rows   1  studies  1: wambier2018

    B. Access level of the 20 studies with IGH rows
      ABSTRACT_ONLY 11: arbache2023, asawanonda2010, chitvanich2016, goldust2013, gordon2017, koh2018, laosakul2017, ploysangam1990, rerknimitr2013, rerknimitr2015, shin2013
      FULL_TEXT      9: arbache2018, deepadarshan2023, deoson2025, hirobe2018, kreeshan2021, pagnoni1999, rajegowda2020, rambhia2020, ravikiran2014

    C. months_after_final_tx on IGH rows (51 rows; 46 treated-arm rows)
      NOT_APPLICABLE  all IGH rows   7 | treated-arm rows   4
      NOT_DERIVABLE   all IGH rows  39 | treated-arm rows  38
      a number        all IGH rows   5 | treated-arm rows   4
      rows with a number: shin2013 2; goldust2013 2; deepadarshan2023 1; arbache2023 1; arbache2023 1
      IGH studies with at least one row timed from the final treatment: 4 of 20
      IGH rows at 6 months or more after the final treatment: 0

    D. Outcome tier, IGH rows
      instrument_color           6
      lesion_count               2
      partial_repigmentation    23
      unquantified              20
      complete_area_coverage rows in the whole ledger: 0
      lasting_color_match rows in the whole ledger: 0

    E. Per study (IGH, mixed and adjacent rows; leads left out)
      study_id | group | access | treatment classes | units | tiers | longest months after final tx
      arbache2018 | IGH | FULL_TEXT | needling_drug_delivery,needling_sham | limb | partial_repigmentation,unquantified | none
      arbache2023 | IGH | ABSTRACT_ONLY | needling_drug_delivery,needling_sham | limb | lesion_count | 1
      asawanonda2010 | IGH | ABSTRACT_ONLY | topical | not | unquantified | none
      chitvanich2016 | IGH | ABSTRACT_ONLY | control,energy_device_plus_topical | lesion | instrument_color,partial_repigmentation | none
      deepadarshan2023 | IGH | FULL_TEXT | energy_device | lesion | partial_repigmentation | 1
      deoson2025 | IGH | FULL_TEXT | chemical_peel,cryotherapy | lesion | partial_repigmentation | none
      elhoshy2025 | adjacent | ABSTRACT_ONLY | control,needling | lesion,not | partial_repigmentation | 3
      goldust2013 | IGH | ABSTRACT_ONLY | energy_device | patient | partial_repigmentation | 2
      gordon2017 | IGH | ABSTRACT_ONLY | energy_device | lesion | partial_repigmentation | none
      hirobe2018 | IGH | FULL_TEXT | grafting | patient | unquantified | none
      koh2018 | IGH | ABSTRACT_ONLY | energy_device,topical | lesion | unquantified | none
      kreeshan2021 | IGH | FULL_TEXT | energy_device,energy_device_plus_topical | patient | unquantified | none
      laosakul2017 | IGH | ABSTRACT_ONLY | control,cryotherapy | lesion | instrument_color,partial_repigmentation | none
      pagnoni1999 | IGH+adjacent+mixed | FULL_TEXT | control,topical | lesion,patient | partial_repigmentation,unquantified | 12
      ploysangam1990 | IGH | ABSTRACT_ONLY | cryotherapy | lesion | unquantified | none
      rajegowda2020 | IGH | FULL_TEXT | chemical_peel,cryotherapy | lesion | partial_repigmentation,unquantified | none
      rambhia2020 | IGH | FULL_TEXT | needling_drug_delivery | not | unquantified | none
      ravikiran2014 | IGH | FULL_TEXT | chemical_peel | lesion | partial_repigmentation | none
      rerknimitr2013 | IGH | ABSTRACT_ONLY | topical | patient,side | instrument_color,partial_repigmentation | none
      rerknimitr2015 | IGH | ABSTRACT_ONLY | control,energy_device | lesion,not | instrument_color,partial_repigmentation | none
      shin2013 | IGH | ABSTRACT_ONLY | laser | patient | partial_repigmentation | 2
      suvanprakorn1985 | mixed | ABSTRACT_ONLY | grafting | not | unquantified | none

    F. Control and sham arms, all groups (arm_result as recorded)
      laosakul2017 [IGH] control: 2% of control lesions showed more than 75% improvement at the fourth month
      elhoshy2025 [adjacent] control: median peripheral tanning observed in 85% of lesions
      elhoshy2025 [adjacent] control: median physician GAI 33.33%
      elhoshy2025 [adjacent] control: median VESTA 29%
      elhoshy2025 [adjacent] control: median patient GAI 50%
      elhoshy2025 [adjacent] control: median increase of +3 grades
      arbache2023 [IGH] needling_sham: median achromic lesions 31 (IQR 24-43) at baseline to 21 (IQR 16-31) post-treatment, p = .000006
      rerknimitr2015 [IGH] control: 18.34% of lesions in control group showed some improvement, vs. 83.34% in treatment group; P < 0.05; counts not in abstract
      chitvanich2016 [IGH] control: not in abstract
      pagnoni1999 [mixed] control: no changes in pigmentation, glyphic pattern, elastic values or histology, in either IGH or MH
      arbache2018 [IGH] needling_sham: 33.8% repigmentation (placebo) vs 75.3% (5-FU), P < .001 [P printed as 'P \.001' in the converted text]

    G. Keyword screens on IGH studies (pointers to rows, not findings)
      untreated, placebo or sham comparison (control or sham row, or comparator names one): 8 of 20: arbache2018, arbache2023, chitvanich2016, gordon2017, laosakul2017, ploysangam1990, rerknimitr2013, rerknimitr2015
      no such comparison (single arm, case report, or active treatments only): 12 of 20: asawanonda2010, deepadarshan2023, deoson2025, goldust2013, hirobe2018, koh2018, kreeshan2021, pagnoni1999, rajegowda2020, rambhia2020, ravikiran2014, shin2013
      lesions clustered in patients, or analysed as independent: 9 of 20: chitvanich2016, deepadarshan2023, deoson2025, gordon2017, koh2018, laosakul2017, rajegowda2020, ravikiran2014, rerknimitr2015
      blinding stated as done in design or assessment: 5 of 20: arbache2018, arbache2023, gordon2017, laosakul2017, rerknimitr2013
      single treatment session: 3 of 20: goldust2013, laosakul2017, shin2013
      face named as a treated site: 1 of 20: shin2013
      denominator or count that does not fit, or conflicts: 6 of 20: chitvanich2016, goldust2013, laosakul2017, ravikiran2014, rerknimitr2013, rerknimitr2015
