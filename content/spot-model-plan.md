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

### 2.1 The space

A square patch of skin seen from above, about 8 mm across, with one spot of 2 to 5 mm at its centre ("small 2- to 5-mm achromic or hypopigmented macules", PMID 3805391). Two stacked layers on the same grid:

- **Basal layer of the epidermis**, where melanocytes sit and hand pigment to the skin cells above them.
- **Superficial dermis** directly beneath, where fibroblasts sit.

Grid spacing, the number of keratinocytes each melanocyte supplies, and the layer thicknesses are `ASSUMPTION` (no saved source gives a number; see section 3). Time steps are days, run to at least 2 years so the six-month test can be read off after any simulated final treatment.

### 2.2 Entities and their states

| Entity | States | Where the states come from |
|---|---|---|
| Melanocyte (M) | active, hypoactive (alive, little or no pigment made), senescent, gone | "Depigmentation in IGH seems to occur in two stages, loss of melanogenic activity in certain malanocytes and elimination of inactive melanocytes" (PMID 7377803; spelling as printed). Senescent state: "expression of p16, p21, and hp1 was significantly higher in lesional skin of IGH patient as compared to healthy controls" (PMID 29516488) |
| Keratinocyte column (K) | holds a melanin amount, renewed over time | The pigment seen at the surface is carried by keratinocytes. The renewal time is `ASSUMPTION` (no saved number) |
| Fibroblast (F) | normal, senescent | Title only: "Role of senescent fibroblasts in the development of idiopathic guttate hypomelanosis" (PMID 31823346). The saved copy has no abstract |
| Dermal signal field (D) | a concentration on the grid, made by senescent fibroblasts, spread by diffusion, removed by decay | `ASSUMPTION`. The nearest saved evidence is in vitiligo, not IGH: "higher expression of DKK1 in the dermis induced senescence in melanocytes that may lead to hypopigmentation" (PMID 29442138) |
| Melanocyte reservoir (R) | a source of new melanocytes at fixed points (hair follicles), on or off | Mouse only: micro-injury "induces the hair follicle melanocyte stem cells to migrate upwards to the interfollicular epidermis, activating and giving rise to melanocytes to repopulate the vitiligo lesion" (PMID 35044224). For IGH: `ASSUMPTION` |

### 2.3 Rules

Each rule is applied every time step. "Sourced" means a saved sentence supports the rule's *direction*; in every case the *rate* is an assumption (section 3).

| # | Rule | Status and source |
|---|---|---|
| R1 | An active melanocyte becomes hypoactive at an intrinsic rate `k_int`, which rises with cell age | Direction sourced: "The basic defect in IGH melanocytes may reflect the aging process" (PMID 7377803); "The evidence indicates an age-related somatic mutation of melanocytes" (PMID 6183861). Rate: `ASSUMPTION` |
| R2 | A hypoactive melanocyte becomes senescent or is eliminated | Sourced: the two-stage quote under 2.2 (PMID 7377803) |
| R3 | A melanocyte that fails to hand over pigment accumulates it, and accumulation raises its chance of senescence | Sourced as a hypothesis by the authors: "Accumulation of melanin can lead to the senescence in the melanocytes of IGH patients" (PMID 29516488). Transfer defect seen directly: "In some areas, there was a reduced uptake of melanosomes by the keratinocytes" (PMID 25088925). In UV-aged cells, not IGH: "senescent melanocytes are characterized by melanosome transport dysfunction resulting in melanin accumulation" (PMID 37554281, full text saved as `pmc_37554281.txt`) |
| R4 | The dermal signal D raises a melanocyte's rate of senescence and death, scaled by a coupling `k_derm` | Direction: vitiligo, DKK1 "induced senescence in the treated melanocytes" (PMID 29442138). IGH: title only (PMID 31823346), and "Our results suggest an interaction between melanocytes and the subjacent dermis in IGH" (PMID 35114009). Strength: `ASSUMPTION` |
| R5 | A senescent fibroblast produces D at rate `p_D`; D diffuses with length scale `λ_D` and decays | `ASSUMPTION` entirely. Only the existence of dermal change is sourced: "We found superficial dermal fibrosis in 90% (18/20) of our IGH cases" (PMID 35114009). One study disagrees: "In the dermis, fibroblasts were structurally normal" (PMID 25088925) |
| R6 | A senescent melanocyte slows its neighbours | Sourced outside IGH, in aged human skin: "senescent melanocyte SASP induces telomere dysfunction in paracrine manner and limits proliferation of surrounding cells" (PMID 31633821). Range and strength: `ASSUMPTION`. Optional switch, off in the base runs |
| R7 | A gap left by a lost melanocyte can be filled by a neighbour dividing, or from the reservoir if it is on | `ASSUMPTION`. Melanocyte division rate in adult skin: no saved number |
| R8 | Each keratinocyte column takes pigment from its supplying melanocyte at rate `k_tr` and loses pigment as the column renews | `ASSUMPTION` for both rates. Transfer defect direction: R3 sources |
| R9 | Transplant event: at a chosen day, add a number of healthy melanocytes per mm² to the spot, with age zero and a stated survival fraction | Visible repigmentation timing sourced: "Repigmentation was visible within 7 to 14 days" (PMID 3908515). Survival fraction and how many cells a graft delivers: `ASSUMPTION` |
| R10 | The model never sets the melanocyte count to exactly zero by rule; zero can only arise from the dynamics | Sourced, with a conflict to keep visible: "In no case were melanocytes completely absent, excluding vitiligo" (PMID 6183861) versus "Histochemical studies confirmed the absence of dopa-positive cells in the areas of leukoderma prior to grafting" (PMID 3908515, a mixed leukoderma series) |

### 2.4 What is deliberately left out

- **Genes, mutations and gene therapy or editing.** The model has no genome. "age-related somatic mutation" (PMID 6183861) enters only as a rate in R1. Simulating a gene therapy would need a target gene established in IGH, and the saved sources name none beyond an early drop in one autophagy protein ("ATG7 downregulation emerged as the earliest molecular alteration", PMID 41453137), which the model can carry as a marker (section 5) but not as an intervention.
- **The immune system.** No immune attack is established in IGH (`content/frontier-scan.md`). One saved series reports "One-third of patients had a sparse perivascular lymphocytic infiltrate, whereas the rest had no significant dermal inflammation" (PMID 25484386). Left out of the base model; an open question if Ben wants it.
- **Drugs, lasers, peels, 5-FU.** Only transplantation in the first build. A wounding stimulus that switches the reservoir on is an optional extension (open question 3).
- **Whole-body (systemic) factors.** See section 4.3: one saved result points that way, and the first build cannot represent it.

## 3. Parameters: what has a published value and what does not

Status words: `QUOTED` (a saved source gives the number; quote and PMID in the table), `NOT IN SAVED SOURCES` (the quantity may well be measured somewhere, but no source saved in this project gives it; a logged search could look, and this plan did not run one), `NOT MEASURED IN IGH` (a saved source gives a value in another condition or species only). Every value that is not `QUOTED` enters the model as an `ASSUMPTION` with a range, and is swept in section 7.

### 3.1 Values a saved source gives

| Parameter | Value | Quote | PMID | Caveat |
|---|---|---|---|---|
| Spot diameter | 2 to 5 mm | "small 2- to 5-mm achromic or hypopigmented macules" | 3805391 | clinical description, not a measured distribution |
| Melanocyte density, spot vs surrounding skin | 55.25 vs 220 per mm² | "reduction of the number of melanocytes in the depigmented macula as compared with the surrounding area (55.25 +/- 18.00 mm2 vs 220 +/- 28.28 mm2" | 2508572 | dopa staining, 1989; patient count not in abstract. [Inferred ratio: about 0.25] |
| Melanocyte density after the spot was grafted onto a mouse | 388.75 per mm² | "The number of melanocytes increased significantly (388.75 +/- 213 mm2)" | 2508572 | grafted IGH skin on nude mice; timing of the count not stated in the abstract for IGH |
| Time to repigmentation, IGH skin on mouse | 20 days | "Twenty days after skin transplantation, repigmentation of the area was observed" | 2508572 | mouse host |
| Time to visible repigmentation after melanocyte grafting | 7 to 14 days | "Repigmentation was visible within 7 to 14 days" | 3908515 | mixed leukodermas including IGH; no later follow-up in the abstract |
| Share of spots with superficial dermal fibrosis | 18 of 20 | "We found superficial dermal fibrosis in 90% (18/20) of our IGH cases" | 35114009 | counted per patient's biopsy |
| Share with epidermal atrophy | 5 of 47 | "epidermal atrophy was present in only five cases (10.6%)" | 20465639 | |
| Share with patchy retained pigment ("skip areas") | almost 80% | "small foci of retained melanin in the basal layer (skip areas) alternating with larger areas of melanin loss were present in almost 80% of cases" | 25484386 | 55 biopsies; a spatial pattern the model must be able to reproduce (section 7) |
| Senescence markers, spot vs control | higher, no size given | "expression of p16, p21, and hp1 was significantly higher in lesional skin of IGH patient as compared to healthy controls" | 29516488 | six patients, six controls; direction only |

### 3.2 Values the model needs that no saved source gives

| Parameter | Symbol | Status | Starting range for the sweep (all `ASSUMPTION`) |
|---|---|---|---|
| Intrinsic rate at which an active melanocyte goes hypoactive | `k_int` | NOT IN SAVED SOURCES | chosen so that spot formation takes years, not weeks (to be set in the spec) |
| How that rate rises with cell age | `a_int` | NOT IN SAVED SOURCES | flat to steep |
| Hypoactive to senescent, and senescent to gone | `k_sen`, `k_loss` | NOT IN SAVED SOURCES | months to years |
| Melanocyte division rate in adult skin | `k_div` | NOT IN SAVED SOURCES | near zero to modest |
| Melanin transfer rate to keratinocytes | `k_tr` | NOT IN SAVED SOURCES | normalised to 1 in healthy skin |
| Keratinocyte column renewal time | `T_K` | NOT IN SAVED SOURCES | weeks |
| Keratinocytes supplied per melanocyte | `n_K` | NOT IN SAVED SOURCES (the term "epidermal melanin unit" appears in PMID 29516488 with no number) | fixed; only enters the rendering |
| Share of dermal fibroblasts senescent under a spot vs outside | `f_sen` | NOT IN SAVED SOURCES (only title-level for IGH, PMID 31823346) | 0 to high |
| Dermal signal production, diffusion length, decay | `p_D`, `λ_D`, `μ_D` | NOT MEASURED IN IGH (DKK1 effect on melanocytes reported in vitiligo, PMID 29442138, with no rate) | `λ_D` from 0.05 mm to 2 mm: this one decides how sharp the spot edge is (section 4) |
| Coupling of dermal signal to melanocyte senescence | `k_derm` | NOT MEASURED IN IGH | 0 (H1) to dominant (H2) |
| Paracrine reach of a senescent melanocyte | `λ_M` | NOT MEASURED IN IGH (direction only, PMID 31633821) | off in base runs |
| Reservoir density and output | `ρ_R`, `k_R` | NOT MEASURED IN IGH (mouse, PMID 35044224) | off, or follicles at a set spacing |
| Transplanted cells delivered per mm², and share surviving | `N_tx`, `s_tx` | NOT IN SAVED SOURCES | delivered: up to the surrounding density of 220 per mm²; survival 10% to 90% |
| Rate at which spots grow in diameter | — | NOT IN SAVED SOURCES | none: this is a model *output*, and the plan treats its absence from the literature as a gap (section 5) |
| Melanin-to-lightness mapping | — | NOT IN SAVED SOURCES | monotone, saturating; chosen so the spot reads about +12 L* above skin, the contrast the existing drift simulation uses (`content/measurement-tool-plan.md` 2.1 item 5) |

[Inference: of roughly 20 inputs, about 9 facts have a quoted value and none of them is a *rate*. The model is therefore a tool for comparing shapes of behaviour, not for predicting dates. Section 8 returns to this.]

## 4. The two competing explanations and the predictions that separate them

## 5. How model output maps to things that can be measured

## 6. Build sequence, tests first

## 7. Validation and sensitivity analysis

## 8. Risks of over-reading the output

## 9. Open questions for Ben

## Sources used
