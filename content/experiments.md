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

### 6. Does space help tell the two explanations of a white spot apart? (spot model, grid version)

<p><span class="tag sim">Simulation</span> Synthetic cells on a synthetic lattice, synthetic images. No patient images. <strong>Certainty level 0: every statement here is a hypothesis that follows from the model's own assumed rates, not evidence about real skin or any treatment.</strong> Nothing here enters the ledger.</p>

The well-mixed spot model (plan `content/spot-model-plan.md`, steps M3 and M4) could not tell its two explanations apart at six months after a transplant: H1, "the pigment cells wear out on their own", and H2, "the dermis underneath wears them out". The grid version (`experiments/spot_model_grid.py`, step M6) puts the same rules on a lattice of pigment-cell sites at the quoted surrounding density (220 per mm², PMID 2508572), with a dermal signal that spreads a distance `lambda_D` from senescent fibroblasts, renders each simulated spot as a photograph (0.1 mm blur, 20 px/mm) and measures it the way the measurement tool would. It reruns the 325 parameter sets the well-mixed sweep had accepted, each with a signal reach drawn between 0.05 and 2 mm, under both settings for transplanted cells. Sets, seeds, acceptance rules, thresholds and expectations were committed before the run (commit de98522). Thresholds are provisional until the phantom tests give a smallest detectable change: 0.1 mm for edge width, 1.0 L* for contrast, 0.05 for the patchiness score.

Numbers below cite lines of `data/spot_model_m6_summary.csv` (S) and, for counts worked out after seeing the results, `data/spot_model_m6_posthoc.csv` (PH, labelled post hoc: not a test of any prediction). Transplanted cells keep the resident rates unless stated; the other setting gives the same edge results (S 87, 110).

- **Space removes sets.** Of 43 H1, 231 H2 and 51 mixture sets the well-mixed model accepted, 34, 67 and 25 pass in space (S 4, 27, 50). Most H2 losses are the sharp-edge check and the density check: 86 and 105 of 231 pass them (S 32, 29). No H2 set with signal reach above 0.4 mm keeps a sharp edge (0 of 95, S 35); the widest accepted reach is 0.35 mm (S 48).
- **Edge width separates H1 from H2 in this model (P1).** H1 edges sit at the blur floor, 0.27 / 0.28 / 0.31 mm (10th / 50th / 90th percentile, S 13), the same for 2 to 5 mm spots (PH 12, 14, 16). H2 edges are 0.36 / 0.50 / 0.89 mm (S 36), get wider on larger spots (median 0.43 to 0.56 mm, PH 13, 15, 17) and with signal reach (0.39 to 0.80 mm, PH 18 to 20). 59 of 67 accepted H2 sets are wider than every accepted H1 set (PH 4). The median gap, 0.22 mm, is above the provisional 0.1 mm threshold (S 73).
- **Patchiness in a photo shows up only under H2 (P3).** The photo patchiness score is above 0.05 in 50 of 67 H2 sets and 0 of 34 H1 sets (PH 7, 6). At cell resolution both explanations are patchy (median 0.21 and 0.21, S 17, 40), so both pass the biopsy "skip areas" check. In this model H1's gaps are single cells, too small to survive the blur, and H2's patches follow the random clusters of senescent fibroblasts.
- **Centre lighter than rim leans H2, but mostly below 1.0 L*.** Median rim-to-centre contrast is 0.01 L* under H1 and 0.61 L* under H2 (S 15, 38); 18 of 67 H2 sets pass 1.0 L*, against 1 of 34 H1 sets (PH 10, 9).
- **Mixtures look like H1.** When both causes act, edges, patchiness and rim contrast fall back towards H1 values (S 59, 62, 61; patchiness above 0.05 in 1 of 25 sets, PH 8). A real spot with both causes would be hard to read from photographs.
- **The six-month transplant result does not change (P4).** No accepted set under either explanation or setting fades by more than 1.0 L* between 28 and 180 days after the final session (S 23, 46, 97, 120). The H2 minus H1 median gap is 0.27 L* (S 76). No transplanted cell was refused for lack of room (overflow 0, S 24, 47).
- **No direct pairs.** No draw was accepted under both H1 and H2 (S 72), so the pre-registered pair scoring is empty. Everything above compares the two groups of accepted sets.

Against the expectations written before the run (plan 11.5 and the run script):

- **G1 held:** H1 edges stay near the blur floor for every size.
- **G2 half held:** high signal reach is rejected by the sharp-edge rule. But the accepted H2 edges are clearly wider than H1's, which the test author listed as counting against G2, and against my own expectation of "untestable".
- **G3 failed for H2:** the photo patchiness score differs between H1 and H2 by more than 0.05 in most sets.
- **G4 failed:** H1 rims stayed near zero, under 0.2 L*, at median.
- **G5 held:** no overflow, and the six-month result matches the well-mixed model.

What this means, at level 0: if the assumptions hold, the edge of an untreated spot, and to a lesser degree its patchiness in a photo, is where the two explanations differ by more than the provisional thresholds. A transplant's six-month colour does not separate them. That makes P1 (edge width from Ben's own photographs) the cheapest test the model points to. It also makes the measurement tool's real smallest detectable change for edge width the number that decides whether that test is usable.

Limits:
- Thresholds are provisional.
- Only sets the well-mixed model accepted were tried.
- H2's photo patchiness rests on one assumption, that senescent fibroblasts sit at random, one per site. No saved source gives their layout.
- The spot is a fixed disc, so growth (P2) is not modelled.
- There is no skin texture, hair or mottle in the rendering, all of which would hide fine edges.
- Signal reach is unmeasured.

```
python3 experiments/spot_model_grid_compare.py --out data --workers 4 --cache <dir>   # about 2 hours on 4 cores
python3 experiments/spot_model_grid_posthoc.py --data data                            # post-hoc counts
SPOT_MODEL_GRID_REQUIRED=1 python3 -m pytest experiments/tests/test_spot_model_grid.py -q   # 124 tests, written before the code
```
