# Plan: a spot colour-match measurement tool

Status: planning document for Ben's review, 27 November 2026. Nothing here is built yet. Not linked from the site (`site.json` does not list it) and not for publication until Gate B.

SIMULATION AND PHANTOMS ONLY inside this repository. Every example below uses synthetic shapes. No patient images, now or later (CLAUDE.md rule 7).

## 1. Why this tool

The ledger cannot answer the core question because no study in it measured it. `python3 tools/ledger.py check` on main (27 November 2026) prints `lasting_color_match rows: 0` and a longest follow-up after the final treatment of 2.0 months on IGH rows (shin2013, goldust2013). Every included study grades repigmentation by eye on a percentage or quartile scale.

What is missing is an instrument: a repeatable number for "how well does this spot match the skin around it", with a known noise floor, that can be taken from photographs months apart. The two simulations in this repository already show which parts of that instrument are easy and which are hard:

- Lighting and white-balance drift are easy. Dividing each colour channel by the ring of skin around the spot cancels a uniform exposure or white-balance change to noise level (`data/drift_sim_results.csv` line 5: 0.16 points mean absolute error under a 20% darker exposure, against 0.13 with no drift at all, line 2).
- Outline placement is hard. The same correction does nothing for a misplaced outline: 0.25 mm on a 2 mm white spot reads as 9.9% false fading with or without it (lines 12 and 13), and 2.33% on an 8 mm spot (line 162). Mottled skin adds spread: at 0.5 mm on a 2 mm spot, SD 0.2 points on even skin (line 22) against 4.44 on mottled skin (line 202).

So the plan below spends most of its effort on registration, and treats colour calibration as a solved-in-principle problem that still needs checking against the cases the simulations did not cover (gradients, glare, the yellowness channel).

## 2. The measurand

### 2.1 Definitions

All quantities are computed per capture, per spot, from a linear-RGB image (raw or a demosaiced linear export; never a JPEG with a tone curve applied, see 3.3).

1. **Colour space.** CIELAB, D65, computed from linear RGB after card calibration (3.2). This is what `experiments/drift_sim.py` already uses (`rgb_to_lab`).
2. **Spot region S.** A fixed-radius disc centred on the registered spot centre (section 4), radius `r_S` chosen once per spot at baseline and never redrawn. Candidate rule to test: `r_S = 0.6 × baseline radius`, so a centring error up to about 0.4 × radius minus blur keeps S inside the spot. This is a proposal, not a result: no simulation has tested it yet (task T2).
3. **Reference ring R.** Annulus centred on the same point, starting 1.0 mm outside the baseline spot edge, 1.5 mm wide (the values both simulations use, `RING_GAP_MM`, `RING_WIDTH_MM`). Pixels flagged as hair, glare or another spot are excluded from R and the exclusion fraction is reported.
4. **Contrast vector.** `C = mean_Lab(S) − mean_Lab(R)`, giving ΔL*, Δa*, Δb*.
5. **Primary number: lightness contrast ΔL\*** in L* units (a white IGH spot has ΔL* > 0). Report the absolute value in L* units first, and percentage change from baseline second. Units matter: the simulations report percentage change only, which hides how small the noise is in absolute terms (the simulated white spot is +12.1 L* above skin, so line 2's SD of 0.16 points is about 0.02 L* units, far below anything a real camera will achieve).
6. **Secondary numbers: Δb\*** (yellowness) and the total colour difference ΔE (CIEDE2000 between mean S and mean R). ΔE alone is not enough because it cannot tell a spot that is still white from one that has overshot to dark; the signed ΔL* can (alignment simulation `dark_overshoot` rows).
7. **Residual contrast ratio** `ρ(t) = ΔL*(t) / ΔL*(baseline before treatment)`. ρ = 1 is unchanged, ρ = 0 is a perfect lightness match, ρ < 0 is overshoot to darker than skin.
8. **Spot area A(t)**, measured separately by segmentation (section 4.3) and reported beside ρ, because a fixed disc cannot see shrinkage from the edge inward. The alignment simulation shows why both are needed: an outline redrawn around whatever is still light hides a 51% loss, reading −4.1% (`data/alignment_results.csv` line 28), while contrast times outlined area recovers it (−52.5%, line 29).
9. **Absolute ring colour** `mean_Lab(R)` after card calibration. Ring normalisation erases it, but it is the only way to see the surrounding skin tanning or fading: in the alignment simulation a 5-unit darkening of nearby skin raises contrast by 33.3% with the spot unchanged (line 50), and only the reference lightness shift (−5.0) reveals the cause.

### 2.2 Uncertainty for one number

Per session, take k = 3 captures (lift the phone, reposition, re-shoot). The session value is the mean of the k measurements; the within-session standard deviation `s_w` is reported with it. The repeatability figure that matters is between sessions, so the validation ladder (section 5) estimates `SEM` (standard error of measurement) from repeat sessions of an unchanged target, and from it the **smallest detectable change** `SDC = 1.96 × √2 × SEM`. A change between two sessions counts as real only if it exceeds SDC.

### 2.3 What would count as a lasting match

Proposed definitions, for Ben to accept or change (open question 1):

- **Lasting colour match** at a spot: at a visit at least 6 months after the final treatment, |ΔL*| ≤ `T_match` and |Δb*| ≤ `T_match_b`, and the 6-month value does not differ from the first post-treatment value by more than SDC in the fading direction.
- `T_match` should come from what people can see, not from the instrument. Until a perception source is quoted in the ledger, any number here is a lead in brackets: a working placeholder of [ΔL* ≤ 2 units] is used only to size the targets below.
- The instrument is good enough only if SDC is well below `T_match`. Target: **SDC ≤ 1.0 L\* unit and ≤ 5% of baseline contrast, at 2 mm**, so a spot that regains half its contrast (the alignment simulation's `genuine_fading` case, −50%) is ten times the noise.
- This target is the project's own design target, not a published figure. A search of existing methods (the external report in `content/external/gpt-measurement-tools-2026-11-27.md`, checked 2026-11-28) found no method that reports an L\* or ΔE smallest detectable change over time for spots this small. The closest checked figure is a contact spectrophotometer on facial skin, 0.63 ΔE\*ab between readings when the probe is lifted and replaced, in one session (Wang et al. 2018, doi 10.1002/col.22230, Table 1). Rung 2 confirms or revises the target. If the measured SDC lands between 1 and 2 L\* units, the plan says so and the six-month analysis uses the measured value.
- The partial / complete / lasting distinction of CLAUDE.md rule 4 maps onto the tool as: partial = ρ decreased by more than SDC; complete area coverage = A fell to below the segmentation's detection limit; lasting colour match = the definition above.

## 3. Capture protocol

Each requirement names the error source it controls and whether a simulation in this repository already quantifies that error.

| # | Requirement | Error source controlled | Quantified so far? |
|---|---|---|---|
| C1 | Fixed working distance by a spacer (a printed cone, or a phone clip-on macro lens with a contact ring) giving at least 20 px/mm on the skin | scale and resolution: both simulations assume 20 px/mm and 0.1 mm blur | Assumed, not varied. Task T3 varies px/mm and blur |
| C2 | Colour and scale card in every frame, beside the spot, in the same plane (open question 3: which card) | exposure and white-balance drift; absolute ring colour (2.1 item 9); scale | Uniform drift: yes, ring normalisation alone handles it (drift CSV line 5). Absolute ring colour: alignment CSV line 50 shows why it is needed. Card-based correction itself: not simulated |
| C3 | Lighting from the device only (ring light or phone torch), room lights off or constant, no window | lighting gradients and mixed illuminants | **Not covered.** Drift sim assumes uniform exposure, no gradient (its docstring). Task T1 |
| C4 | Cross-polarised capture (linear polariser over the light, crossed polariser over the lens) if affordable; otherwise a fixed light angle and a glare mask | specular glare on skin, which is brighter than any white spot and would read as spot | **Not covered.** No simulation has glare. Task T1 adds a specular patch case |
| C5 | Raw (DNG) capture or a linear export; manual or locked exposure, ISO and white balance; no beauty filters, HDR or scene modes | tone curves and per-image processing that ring normalisation cannot undo (it is only exact for a linear, per-channel gain) | **Not covered.** Both simulations assume linear RGB. Task T1 adds a gamma/tone-curve case |
| C6 | Camera axis perpendicular to skin, fixed by the spacer of C1 and checked by the card's shape in frame. Camera angle is a large error source: in a phone study on printed skin-tone swatches, changing the angle gave L\* standard errors above 5 units in one experiment, against about 1 unit for distance (Cronin et al. 2023, doi 10.1002/jbio.202200381) | perspective foreshortening, which turns a disc into an ellipse and biases a fixed disc | Not covered |
| C7 | Landmarks at each session: two or more skin-safe fiducial dots, or a printed ring sticker (section 4.1), plus a body-site photo at arm's length for finding the spot | outline misplacement between sessions | **Quantified, and the dominant error**: 9.9% false fading at 0.25 mm on 2 mm (drift CSV line 12) |
| C8 | Same limb position (forearm prone on a table, elbow at a marked point) | skin stretch and curvature changing the spot's shape | Not covered |
| C9 | k = 3 repositioned captures per session; session log of date, time, device, settings, sun exposure in the past week | within-session variability; ring skin tanning (seasonal) | Within-session: not measured, comes from phantoms (rung 2). Seasonal tanning: alignment CSV line 50 shows the size of effect a 5-unit tan has |
| C10 | Exclude a capture automatically when the card is not found, the ring is more than 20% masked, or registration confidence is low | silent failures | The alignment simulation already shows the right behaviour for one case: a traced outline on an overshoot spot rejects all 200 captures instead of returning a number (lines 40, 41) |

**Kit note (2026-11-28, Ben's go-ahead 02:04 UTC).** Whatever camera is chosen, the rigid spacer or small copy stand that fixes both distance and angle (C1, C6) is part of the kit from the first session, not an add-on for later. Do not buy a contact spectrophotometer such as the Konica Minolta CM-700d as the main instrument: its smallest skin-tested aperture is 3 mm (Wang et al. 2018), larger than a 2 mm spot, and it costs about $6,750 at a reseller. Borrowing one for a single session to anchor phantom and card colours (open question 4) is still worthwhile.

Phone or camera: either can work if C1, C2 and C5 are met. A phone that exports DNG with manual exposure and white balance is the cheapest route; device choice is open question 2.

## 4. The hard problem: placement and registration between sessions

The aim is to place S and R on the same skin at every session. The target, from 2.3, is a placement error small enough that its false change is below SDC. From the drift simulation, false fading on a fixed outline is 9.9% at 0.25 mm and 26.0% at 0.5 mm on 2 mm (lines 12, 22), and 2.33% and 6.19% on 8 mm (lines 162, 172). So **a traced outline needs centring to well under 0.1 mm on a 2 mm spot**, which is not realistic by hand. Each approach below has a test that would show whether it reaches the target.

**Stated target for every approach: false change on an unchanged synthetic spot ≤ 2% mean and ≤ 1 point SD on mottled skin, at 2 mm and 0.5 mm initial misplacement, together with sensitivity to a true −50% fading within ±2 points.**

### 4.1 Fiducials around the spot

A printed ring sticker (a thin annulus of known inner diameter, with an orientation tick), or three small skin-marker dots, applied around the spot for the capture and removed after. The sticker defines the centre in every capture independently of the spot's own appearance.

- Strength: does not depend on the spot being visible, so it works when the spot has faded, which is exactly when image-based registration fails.
- Weakness: reapplying the sticker in exactly the same place is itself a placement error. A sticker is only a capture aid unless something on the skin persists between sessions.
- Test: (a) simulation T2 with fiducial-detection noise; (b) phantom rung 2, sticker removed and reapplied 10 times by Ben, centre measured against the phantom's printed true centre. Pass: reapplication SD ≤ 0.1 mm.

### 4.2 Landmark-based registration on the surrounding skin

Register each capture to the baseline using texture outside the spot: skin lines, pores, freckles, other spots, using feature matching or the FFT cross-correlation already in `alignment_pixel_sim.py` (`estimate_shift`), but computed on the ring and beyond, not on the spot.

- Strength: no consumables; works on photographs taken without a sticker.
- Weakness: needs texture, and mottled texture is the case where the simulations already show the most scatter (drift CSV line 202). The alignment simulation's registration locked onto the spot itself and removed the bias completely in a flat scene (alignment CSV line 7, mean absolute error 0.2 points at 0.25 mm); registering on the spot is not acceptable for the real tool because a spot that changes moves the registration with it.
- Test: simulation T2, registration restricted to pixels outside the ring, on mottled texture with a changed spot. Pass: the stated target.

### 4.3 Automatic segmentation

Find the spot edge at each session (threshold, active contour, or a trained model) and measure inside it.

- Use it for area A(t) only, never for colour. The alignment simulation shows a redrawn outline hides shrinkage in mean contrast (−4.1% for a −51% true change, line 28) and fails outright on overshoot (lines 40, 41).
- Test: simulation T2 shrink and overshoot cases; phantom rung 2 with printed spots of known area. Pass: area error ≤ 10% at 2 mm.

### 4.4 Fixed-radius disc centred by registration (recommended primary)

Combine 4.1 or 4.2 for centring with the fixed inner disc S of 2.1 item 2. Because S is smaller than the spot, a centring error shifts S within the spot and changes nothing until S reaches the edge. The tolerance is set by geometry: with `r_S = 0.6 r`, the disc stays wholly inside the spot for shifts up to `0.4 r − blur` (about 0.3 mm on a 2 mm spot at 0.1 mm blur). This is an untested prediction from geometry; task T2 tests it.

- Weakness: S sees only the centre. A spot that repigments from the edge inward or in dots keeps a white centre and reads as unchanged until late. Pair it with A(t) (4.3) and report both.
- Test: simulation T2. Pass: the stated target, plus the disc's false change on an unchanged spot is below the noise floor at every shift up to 0.3 mm on 2 mm.

## 5. Validation ladder

Each rung has a pass or fail criterion. A rung must pass before work on the next begins. Tests are written before code, as `.claude/agents/test-author.md` requires.

### Rung 1: extended simulation (in this repository)

Synthetic shapes only. Extends `experiments/drift_sim.py`; does not change its tests.

| Case to add | Why | Pass criterion |
|---|---|---|
| Lighting gradient (linear ramp across the field, 5% and 20% end to end) and vignetting | C3; ring normalisation assumes the ring sees the same light as the spot | Ring-normalised false change ≤ 1% at 20% gradient, or the gradient size at which it exceeds 1% is reported |
| Yellowness channel b* reported for every row, and a and ΔE | drift CSV is L only (column `channel` is `L` in all 720 rows) | b* false change under ring normalisation within the same tolerance as L* |
| Changed-spot cases (contrast ×0.5, ×0, ×−1/3; diameter ×0.7), as `alignment_pixel_sim.py` has | sensitivity, not just false change | Measured change within ±2 points of the true change at zero misplacement |
| Non-linear capture (gamma 2.2 then a gain) | C5 | Shows the size of error when a JPEG is used; no pass threshold, it documents why C5 exists |
| Specular glare patch in ring or spot | C4 | Glare mask detects ≥ 95% of glare pixels; with mask, false change ≤ 1% |
| Fixed inner disc S and registration on the ring only (4.2, 4.4) | the hard problem | The stated target in section 4 |
| Absolute units: every row also in L* units, and SDC computed from the trial spread | 2.2 | Reported, no threshold |

Fail: any case misses its criterion. Then the protocol requirement it tests stays mandatory and the plan says so.

### Rung 2: physical phantoms (Ben, by hand; derived numbers committed)

Printed or painted targets with known colour differences: discs of 2, 3, 5 and 8 mm in a graded series of lighter tones on a skin-tone field, some on a printed mottled texture, plus discs of reduced contrast standing in for "repigmented" states. A colour card in frame. Photograph:

- 10 sessions over at least 2 weeks, 3 repositioned captures each, on one device;
- the same phantom on a second device and under a second light;
- the sticker reapplied each session (4.1).

Pass criteria:
- SDC ≤ 1.0 L* unit and ≤ 5% of baseline contrast for the 2 mm disc on one device;
- between-device bias ≤ SDC after card calibration;
- measured contrast difference between phantom tones within ±1 L* unit of the difference measured by a reference instrument, if one can be borrowed (open question 4), or of the printer's own measured patches otherwise.

Phantom images contain no person and may be committed if small; the preferred route is still to commit only the derived CSV and keep images in `papers/`-style ignored folders.

### Rung 3: real skin (only later, outside this repository)

Not part of this plan's build. Recorded here so the boundaries are clear:

- Photographs of skin never enter this repository, not in commits, not in pull requests, not in `/mnt/project-files/`. They stay on Ben's own device or storage. The tool runs locally and only derived numbers (session date, spot code, ΔL*, Δb*, ΔE, A, ring colour, capture-quality flags) are committed, under codes that do not identify a person.
- First real-skin step is Ben photographing an unchanged spot on his own skin, untreated, for repeatability only (SDC on real skin). That is Ben's choice to make.
- **Photographing anyone other than Ben needs their informed consent and probably ethics advice (an institutional review board or research ethics committee) before it starts, and possibly data-protection rules depending on where they live. That decision is Ben's, and nothing in this plan starts it.**
- Treatment is out of scope for this repository: the tool measures; it does not recommend or deliver anything.

## 6. Build sequence

One unit per task, tests before code, each with an input, an output path and a done criterion. T1 to T3 can start now; they need nothing from Ben.

| Task | Role | Input | Output path | Done when |
|---|---|---|---|---|
| **T1** Spec and tests for drift-sim v2: gradients, vignetting, b*/a*/ΔE channels, changed-spot sensitivity, gamma, glare | test-author | this plan section 5 rung 1; `experiments/drift_sim.py` interface | `experiments/tests/test_drift_sim_v2.py` | tests committed and fail against current code; `git diff --exit-code <commit> -- experiments/tests` becomes the builder's contract |
| **T2** Spec and tests for placement strategies: fixed inner disc, registration on ring-only texture, sticker centring with detection noise, segmentation for area | test-author | sections 2.1 and 4; `experiments/alignment_pixel_sim.py` | `experiments/tests/test_placement_sim.py` | tests committed and fail; each test states its tolerance and why |
| **T3** Prior-art search, logged, one query set (section 7) | searcher | section 7 list | `data/search_log.csv` rows, `data/prior_art_screening.csv` | every query logged with date, source and hit count; no tool described without a link |
| T4 Implement drift-sim v2 to T1's tests | builder thread (no role file, as for PR #5) | T1 tests | `experiments/drift_sim_v2.py`, `data/drift_sim_v2_results.csv` | T1 tests pass unchanged; full run reproducible from the stated seed |
| T5 Implement placement sim to T2's tests | builder | T2 tests | `experiments/placement_sim.py`, `data/placement_sim_results.csv` | T2 tests pass unchanged; section 4 target met or the failing case named |
| T6 Write up rung 1 results | main session | T4, T5 CSVs | `content/experiments.md` new section, every number cited by CSV line | each number in the text appears in the CSV at the cited line |
| T7 Phantom design file (printable PDF/SVG of discs, mottled field, sticker ring) | builder | rung 2 spec | `experiments/phantoms/phantom_v1.svg` and a generator script | generator test checks disc sizes and tone steps in the output; synthetic shapes only |
| T8 Measurement pipeline skeleton: card detection, linearisation, registration, S/R measurement, quality flags, CSV out; runs on synthetic renders from drift_sim | test-author then builder | sections 2 to 4 | `tools/spotmeter/`, `tests/test_spotmeter.py` | passes on synthetic renders with known answers; refuses (does not guess) on missing card or low registration score |
| T9 Analyse phantom sessions | main session | Ben's derived CSV from rung 2 (images stay on his device) | `data/phantom_repeatability.csv`, `content/experiments.md` section | SDC and between-device bias computed; rung 2 pass or fail stated |

### What Ben needs to do by hand

1. **Decide** the open questions in section 8 (especially 1 to 3), ideally before T4.
2. **Buy** a colour reference card with a scale (open question 3), and if going cross-polarised, a clip-on macro lens plus two linear polariser sheets. Budget is his call; no product is recommended here until T3 finds and links options.
3. **Print** the T7 phantoms on the printer he will keep using (colour management off or fixed), and keep the prints flat and out of sunlight.
4. **Photograph** the phantoms on the rung 2 schedule (10 sessions over 2 weeks, 3 captures each, plus a second device and light), and run the T8 pipeline locally, committing only the derived CSV.
5. **Later and optionally**, decide whether to photograph an untreated spot on his own skin for real-skin repeatability, kept off the repository.

## 7. Prior art to check before building

Nothing below is claimed to exist. T3 searches each item, logs the query and links what it finds; anything not linked stays unverified.

- **Clinical colorimetry and reflectance devices** used in pigmentation research (tristimulus colorimeters, spectrophotometers, narrow-band reflectance "melanin/erythema index" meters): typical repeatability figures and published smallest detectable changes, which would set `T_match` and the SDC target.
- **Checked so far (2026-11-28; details in `content/external/gpt-measurement-tools-2026-11-27.md`, Appendix 1).**
  - Wang et al. 2018, *Color Res Appl*, doi 10.1002/col.22230: open access, read in full. It is the contact-instrument baseline. Konica Minolta CM-700d on 11 subjects' forehead and cheekbone: mean short-term repeatability of 0.37 ΔE\*ab with continuous readings and 0.63 with the probe replaced. Changing the aperture between 8 mm and 3 mm shifted readings by 2.48 to 3.04 ΔE\*ab. Differences between body sites were larger than the instrument's repeatability.
  - Cronin et al. 2023, *J Biophotonics*, doi 10.1002/jbio.202200381 (PMC10247498): raw files had lower median variability than JPEG, distance affected L\* only, angle affected all channels, and flash did not generally help. The targets were printed swatches, not skin.
  - PDFs to obtain (paywall list in `STATUS.md`): Vander Haeghen & Naeyaert 2006, PMID 16415385, the whole-process error of card-calibrated clinical photography; Navarro et al. 2019, PMID 29993849, the registration error between dermoscopic images.
- **Perceptibility thresholds** for skin colour differences (ΔE or ΔL* that observers notice on skin), as quotable sources for `T_match`.
- **Dermoscopy and total-body-photography software** that registers lesions between visits: how they align images, whether they report colour change, and what accuracy they publish.
- **Vitiligo area and colour scoring tools** (area indices, image-based repigmentation scoring, smartphone vitiligo apps): the closest existing field, with repigmentation as the outcome; check whether any report a colour-match measure with repeatability.
- **Image-based IGH measurement** specifically: any study in the screening log or beyond that used colorimetry or calibrated photography on IGH.
- **Open-source colour-calibration libraries** (colour-checker detection and correction, raw processing to linear RGB) and **registration libraries** (feature matching, phase correlation), with licence noted.
- **Standards and guidance on clinical photography and colour reference cards** in dermatology.

## 8. Open questions for Ben

1. Accept the proposed measurand (signed ΔL* in a fixed inner disc minus ring, with Δb*, ΔE and area beside it), and the working target SDC ≤ 1.0 L* unit at 2 mm?
2. Which device will be used for every capture: a specific phone with DNG export, or a dedicated camera?
3. Which colour card, and is cross-polarisation in the budget?
4. Can a reference instrument (a colorimeter or spectrophotometer) be borrowed for one phantom session, to anchor the phantom tones?
5. Is the long-term aim a tool only for Ben's own records, or one others could use? That changes how much effort goes into the pipeline's interface and into consent and ethics questions.
6. Should the T7 phantom also cover brown spots (Module 2's target), or stay white-spot only until Module 1 closes?
