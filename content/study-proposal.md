## Study proposal: a six-month colour-match follow-up for IGH

<p class="notice"><strong>Status: design sketch for discussion, 27 November 2026.</strong> This is a research design sketch written for Ben to react to and later discuss with clinicians. It is not a protocol ready for ethics review, it is not medical advice, and it does not recommend that anyone undergo any treatment. Every number about published studies below is quoted from the project's evidence ledger (<code>data/evidence.csv</code>, quotes in <code>data/evidence_quotes.jsonl</code>), cited by study_id. Numbers from the project's own simulations are labelled as such. Numbers in [square brackets] are inferences. Results are never pooled across studies. This page is not listed in <code>site.json</code>, so it is not part of the public site build.</p>

### 1. The question this study would answer

Which treatment helps a small idiopathic guttate hypomelanosis (IGH) white spot match the surrounding skin, and does that match last at least six months after the **final** treatment?

The study keeps the project's three outcomes separate throughout: partial repigmentation, complete area coverage, and lasting colour match. Only the third answers the core question.

### 2. The gap, in the ledger's own words

As of main at merge 679f20c (54 rows, 21 studies), `python3 tools/ledger.py check` prints:

```
longest months after final treatment, IGH rows: 2.0
lasting_color_match rows: 0
```

What that means, study by study:

- **No ledger row measures a lasting colour match.** Zero rows carry the `lasting_color_match` tier. The best-reported tiers are partial repigmentation, an instrument colour reading, a lesion count, or an unquantified description.
- **The longest quoted gap after a final treatment on an IGH row is two months**, in two single-session fractional CO2 laser studies, both counting patients and both reporting partial repigmentation:
  - shin2013: "Two months after a single treatment, physicians' clinical assessments were performed and the patients' overall satisfaction was evaluated."
  - goldust2013: "Two months after a single treatment session, 115 patients (47.9%) exhibited more than 75% clinical improvement."
  - The two abstracts share that methods sentence word for word. STATUS.md lists this as a possible text-reuse question for Ben.
- **Most studies count time from the start of treatment, not from the final treatment**, so the ledger records `NOT_DERIVABLE` for them. Examples:
  - laosakul2017: "Colorimeter was used to measure lesional luminosity at baseline and then monthly until 4 months."
  - rerknimitr2013: "Colorimeter was used to assess skin colour at baseline and at 1, 2, 3, 4 and 6 months of treatment."
  - ravikiran2014: "Patients were assessed both subjectively and objectively after every session and at the end of 3 months of initiation of therapy."
  - rajegowda2021 reports results only "At the end of the treatment period".
- **The only durability observation in the ledger is a loss of effect, and it is not IGH.** pagnoni1999 (row recorded as ADJACENT, macular hypomelanosis): "Follow-up of 2 patients with MH a year after stopping tretinoin showed clinical regression of the macules to the original state." The authors add: "maintenance therapy may be required for durable effects."
- **Authors themselves name the gap.** deepadarshan2023: "The limitations of this study were the limited sample size and short follow-up period". ravikiran2014: "Comparison with control and further follow up may add more information about its use."

### 3. Why the measurement has to be designed first

Most ledger endpoints are physician grades of "improvement" against baseline. None compares the spot with the skin around it at a fixed time after the final treatment. The few instrument readings report only P values:

- rerknimitr2015: "continued to decrease until 4 weeks' follow-up (week 16) (P = 0.047, 0.016 and 0.06 respectively)." No arm values or units are in the abstract.
- rerknimitr2013: "Mean luminosity scale after adjusted for baseline from the treated side gradually decreased and reached statistical significance compared with the control group after 6 months of treatment (P = 0.019)."
- laosakul2017: "the score of the treated lesions has been significantly lower than that of the control lesions since week 8 (p = .005)."

So the field has no spot-versus-surround colour difference with a spread, which is exactly what a sample-size calculation needs (section 7).

#### 3.1 Proposed endpoint

For each spot at each visit:

1. **Colour difference to the ring.** Mean colour inside the spot outline versus mean colour in a ring of nearby skin, expressed in CIELAB (a device-independent colour space) and summarised as the CIEDE2000 colour difference, ΔE00. The signed lightness difference ΔL\* is reported alongside, because a spot can overshoot to darker than its surroundings and ΔE00 alone does not show direction.
2. **Ring lightness on its own.** Reported separately, so a change in the surrounding skin is not mistaken for a change in the spot. pagnoni1999 is a reminder: "Interestingly, the surrounding skin showed a decrease in pigmentation."
3. **Residual spot area.** The area that still differs from the ring, measured with an integrated (area times contrast) method, so that shrinkage is not hidden.

A spot counts as a **lasting colour match** if its ΔE00 to the ring is below a pre-stated threshold at the visit six months after its final treatment, with no dark overshoot. The threshold itself is an input the study must set before it starts (section 7.2). It is not in the ledger and is not invented here.

#### 3.2 What the project's simulations already show

These are simulations on synthetic disks on a uniform background. They test the measuring method, not any treatment, and contain no patient images (`content/experiments.md`).

- **A fixed outline fakes fading.** In `data/alignment_results.csv`, an unchanged 2 mm spot with the outline placed 0.25 mm off reads as −10.0% change (`unchanged, 2.0, 0.25, fixed_misaligned`). At 0.5 mm it reads −26.1%. The closed-form check in `experiments/alignment.py` and `data/alignment_validation.csv` gives 15.874% for the sharp-edged 2 mm, 0.25 mm case, so the formula is a worst case.
- **Re-registering the outline removes that bias** in the simple scene: −0.0% for the same case (`registered`).
- **Redrawing the outline around whatever is still light hides shrinkage.** A spot that lost half its area (true change −51.0%) reads −4.1% with `traced_mean`, and −52.4% with `traced_integrated` (2 mm, 0.25 mm). The endpoint therefore uses a registered outline and an integrated measure.
- **A traced outline correctly fails on dark overshoot.** All 200 captures were rejected (`dark_overshoot, traced_mean, rejected 200`). The registered outline measures it (−133.3% true, −133.3% measured). Dark overshoot is therefore a measured outcome, not a missing value.
- **Darkening of nearby skin changes contrast by a third** (true 33.3%) while the spot is unchanged, and the reference ring's lightness shift of −5.0 units is what reveals it. That is why ring lightness is reported on its own.
- The pixel model `experiments/alignment_pixel_sim.py` already places the reference ring 1.0 mm outside the outline with a 1.5 mm width (`RING_GAP_MM = 1.0`, `RING_WIDTH_MM = 1.5`). The proposal adopts that geometry as a starting point, to be checked in the phone repeatability test.

**In progress, results not stated here:** a drift simulation (lighting and white-balance drift, 2 to 8 mm spots, ring normalisation) is being built on a separate branch. `experiments/drift_sim.py` is not on main as of this draft. Its results should decide how tightly lighting must be controlled and whether ring normalisation is enough on its own.

Limits the simulations state themselves: one spot, flat uniform skin, no hair, no curvature, no lighting gradient. Real captures will be worse.

#### 3.3 Photography protocol (sketch)

- Same camera model and settings at every visit, fixed working distance with a spacer, cross-polarised light from a fixed source, and no room light where possible.
- A grey reference and a small colour chart in the same plane as the skin in every frame, plus a millimetre scale. Colour is converted to CIELAB from the chart in each frame, then measured against the ring, which corrects most of what remains.
- Fiducial marks or a body-map position so the outline can be re-registered at each visit.
- Before any patient is enrolled, run the engineering task already written in `content/open-questions.md`: a printed matte target with 2, 3 and 5 mm dots, 10 fully repositioned photographs per session, repeated on a second day and phone. That gives the measurement error of the whole chain with no skin involved.
- **No patient images go into this repository** (rule 7). Study images would stay with the clinical site under its own consent and data rules.

#### 3.4 Blinded assessment

- The primary endpoint is computed by software from the photographs, using a fixed, versioned script, with outlines registered blind to allocation.
- A secondary rating by at least two assessors who do not know the allocation or the visit, viewing crops of spot plus ring in random order, with "can you see where the spot was?" as the question. This feeds the `patient_noticeability` and observer-match outcomes and helps calibrate the ΔE00 threshold.
- Assessor blinding is weak when treatments leave visible marks. Several ledger rows report scabbing or post-inflammatory hyperpigmentation (for example deepadarshan2023: "hyperpigmentation was noted in 18 (9%) macules which persisted at 4th month of follow up."). This is one more reason the primary endpoint is computed rather than graded, and why the six-month visit is far from the last session.

### 4. Design choices, each answering a weakness in the ledger

| Weakness recorded in the ledger | Design answer |
|---|---|
| Time counted from baseline; date of each spot's final session not reported (deoson2025: "The procedure was repeated at monthly interval up to 3 sittings till complete repigmentation was achieved."; rajegowda2021: "once in a month till the repigmentation for maximum of 3 applications") | Fixed number of sessions per arm, no stopping early once a spot looks repigmented. Record the date of every session for every spot. The primary visit is six months after that spot's final session. |
| No untreated spots, yet untreated or sham spots changed where they were measured (see 4.1) | Every patient has at least one untreated control spot, and a sham where the procedure allows one. |
| Spots analysed as independent (deoson2025: "30 patients with each group containing 15 patients and 5 macules in the pre – tibial region of each patient were selected."; koh2018: "A total of 122 lesions were analyzed from 18 patients") | The patient is the unit of analysis. Spots are clustered within patients and analysed with a mixed model with a patient random effect. Per-patient results and the within-patient correlation are published. |
| Results depend heavily on the clustering assumption | `data/clustering_sensitivity.csv` (calculation on deoson2025 Table 1): the cryotherapy minus TCA difference of 18.7 points has a 95% interval of 4.4 to 32.9 if spots are independent, and −1.5 to 38.8 at an assumed correlation of 0.25. The proposed study measures that correlation directly. |
| Primary endpoint not pre-stated; many outcomes, only P values | One pre-stated primary endpoint and time point, registered before enrolment with a written analysis plan. |
| Attrition not reported, or results only for completers (rajegowda2021: "A total of 30 patients with more than 10 IGH macules were selected." and "A total of 25 patients completed the study.") | A flow diagram of patients and spots at every visit, reasons for loss, and an intention-to-treat analysis with a stated method for missing six-month data. |
| Mostly facial spots in one study (shin2013: "The face was the most commonly treated area, although the extremities are epidemiologically the most frequently affected areas.") | Off-face sites only: forearms and shins. |
| Partial grades reported as success | The three outcomes are reported separately. A ">75% improved" grade is partial repigmentation. |
| Dark overshoot and scarring reported inconsistently | Signed ΔL\* captures overshoot; texture and scarring are recorded per spot and per patient, with both denominators stated. |

#### 4.1 Why the control spot is not optional

Where ledger studies measured untreated or sham-treated spots, some of those spots changed:

- laosakul2017: "82.3% of the treated lesions comparing to only 2% of the control showed more than 75% improvement".
- rerknimitr2015: "83.34% of the lesions in treatment group vs. 18.34% in the control group showed some improvement."
- arbache2023, saline delivered with a tattoo machine on the other limb: "saline-treated limbs (baseline: 31, IQR 24-43 × post-treatment: 21, IQR 16-31, p = .000006)".
- elhoshy2025 (ADJACENT, not IGH): "Median peripheral tanning was observed in 80% of lesions in the microneedling arm versus 85% in the no-treatment arm."

One ledger source points the other way: pagnoni1999, "In Nivea-treated forearms, no changes in pigmentation, glyphic pattern, elastic values and histology were observed either in IGH or MH." Another asserts the opposite without a control: ravikiran2014, "Unlike in vitiligo, spontaneous repigmentation does not occur in any IGH lesions." The proposed study would settle this for its own sample rather than assume it.

#### 4.2 Within-person controls and their one risk

Within-person control spots remove differences between people (skin tone, sun habits, age) and make a small study far more efficient. Their risk is that treatment on one spot affects others: elhoshy2025's ledger rows note that the authors raise "a possible systemic effect of microneedling" (ADJACENT, not IGH), and arbache2023's saline arm was itself a needling procedure. Two mitigations:

- Put the control spot on the other limb, not next to the treated spot, and record the distance.
- If the budget allows, add a small group of patients who receive no procedure at all, photographed on the same schedule. That group shows natural drift without any possible spillover.

#### 4.3 Visit schedule (sketch)

| Visit | Timing |
|---|---|
| Screening and baseline photographs | before the first session |
| Each treatment session | photographs before treatment |
| End of treatment | at the final session |
| Intermediate | 1 and 3 months after the final session |
| **Primary** | **6 months after the final session** |
| Optional | 12 months after the final session |

Season matters. A six-month visit falls in the opposite season to baseline, and surrounding skin tans and fades through the year. The ring measurement captures that, but the match itself may look different in summer and winter. A 12-month visit compares like season with like season. Recording sunscreen use and sun exposure at each visit is part of the design.

### 5. Candidate arms, as the ledger describes them

This table describes what the ledger rows show for each intervention family. It does not rank them, and nothing here is a recommendation to use any of them. "Months after final treatment" is the value in the ledger's `months_after_final_tx` column.

| Intervention family | Ledger studies | Best tier reached | Unit counted | Control in the study | Months after final treatment | Access |
|---|---|---|---|---|---|---|
| Cryotherapy (liquid nitrogen) | laosakul2017, deoson2025, rajegowda2021, ploysangam1990 | partial repigmentation; instrument colour (laosakul2017) | lesion | untreated lesions (laosakul2017); TCA in other patients (deoson2025); phenol in the same patients (rajegowda2021); none (ploysangam1990) | NOT_DERIVABLE in all four | deoson2025 full text; others abstract only |
| Chemical wounding (50% TCA, 88% phenol) | deoson2025, rajegowda2021, ravikiran2014 | partial repigmentation | lesion | cryotherapy (deoson2025, rajegowda2021); none (ravikiran2014) | NOT_DERIVABLE | deoson2025 and ravikiran2014 full text; rajegowda2021 abstract only |
| Ablative fractional laser (CO2, Er:YAG) | shin2013, goldust2013, koh2018 | partial repigmentation (shin2013, goldust2013); unquantified (koh2018) | patient (shin2013, goldust2013); lesion, inferred (koh2018) | none (shin2013, goldust2013); the other laser and tretinoin (koh2018) | 2 (shin2013, goldust2013); NOT_DERIVABLE (koh2018) | abstract only |
| Non-ablative fractional 1550-nm laser, alone or with tacrolimus | rerknimitr2015, chitvanich2016 | partial repigmentation; instrument colour | lesion | control lesions on the other side | NOT_DERIVABLE | abstract only |
| 308-nm excimer laser or lamp | deepadarshan2023, gordon2017, kreeshan2021 | partial repigmentation (deepadarshan2023, gordon2017); unquantified (kreeshan2021) | lesion; one patient (kreeshan2021) | none (deepadarshan2023); untreated lesions (gordon2017); bimatoprost patch (kreeshan2021) | 1 (deepadarshan2023); NOT_DERIVABLE or NOT_APPLICABLE otherwise | deepadarshan2023 and kreeshan2021 full text; gordon2017 abstract only |
| 5-fluorouracil delivered into the skin (tattoo machine or needle) | arbache2023, rambhia2020; leads arbache2018, wambier2018 not extracted | lesion count (arbache2023); unquantified (rambhia2020) | limb (arbache2023); not reported (rambhia2020) | saline with the same device on the other limb (arbache2023); none (rambhia2020) | 1 (arbache2023, from "30 days after treatment"); NOT_DERIVABLE (rambhia2020) | arbache2023 abstract and registry; rambhia2020 full text |
| Topical tacrolimus | rerknimitr2013 | instrument colour; partial repigmentation | side; patient | placebo ointment on the other side | NOT_DERIVABLE | abstract only |
| Topical tretinoin | pagnoni1999 (IGH and macular hypomelanosis pooled), koh2018 | partial repigmentation (pagnoni1999); unquantified (koh2018) | lesion; patient | moisturiser on the other forearm (pagnoni1999); lasers (koh2018) | NOT_DERIVABLE for IGH; 12 on an ADJACENT row, showing regression | pagnoni1999 full text; koh2018 abstract only |
| Microneedling alone | elhoshy2025 (ADJACENT, not IGH) | partial repigmentation | lesion or half-area | untreated half of the same area | 3, on ADJACENT rows only | abstract and registry |
| Melanocyte grafting | suvanprakorn1985 (mixed diagnoses) | unquantified | not in abstract | none | NOT_DERIVABLE | abstract only |

What the table supports, and what it does not:

- Several families have at least one within-person controlled study, so a within-person design is already feasible with them.
- No family has a row timed six months after the final treatment, and no family has a colour-match row. The table therefore cannot say which arm to pick on efficacy. Practical criteria (a fixed, short treatment course so that "final treatment" has one clear date; a credible sham; known local side effects) can narrow the choice, and that choice belongs to Ben and the clinicians.
- Single-session treatments make the final-treatment date unambiguous. In the ledger, laosakul2017 ("A single session of tip cryotherapy was delivered and remained for 5 s."), shin2013 and goldust2013 used one session.

### 6. Statistical analysis (sketch)

- **Primary analysis:** a linear mixed model of ΔE00 (spot to ring) at the six-month visit, with arm as a fixed effect, baseline ΔE00 as a covariate, and a random intercept for patient. The estimate of interest is the treated-minus-control difference within patients, with a 95% confidence interval.
- **Key secondary:** the share of **patients** whose treated spot meets the lasting-match definition, compared with the share whose control spot does.
- **Other secondaries:** ΔE00 at 1 and 3 months after the final session (does the match drift?); residual area; dark overshoot; texture and scarring; observer rating; patient rating.
- **Reported always:** the within-patient correlation of spot outcomes, so later studies can size themselves.

### 7. Sample size: what can and cannot be computed now

**It cannot be computed yet.** No ledger row has a quoted effect size, or a spread, on a spot-versus-surround colour endpoint. What can be written down is the formula and the list of missing inputs.

#### 7.1 Formula

For a within-patient comparison with one treated and one control spot per patient, the number of patients is approximately

  n = (z₁₋α/₂ + z₁₋β)² × σ_d² / δ² + z₁₋α/₂² / 2

where δ is the smallest treated-minus-control difference in ΔE00 worth detecting, σ_d is the standard deviation of that within-patient difference at six months, and the last term is a small-sample correction.

If each patient contributes m spots per arm, σ_d² is replaced by the variance of the patient-mean difference, which depends on the between-spot variance and the within-patient correlation ρ: roughly σ_d² × (1 + (m − 1)ρ) / m. More spots per patient help only when ρ is low.

To allow for loss to follow-up, divide by (1 − expected attrition).

For orientation only, the formula's arithmetic at α = 0.05 two-sided and 80% power, expressed in standardised units (δ/σ_d) rather than in colour units:

| δ/σ_d (standardised, not an IGH estimate) | patients, before attrition |
|---|---|
| 0.3 | 90 |
| 0.5 | 34 |
| 0.8 | 15 |

These are properties of the formula. They say nothing about what an IGH treatment does.

#### 7.2 Missing inputs and where each would come from

| Input | Status in the ledger | How to get it |
|---|---|---|
| δ, the smallest difference that matters | not measured: no ledger study reports a spot-to-surround colour difference | a perceptibility rating on study photographs (lay and expert viewers), which also sets the lasting-match threshold |
| σ_d, spread of the within-patient difference at six months | not reported: instrument rows give P values only (rerknimitr2013, rerknimitr2015, laosakul2017, chitvanich2016) | a pilot with six-month follow-up; until then, only measurement error can be bounded |
| Measurement error of the photo chain | not measured | the phone repeatability test (section 3.3) and the drift simulation in progress |
| Within-patient correlation ρ | not reported anywhere in the ledger; `data/clustering_sensitivity.csv` shows conclusions change between 0 and 0.25 | the pilot, analysed at the patient level |
| Attrition to six months after the final session | not reported for any six-month interval; the only quoted losses are over shorter studies (deepadarshan2023: "A total of 44 patients were recruited out of which 40 patients completed the treatment and 4 patients were lost to follow up.") | the pilot, or any existing cohort that is followed up |

#### 7.3 What a pilot would and would not do

A small pilot, with the same imaging and the same six-month visit, would estimate σ_d, ρ, attrition and the measurement error. It would not be sized to show that any treatment works, and its efficacy estimate should not be used as δ, because small pilots tend to overstate effects. The pilot's size should be set by how precisely it needs to estimate σ_d, which is a question for the clinicians and a statistician.

### 8. Lower-cost routes to six-month data sooner

| Route | What it could show | What it could not show |
|---|---|---|
| **Later follow-up of existing trials.** The authors of the controlled ledger studies (for example laosakul2017, rerknimitr2015, arbache2023, rajegowda2021) could in principle be asked whether any patients were seen again later. This is noted only as possible. No message is drafted or sent: Ben's rules stop at any contact with a researcher. | Whether their reported improvement persisted, in their own grading, for patients who returned | A colour match, if they never measured one; an unbiased answer, because patients who come back are self-selected; the date of the final treatment, if it was never recorded |
| **Prospective case series or registry with the same endpoint.** Clinics that already treat IGH use the same photo protocol and add a visit six months after the final session, photographing one untreated spot as well. | Durability of whatever each clinic does, on a valid colour-match endpoint, with natural drift measured on the untreated spot | A fair comparison between treatments, because choice of treatment is not randomised |
| **Natural-history series of untreated spots.** Photograph untreated IGH spots on the same schedule. | How much untreated spots drift over six months and across seasons, which is the control arm's behaviour and a direct input to σ_d | Anything about treatment |
| **Measurement validation without people.** The phone repeatability test and the drift simulation. | The measurement error floor and how much lighting control is needed | Anything about skin or treatment |

A reasonable order is: measurement validation, then a natural-history or registry series, then the controlled study sized from them. That is a suggestion for discussion, not a decision.

### 9. Open questions for Ben

1. Should the first study compare one treatment against an untreated control (smaller, clearer), or two treatments against each other plus a control?
2. Should arms be restricted to single-session treatments, so that "final treatment" has one unambiguous date?
3. Who defines a "match": lay viewers, dermatologists, or a ΔE00 threshold set from both in a rating exercise?
4. Is a separate no-procedure patient group worth the cost, to rule out spillover between spots on the same person?
5. Is a 12-month visit worth adding, so the final reading is taken in the same season as baseline?
6. Forearms, shins, or both?
7. Should the registry or case-series route come first, with the controlled study only after it supplies σ_d and attrition?
