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

The audit covers every percentage in the ledger that is printed with a denominator, both quoted (68 pairs from 10 studies, `data/denominator_audit.csv`). Seven percentages, in four studies, do not correspond to a whole number of the stated lesions or patients: laosakul2017 (82.3% of 43 treated lesions), rerknimitr2013 (11% of 26 patients), goldust2013 (41.6% and 10.3% of 240 patients) and ravikiran2014 (35.9% of 139 macules; 41.5% and 13.4% of 89 repigmented macules). In three of them the paper also prints the count, and that count gives a slightly different percentage (100/240 = 41.67%, 25/240 = 10.42%, 50/139 = 35.97%). Five of the seven fit if the paper cut the decimals instead of rounding them; 82.3% of 43 and 10.3% of 240 fit neither way. Possible reasons are an evaluable number smaller than the one stated, a different unit being rated, or a rounding convention. Each is a question for the full text. Eleven further percentages are not audited because the ledger gives no denominator for them, or only an inferred one in brackets (`data/denominator_not_audited.csv`); rerknimitr2015 is audited against the 120 lesions its abstract states, not the inferred 60.

{{reproduce_calc}}
