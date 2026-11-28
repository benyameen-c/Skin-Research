# Project brief: lasting colour repair of idiopathic guttate hypomelanosis

Draft for review, 28 November 2026. Not published, not linked from the site (`site.json` does not list it). Research notes, not medical advice.

## How to read this brief

This brief is for a dermatology researcher or grant reviewer meeting the project for the first time. The project is an open evidence effort run by a non-clinician with an engineering background. Its aim is to set out the problem clearly enough that a fuller study can be designed and run by professionals.

Statements carry one of three weights:

- **Evidence** is a published human finding quoted word for word, either in the project's ledger (`data/evidence.csv`) or in a saved source the project checked. It always names its study or PMID.
- **[Inference]**, in square brackets, is the project's own reasoning. It is a hypothesis.
- **Model, level 0** is simulation output that follows from assumed rates.

Material from a pull request not yet merged into the project's main branch is marked *(unmerged, PR n)*. Outside AI reports are used only for claims the project checked against a primary source and found.

## 1. The question

Idiopathic guttate hypomelanosis (IGH) is "a common leukodermic dermatosis of obscure origin, consisting of small 2- to 5-mm achromic or hypopigmented macules, mainly affecting the exposed upper and lower extremities", and its prevalence "became more common with advancing age" (Falabella 1987, PMID 3805391).

> Which treatments make a small white spot match the surrounding skin, and does that match last at least six months after the **final** treatment?

Two rules run through the project:

- **Follow-up is counted from the final treatment.** A result read "at month 4" of a course that may have ended at month 3 is not a four-month durability result.
- **Three outcomes are kept apart.**
  - Partial repigmentation: some colour returned. "More than 75% improved" is partial.
  - Complete area coverage: the whole spot has pigment, possibly the wrong shade.
  - Lasting colour match: the spot blends with nearby skin six months or more after the last treatment.

The longer aim is to find what is damaged in a spot, so that a treatment can address the cause rather than bring pigment back for a while.

## 2. What the published evidence shows, and what it does not

The ledger holds the human IGH treatment studies the project found and could read, one row per arm, endpoint and time point: 64 rows from 23 studies, 19 of them with rows for IGH itself (`content/evidence-summary.md`). Nothing is pooled, because the studies count different units (patients, spots, limbs).

**Evidence.**

- **Treatments tried.** Cryotherapy, phenol and TCA peels, excimer light, fractional lasers, topical tacrolimus, pimecrolimus and tretinoin, needle-delivered 5-fluorouracil and scalp mini-grafts all report some colour returning in some spots.
- **No ledger row records a lasting colour match or complete area coverage.**
- **Follow-up after the final treatment.**
  - Only 4 of 19 IGH studies state any interval after the final treatment.
  - The longest interval is 2 months, after a single fractional CO2 session: "Two months after a single treatment session, 115 patients (47.9%) exhibited more than 75% clinical improvement" (goldust2013; shin2013 is similar). This is partial repigmentation.
  - 36 of 44 treated-arm IGH rows give time from the start of treatment only. No IGH row is at six months or more after a final treatment.
- **The longest durability claim** comes from a 4-patient grafting series: "our two patients that were followed up to 8 (patient 1B) and 12 (patient 1C) months, the color-matched repigmentation was maintained" (hirobe2018). That is a judgement by eye with no scale, timed from grafting. NB-UVB followed "three times a week for 1e2 months" [1 to 2 months], with no end date given for each patient.
- **The one longer follow-up from a final treatment shows loss, and it is not IGH.** In macular hypomelanosis, "a year after stopping tretinoin", 2 patients had "clinical regression of the macules to the original state" (pagnoni1999).

**Recurring weaknesses.**

- 12 of 19 IGH studies have no untreated, placebo or sham comparison.
- Where there was a control, it often changed too. Saline by tattoo machine took median white spots per limb from 31 to 21 (arbache2023).
- 9 of 19 count several spots per person as if they were independent.
- Only 4 of 19 state that grading was blinded.

[Inference: several treatments bring some pigment back for a few months. Whether any of them produces a match that lasts is unknown, because no study has reported the measurement that would show it.]

## 3. The measurement gap and the proposed objective colour tool

**Evidence: colour match is judged by eye.**

- IGH studies grade repigmentation visually. Four record colorimeter lightness (chitvanich2016, laosakul2017, rerknimitr2013, rerknimitr2015), but none compares the spot with the skin around it.
- Of nine registered trials in other white-spot conditions with a colour-match outcome, none names an instrument *(unmerged, PR 21)*.
- In the pivotal cell-suspension trial in vitiligo (NCT04547998, posted results), ≥80% repigmentation was reached in 9 of 25 treated areas against 0 of 25 controls at week 24. The blinded four-step colour-match grade still did not differ between arms (p "1.000"). Only areas with some repigmentation were graded, and nothing after week 24 is posted.

[Either the returned pigment matches equally well whatever brought it back, or a four-step grade on 19 pairs cannot detect a difference.]

**Evidence: no published repeatability figure fits spots this small.**

- The closest is a contact spectrophotometer on facial skin: 0.63 ΔE\*ab between lift-and-replace readings in one session (Wang et al. 2018, doi 10.1002/col.22230).
- Its smallest skin-tested aperture is 3 mm, larger than a 2 mm spot.

**Proposal** (`content/measurement-tool-plan.md`):

- **Capture.** Calibrated raw photographs with a colour card in frame, device-only lighting (cross-polarised where possible), and a rigid spacer that fixes distance and angle.
- **Measure.** ΔL\*, the lightness of a fixed disc inside the spot minus a ring of skin around it, with Δb\* and CIEDE2000 as secondary numbers. It is defined for every spot, including spots that did not repigment, and its sign shows overshoot to darker than the skin.
- **Lasting match.** |ΔL\*| below a threshold that people cannot see, at six months or more after the final treatment. That threshold is not yet sourced.
- **Target.** A smallest detectable change of 1.0 L\* or less on a 2 mm spot. [This is the project's own design target, not a published figure.]

**Model, level 0** (synthetic spots, not skin):

- Dividing by the surrounding ring removes uniform exposure drift.
- A misplaced region is the dominant error: a 0.25 mm offset on a 2 mm spot reads as 9.9% false fading.
- Only registration on the surrounding skin texture met the placement target, at −0.07% mean false change and 0.43 spread. A sticker re-applied with 0.1 mm error failed.
- Specular glare is not yet handled: false change reached 18.5% in the worst 2 mm case *(unmerged, PR 18)*.

## 4. What is known about what is damaged in a spot

These sources are small, mostly descriptive, and mostly read as abstracts. They come from the project's damage scan *(unmerged, PR 31)* and its check of a tissue-markers report *(unmerged, PR 24)*.

**Evidence, fairly consistent across studies.** There are fewer melanocytes in a spot, but some remain.

- "At the center of the lesions melanocytes were invariably reduced in number to between 25 and 50 % of normal", and "In no case were melanocytes completely absent" (Wilson 1982, PMID 6183861, 20 cases).
- "The pathogenesis of IGH involves an absolute decrease in the number of melanocytes" (Wallace 1998, PMID 9765023).
- One study disagrees: "similar melanocyte density was observed in the lesional epidermis compared with the normal epidermis, melanoblast density was dramatically decreased" (Hirobe 2018, five patients).

**Evidence from one or two small groups:**

- **Pigment transfer.** "a functional defect in the transfer of melanosomes from the melanocytes to the keratinocytes" (PMID 25088925, four patients).
- **Senescence.** "expression of p16, p21, and hp1 was significantly higher in lesional skin of IGH patient as compared to healthy controls" (PMID 29516488, six patients against six other people).
- **Autophagy.** "ATG7 downregulation emerged as the earliest molecular alteration and was consistently found in senescent melanocytes and idiopathic guttate hypomelanosis skin" (PMID 41453137, mainly cultured cells).
- **The dermis.** "superficial dermal fibrosis in 90% (18/20) of our IGH cases", which the authors read as "an interaction between melanocytes and the subjacent dermis in IGH" (PMID 35114009).
- **Repigmentation off the body.** IGH skin grafted onto nude mice: "Twenty days after skin transplantation, repigmentation of the area was observed" (PMID 2508572).

**Not established.**

- **No cause.** No study has changed a suspected cause and watched spots appear or clear.
- **No gene.** "An age-related somatic mutation of melanocytes" was proposed in 1982 (PMID 6183861) without any DNA being measured. No study has compared DNA inside and outside a spot.
- **No same-person expression data.** No dataset compares a spot with the same person's normal skin.
- **Unknown order.** It is unknown which cell fails first: the melanocyte, the keratinocyte or the fibroblast.

**The background skin, outside IGH.** Sun-exposed skin "is a patchwork of thousands of evolving clones with over a quarter of cells carrying cancer-causing mutations while maintaining the physiological functions of epidermis" (PMID 25999502).

[Inference: damage spread across thousands of clones offers no single gene to correct. The best-supported defect is missing or inactive pigment cells, possibly held back by the dermis. So the nearest complete fix is replacing or reawakening healthy melanocytes, after finding out which layer is failing.]

## 5. Candidate professional studies, in order

Each study builds on the one before. All of them need a dermatologist and ethics review.

**Study 1. Validate the colour measurement.**

- **Design.** Phantoms first, then repeat sessions on unchanged volunteer skin, to measure the smallest detectable change in ΔL\* at 2 to 5 mm.
- **Link to clinical practice.** Measure agreement with a blinded three-rater panel grade, so the number is tied to what clinicians see *(suggested in unmerged PR 21)*.
- **Why first.** Untreated control spots in the ledger changed on their own, so a six-month claim needs a known noise floor.
- **Approval.** Photographing volunteers needs an independent ethics determination first. One board posts fees of $925 (non-human-subject determination), $1,200 (exempt) and $2,100 (expedited) *(unmerged, PR 20)*.

**Study 2. Modern cell transplantation, with colour read six months after the final treatment.**

- **Design.** Autologous melanocyte-keratinocyte transplantation on IGH spots, with untreated control spots in the same person.
- **Primary endpoint.** ΔL\* for every spot. Any adjunct, such as NB-UVB, counts as treatment, so the six-month clock starts only when everything has stopped.
- **IGH precedents.**
  - Blister-roof grafts: "Repigmentation was visible within 7 to 14 days", with nothing reported later (PMID 3908515).
  - Scalp mini-grafts held a match by eye to 12 months from grafting (hirobe2018).
  - An older series is negative: "Minigrafts of normal skin implanted in idiopathic guttate hypomelanosis lesions did not modify the achromic defects" (PMID 3805391).
- **Evidence from vitiligo, not IGH.** A 23-patient series reports repigmentation "sustained over 84 months" (PMID 39507768). That is a VASI score, not a colour match.
- **Nearest registered trial.** NCT07662915 covers non-vitiligo leukoderma, with "Color Match Assessment" at "6 months". It is not yet recruiting and does not name IGH.
- [Inference: an arm with a graft that carries its own dermis would also test whether the dermis is to blame.]

**Study 3. Paired tissue comparison, inside against just outside a spot, in the same person.**

- **Measures.**
  - Melanocytes and melanoblasts per millimetre of basement membrane.
  - p16 in melanocytes and in dermal fibroblasts.
  - ATG7.
  - Single-melanocyte DNA sequencing, a method that already exists (PMID 33029006).
- **Pairing.** Each biopsy is paired with the photographic measure. A sister spot is sampled six months after the final treatment in Study 2.
- **Why.** This decides which layer is failing, whether cell replacement can last, and whether any gene-level target exists.
- **Limits.**
  - A punch removes most of a 2 to 5 mm spot, so the same spot cannot be sampled twice.
  - Research-only biopsies fall outside expedited review and need full-board approval *(unmerged, PR 20)*.

**Funding routes checked** *(unmerged, PR 20)*:

- **NSF SBIR Phase I**, "up to $305,000" over 6 to 18 months. This fits Study 1 through a small business.
- **NIH R21**, up to $275,000 direct over two years, with NIAMS participating. This needs an academic partner, and it is the route that fits Studies 2 and 3.

## 6. The project's simulations and how much weight they carry

All simulations use synthetic shapes and no patient images, and all had their tests written before their code. The measurement simulations (section 3) model the instrument, not biology. Their main limit is that the synthetic skin never changes between visits except for noise.

**The cell model of one spot** *(unmerged, PR 29)* compares two explanations:

- **H1:** melanocytes wear out on their own.
- **H2:** senescent or scarred dermis wears them out.

Of its 33 inputs, 10 are quoted values and 23 are labelled assumptions. None of the quoted values is a rate. The only intervention modelled is adding melanocytes, and gene therapy is out of scope.

**Model, level 0.** Over 4,000 parameter draws:

- Six months after the final transplant session, H1 and H2 cannot be told apart at a 1.0 L\* threshold.
- 9 of 231 accepted H2 sets faded by more than 1.0 L\*, against none under H1.

[Inference: a six-month colour readout alone may not show why a transplant fails. That is why Study 3 pairs tissue markers with the colour measure.]

**Certainty levels:**

- **Level 0:** model only.
- **Level 1:** a frozen prediction tested against a photo series.
- **Level 2:** tested against biopsy markers.
- **Level 3:** tested against a transplant study's six-month readout after the final session.

**Everything to date is level 0.** Predictions P1 to P6 were frozen in `data/spot_model_predictions.csv` before any data. A later row, P4b, is marked as added after the first results.

## 7. Limits and open questions

**Limits.**

- **Search coverage.** PubMed, Europe PMC, ClinicalTrials.gov and data repositories only. Web of Science, Scopus and Embase were not searched.
- **Abstracts.** 11 of the 19 IGH treatment studies were read as abstracts only.
- **Paywalls.** Two IGH senescence letters are known only by title: PMID 36394380, "Melanocytes in idiopathic guttate hypomelanosis disappear and are senescent", and PMID 31823346, "Role of senescent fibroblasts in the development of idiopathic guttate hypomelanosis". H2 rests partly on the second.
- **Borrowed evidence.** Long transplant follow-up and every colour-match trial design come from vitiligo or other leukodermas. Vitiligo is immune-driven, and IGH is not known to be.
- **No clinical review yet.** Every ledger record passed an independent verifier against its source, but no dermatologist has reviewed this work.

**Open questions for a professional partner.**

1. What colour difference can people see on a 2 to 5 mm spot? That number sets the lasting-match threshold.
2. Are melanocytes in a spot missing (Wilson, Wallace) or present but immature (Hirobe)? The answer decides between replacing cells and activating the ones there.
3. Does the dermis under a spot differ from the dermis just outside it?
4. Do melanocytes inside a spot carry more DNA damage than those just outside?
5. Could IGH spots be added to a registered leukoderma transplant trial such as NCT07662915, with colour read six months after the final treatment?

## Where each claim comes from

| Topic | File | Status |
|---|---|---|
| Treatment evidence and counts | `data/evidence.csv`, `content/evidence-summary.md` | merged |
| Measurement tool and simulations | `content/measurement-tool-plan.md`, `content/experiments.md` | merged |
| Experimental directions | `content/frontier-scan.md` | merged, leads only |
| Glare simulation | `experiments/drift_sim_v2.py` | unmerged, PR 18 |
| Funding and ethics checks | `content/external/funding-sources-2026-11-27.md`, `ethics-regulatory-2026-11-27.md` | unmerged, PR 20 |
| Colour-match trials check | `content/external/colour-match-trials-2026-11-27.md` | unmerged, PR 21 |
| Tissue markers check | `content/external/tissue-markers-2026-11-27.md` | unmerged, PR 24 |
| Spot model | `content/spot-model-plan.md`, `data/spot_model_m4_*.csv` | unmerged, PR 29 |
| Damage scan | `content/damage-scan.md` | unmerged, PR 31, leads only |
