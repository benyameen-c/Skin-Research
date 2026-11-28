# Plan: a cell-level model of one IGH white spot

Status: planning document for Ben's review, 28 November 2026. No code exists yet and none is written until Ben has read this plan. Not linked from the site (`site.json` does not list it) and not for publication until Gate B. Research, not medical advice.

SIMULATION ONLY. Synthetic cells on a synthetic grid. No patient images (CLAUDE.md rule 7).

## 1. Purpose, and what the model can and cannot claim

Ben asked to "delve deeper into exact simulations for therapies" (28 November 2026). This plan is the first, deliberately small step: one model of one white spot, built to compare two explanations of why the spot stays white, and to say what each explanation predicts for a cell transplant.

**What the model is for.** IGH papers agree that a spot has fewer pigment cells (melanocytes) than the skin around it. They disagree, or are silent, on why. Two explanations are on the table in the saved sources (section 4): the melanocytes wear out on their own, or the deeper skin layer (the dermis) wears them out. Those two explanations make different predictions about things that can be measured: how the edge of a spot looks, whether a spot grows, whether transplanted melanocytes keep their colour after six months, and which tissue markers should differ between spot and surrounding skin. The model's job is to make those predictions explicit and numerical, so that the cheapest measurement that tells the two apart can be named.

**What the model can claim.**

- "If explanation A is true and these assumptions hold, the model predicts X; under explanation B it predicts Y."
- "Prediction X holds across this range of the unmeasured inputs; prediction Z flips sign inside it, so Z is not a useful test."
- "These are the inputs nobody has measured that the answer depends on most."

**What the model cannot claim.**

- That either explanation is true. A model built on its own assumptions can only show what follows from them.
- That any treatment works, or how well. Output is a ranked list of testable hypotheses, never evidence for the ledger. Nothing it produces enters `data/evidence.csv`.
- Anything about gene therapy or gene editing. Those are out of scope by design (section 2.4).
- Anything numerical about a real person's spot. Every unmeasured input is labelled an assumption, and most inputs are unmeasured (section 3).

**Scope.** Cell behaviour inside and around a single 2 to 5 mm spot, and one intervention: adding melanocytes (cell transplantation, the only direction in `content/frontier-scan.md` with an IGH precedent and long follow-up elsewhere). Every model input is traced to a quoted sentence in a source already saved in `papers/excerpts/` with its PMID, or labelled `ASSUMPTION`. No new literature search was run for this plan.

## 2. Entities and rules

## 3. Parameters: what has a published value and what does not

## 4. The two competing explanations and the predictions that separate them

## 5. How model output maps to things that can be measured

## 6. Build sequence, tests first

## 7. Validation and sensitivity analysis

## 8. Risks of over-reading the output

## 9. Open questions for Ben

## Sources used
