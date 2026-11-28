## Experiments

### 1. How much fading can a misplaced outline fake?

<p><span class="tag sim">Simulation</span> Synthetic disks on a uniform background. No patient images. This tests the measuring method only.</p>

A common way to track a spot is to outline it at the first visit and measure the same outline later. If the outline lands slightly off at the second visit, part of it covers normal skin and the spot looks as if it faded.

{{alignment_widget}}

**Check of the starting formula.** The seed brief's closed-form result was rebuilt as a pixel image, with each pixel split into 64 sub-pixels, and measured directly.

{{validation_table}}

The two methods agree to within 0.04 percentage points whenever the outline is displaced. With no displacement, the pixel image reads 0.3 to 1.5% lower than the ideal, because edge pixels are part spot and part skin. The formula has no pixels, so it cannot show that.

**Five follow-up situations, four ways of placing the outline.** Each cell is 200 simulated captures at 20 pixels per mm, with noise and a 0.1 mm blur. The table shows the 0.25 mm displacement; the results file has 0 and 0.5 mm too.

{{results_table}}

What the simulation shows:

- **A fixed outline is biased by displacement in every situation.** With blur included, 0.25 mm on a 2 mm spot reads as 10% fading with nothing changed. The sharp-edged formula says 15.9%, so the formula is a worst case.
- **Re-registering the outline removes that bias** in this simple scene, including when the spot ends up darker than the skin.
- **An outline redrawn around whatever is still light hides shrinkage.** A spot that lost half its area reads as a 1 to 4% change in mean contrast. Multiplying contrast by outlined area recovers the loss.
- **A redrawn outline fails completely on a spot that overshoots to dark.** All 200 captures were rejected, which is the correct behaviour: it reports a failure and does not return a number.
- **Darkening of nearby skin changes contrast by a third** while the spot itself is unchanged. The separately measured reference lightness (down 5 units) is what reveals it.

Limits: one spot, flat uniform skin, no hair, no curvature, no lighting gradient, and registration that has only the spot to lock onto. Real captures will be worse.

{{reproduce_sim}}

### 2. Do spot-level results survive counting patients, not spots?

<p><span class="tag calc">Calculation on published counts</span> No new data. Counts are taken from two open tables.</p>

Studies treat five spots per person and analyse them as if they came from different people. Spots on one person tend to respond alike. The calculation below shrinks the sample size by a standard design effect for a range of assumed within-person correlations (0 = spots independent, 1 = all spots on a person respond identically).

{{clustering_table}}

The advantage of cryotherapy over 50% TCA is clear only if spots within a person are close to independent. At a correlation of 0.25 the interval already includes zero. The true correlation is unknown, and publishing per-patient results would settle it.

### 3. Do the published percentages fit the stated numbers?

<p><span class="tag calc">Calculation on published counts</span></p>

{{denominator_table}}

The audit covers every percentage in the ledger that is printed with a denominator, both quoted (70 pairs from 10 studies, `data/denominator_audit.csv`). Seven percentages, in four studies, do not correspond to a whole number of the stated lesions or patients: laosakul2017 (82.3% of 43 treated lesions), rerknimitr2013 (11% of 26 patients), goldust2013 (41.6% and 10.3% of 240 patients) and ravikiran2014 (35.9% of 139 macules; 41.5% and 13.4% of 89 repigmented macules). In three of them the paper also prints the count, and that count gives a slightly different percentage (100/240 = 41.67%, 25/240 = 10.42%, 50/139 = 35.97%). Five of the seven fit if the paper cut the decimals instead of rounding them; 82.3% of 43 and 10.3% of 240 fit neither way. Possible reasons are an evaluable number smaller than the one stated, a different unit being rated, or a rounding convention. Each is a question for the full text. Ten further percentages are not audited because the ledger gives no denominator for them, or only an inferred one in brackets (`data/denominator_not_audited.csv`); rerknimitr2015 is audited against the 120 lesions its abstract states, not the inferred 60.

{{reproduce_calc}}

### 4. Do lighting and white-balance changes fake a change in colour?

<p><span class="tag sim">Simulation</span> Synthetic disks on synthetic skin texture. No patient images. This tests the measuring method only; it says nothing about any treatment.</p>

The same spot is "photographed" twice. Between the two captures nothing about the spot changes, so the true change is 0% in every case and any change the method reports is false. The second capture can differ in four ways: the outline is misplaced (0, 0.25 or 0.5 mm), the exposure changes (20% darker or 25% brighter), the white balance changes (warmer or cooler), or both. Spots are 2, 3, 4, 5, 6 and 8 mm, either a white spot (like IGH) or a brown spot (like a sun spot), on even skin or on mottled skin (brightness varying by 5% in patches about 1 mm across). Each cell is 100 simulated pairs at 20 pixels per mm, with noise and a 0.1 mm blur. Colour is measured in CIELAB, pixel by pixel, as the spot's lightness minus the lightness of a ring of skin around it.

Assumptions: lighting change is the same over the whole picture (no gradient, no shadow, no glare). The only correction tested divides each colour channel by its average in the ring around the spot. The spot never changes.

What the simulation shows (row numbers are lines of `data/drift_sim_results.csv`):

- **A 20% darker exposure, uncorrected, reads as about 7% fading** of a spot that did not change, at every size (2 mm white spot: line 4, −7.16%; 8 mm: line 154, −7.15%). A 25% brighter exposure reads as about 7.7% more contrast (line 6, +7.74%).
- **The white-balance shifts tested move the lightness result by less than half a point** (lines 8, 370, 520: −0.23, +0.44, −0.40%). They matter more for the yellowness channel, which this table does not report.
- **Dividing by the skin ring removes lighting and colour drift** to within the noise: the 2 mm white spot under a 20% darker exposure reads 0.16 points mean error with the correction (line 5), against 0.13 with no drift at all (line 2).
- **The correction does nothing for a misplaced outline.** 0.25 mm on a 2 mm spot still reads about 10% fading with or without it (lines 12 and 13, −9.90%); on an 8 mm spot about 2.3% (line 162). When both happen, the errors add: −16.0% uncorrected and −9.5% corrected on a mottled 2 mm spot (lines 194 and 195).
- **Mottled skin makes misplacement errors unpredictable.** At 0.5 mm on a 2 mm white spot, the average false fading is similar (26.0% even, 25.3% mottled), but the spread between captures rises from 0.2 to 4.4 points (lines 22 and 202).

Limits: flat skin, one spot, uniform lighting, no hair, no curvature, a ring of clean skin around the spot. Real photographs will be worse.

```
python3 experiments/drift_sim.py --out data      # about 12 minutes
python3 -m pytest experiments/tests -q           # 35 tests, written before the code
```

### 5. Which way of placing the measurement survives a misplaced photo?

<p><span class="tag sim">Simulation</span> Synthetic disks on synthetic skin texture. No patient images. This tests the measuring method only; it says nothing about any treatment.</p>

The second photo of a spot is never framed exactly like the first. This simulation compares ways of putting the measurement back on the same skin when the follow-up photo is off by up to 0.5 mm. Two regions are measured: the full outline drawn at baseline, and a fixed inner disc at 0.6 of the baseline radius. Three ways of finding the follow-up centre are tested: none (measure where the frame is), lining up on the skin texture outside the spot and its gap only, and a sticker ring whose centring is off by a random amount (standard deviation 0.1 mm per axis by default). Outline detection is used for area only. The spot is either unchanged, fades to half its contrast, disappears, overshoots to darker than skin, or shrinks to 0.7 of its diameter. Each cell is 100 simulated pairs at 20 pixels per mm, with capture noise, 0.1 mm blur and 5% mottle. The plan's target (measurement tool plan, section 4), at 2 mm, 0.5 mm misplacement and mottled skin, is a false change of no more than 2% on average and 1 point of spread on an unchanged spot, plus a measured half-fading within 2 points of the truth.

What the simulation shows (row numbers are lines of `data/placement_sim_results.csv`):

- **With no correction, both regions fail.** The outline reads −25.4% on an unchanged 2 mm spot (line 290) and the inner disc −7.1% (line 291).
- **Lining up on the surrounding skin passes the target with both regions:** −0.17% mean and 0.33 spread with the outline, −0.07% and 0.43 with the inner disc (lines 292, 293). The half-fading reads −46.3% and −46.2%, against a true −46.7% and −46.5% (lines 796, 797).
- **The sticker at 0.1 mm error fails.** The outline reads −3.7%, spread 3.4 (line 294). The inner disc averages +0.25%, but its spread of 1.78 is above the target's 1 point (line 295).
- **Outline detection gets the area right:** −0.2% on the unchanged spot and +2.2% on the shrinking one, inside the 10% limit (lines 290 and 2306, column `area_error_pct`).
- **Lining up refuses when there is nothing to line up on.** On even skin with no texture, it refused every trial instead of guessing (for example line 40, 100 of 100 rejected).

How much two assumptions matter:

- **Sticker accuracy decides the sticker result.** On the same simulated photos, the sticker with the inner disc passes at 0 and 0.05 mm of centring error and fails from 0.1 mm on (`data/placement_sim_sticker_sensitivity.csv`, lines 5 and 7: spread 0.84, then 1.62). The plan's pass mark for re-applying a sticker by hand is 0.1 mm, so a sticker that only just meets that mark is not good enough here.
- **"Below the noise floor" (plan 4.4) holds under three of the four readings tried.** Up to 0.3 mm of misplacement, the inner disc's worst average false change is 0.20% with no correction, 0.04% when lined up on the skin and 0.19% with the sticker. All three are below the zero-shift spread, the plan's smallest-detectable-change form and the 2% limit. All three fail a standard-error floor (spread divided by the square root of 100), lining up on the skin by 0.0007 points (`data/placement_sim_noise_floor_sensitivity.csv`, lines 2 to 13).

Limits: this is the best case for lining up on the skin. The synthetic skin is identical between visits apart from noise: no hair, tanning, stretch, rotation, curvature or uneven lighting. The true change is measured on even skin, so texture effects count as measurement error. Real photographs will be worse, and the next test is the printed phantom (plan rung 2).

```
python3 experiments/placement_sim.py --out data            # about 18 minutes on 4 cores
python3 experiments/placement_sensitivity.py --out data    # about 10 minutes
python3 -m pytest experiments/tests -q                     # 55 placement tests, written before the code
```

### 6. Does lining up on the skin survive hair, tanning, rotation and uneven light?

<p><span class="tag sim">Simulation</span> Synthetic disks, synthetic skin texture and synthetic straight hairs. No patient images. This is a simulation result, not evidence: it tests the measuring method only and says nothing about any treatment. <strong>Every disturbance size below is the test author's assumption, chosen to bracket plausible conditions. None comes from a quoted source.</strong></p>

Section 5 tested lining up on the surrounding skin in its best case, with the same skin texture at both visits. This round adds four things that change between real photo sessions, one at a time and then all together: hair across the spot and ring (2 or 8 strands), tanning of the skin around the spot (2 or 5 L\* darker, evenly, or 5 L\* with a new 3 % patchy pattern), turning of the camera (2, 5 or 10 degrees) and uneven light (a 5 % or 20 % ramp across the field, or 10 % or 20 % fall-off towards the edges). Four placements are compared: none, lining up by sliding only, lining up by sliding and turning (new in this round), and the sticker (0.1 mm error). Each measurement is made with no hair mask and with hairs found automatically and left out. Tanning is a real change in how the spot contrasts with the skin, so it counts as truth; hair, turning and light do not. The test is the plan's section 4 target, restated as error against the truth: on a 2 mm spot moved 0.5 mm on mottled skin, an average error within 2 points and a spread of at most 1 point on an unchanged spot, a half-fading read within 2 points, and no more than 10 % of photos refused. Each condition is 100 simulated pairs at 20 pixels per mm.

What the simulation shows. Row numbers are lines of `data/registration_stress_results.csv` (inner disc, 2 mm), and the pass or fail summary is in `data/registration_stress_target.csv`.

- **With nothing disturbed, lining up still passes.** Sliding: error −0.01 points, spread 0.34 (line 8). Sliding and turning: +0.01, spread 0.32 (line 12). The sticker fails on spread (1.64, line 16), as in section 5.
- **Even tanning does no harm.** At 5 L\* the true change of an unchanged spot is +41.3 %, and lining up reads it within 0.03 points, spread 0.39 to 0.41 (lines 136, 140).
- **Patchy tanning breaks it.** When the skin pattern itself changes, the spread rises to 1.20 for sliding and 1.16 for sliding and turning (lines 168, 172). The average stays close (under 0.1 point), but single readings scatter too much.
- **Turning the camera breaks sliding at 5 degrees, but not sliding and turning.** Sliding only: spread 1.04 at 5 degrees (line 232) and 3.90 at 10 degrees, with 2 of 100 photos refused (line 264). Sliding and turning passes at every angle tried, spread 0.32 at 10 degrees (line 268).
- **A 20 % light ramp breaks every method, just.** Spread 1.04 for sliding and 1.06 for sliding and turning (lines 328, 332). A 5 % ramp passes (lines 296, 300).
- **Fall-off towards the edges breaks every method from the smallest size tried, even the sticker.** At 10 % the unchanged spot reads 4.6 points too high whether lined up or not (lines 360, 364, 368). The ring around the spot gets less light than the spot, so the contrast itself changes; better placement cannot fix that. At 20 %, lining up also misses its mark (0.25 mm average centre error) and refuses 14 of 100 photos (line 392).
- **Two hairs break every method.** With no mask, the spread is about 12.8 for every placement (lines 40, 44, 48). Leaving out the hairs found automatically brings it down to 1.91 and 1.88 for the two ways of lining up (lines 41, 45), still above 1. With 8 hairs and the mask, every photo is refused because more than 20 % of the ring is masked (line 73; 100 of 100), and without the mask the spread is about 28 (line 72).
- **All four together break every method** (spread 3.27 at best, sliding and turning with the hair mask, line 429).

The smallest size at which each method fails (target file, lines 230 to 353):

| Disturbance | Sliding | Sliding and turning | Sticker |
|---|---|---|---|
| Hair | 2 strands | 2 strands | 2 strands |
| Even tan | none of the sizes | none of the sizes | fails already with nothing disturbed |
| Patchy tan | 5 L\* (only size) | 5 L\* (only size) | fails already |
| Turning | 5 degrees | none of the sizes (up to 10) | fails already |
| Light ramp | 20 % | 20 % | fails already |
| Edge fall-off | 10 % | 10 % | fails already |
| All together | fails | fails | fails |

What this means for the plan, if the simulation's assumptions hold. Lining up by sliding and turning should replace sliding only, because it removes the camera-turning problem at no cost in the best case. Edge fall-off is the biggest problem, and it is a lighting problem, not a placement one: the plan's section 4 target cannot be met without a flat-field correction or lighting that is even across the ring (plan C3). Hair needs either shaving or clipping before each session or a better hair finder than the simple one used here. The hair finder is the builder's own design, not part of the test contract, so this result is about this detector, not about hair masking in general. Patchy tanning suggests photos should be taken in the same season, or the reference ring should be corrected for tan.

Limits: the hairs are straight, dark, 0.08 mm wide and redrawn independently at each visit. Tanning of the spot itself is set to zero (a READING in the test file). Light changes are smooth and multiplicative. The skin does not stretch or curve. Rows for 4 mm are in the results file but are not judged against the 2 mm target.

```
python3 experiments/registration_stress_sim.py --out data   # about 26 minutes on 4 cores
python3 -m pytest experiments/tests -q                      # 66 stress tests, written before the code
```
