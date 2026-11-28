# IGH Repair Notebook: project rules

Open research on repairing sun-damaged skin, built hub-and-spoke. Module 1 (IGH white spots) is active. Modules 2 to 4 follow the same rules. The owner is Ben, a manufacturing engineer. This is research, not medical advice.

**Read `STATUS.md` before doing anything. Update it before you stop.**

## Core question

Which treatments help a small white spot match the surrounding skin, and does the match last at least six months after the final treatment? For later modules, replace "white spot" with that module's target and keep the six-month test.

## Modules

| Module | Target | Scope limit |
|---|---|---|
| 1-hypopigmentation | IGH white spots | all human clinical studies |
| 2-hyperpigmentation | solar lentigines, mottled brown tone | off-face only (forearm, hand, chest, lower leg); systematic reviews and controlled trials |
| 3-dermal-texture | thinning, crepiness, elastosis | off-face only; needs biopsy, ultrasound or cutometer data |
| 4-surface-vascular | roughness, fine redness | off-face only; exclude actinic keratoses and anything precancerous |
| 5-damage-repair | what is damaged at the cell and gene level in sun-damaged skin of this kind, and repair approaches (gene therapy, cell therapy, other state-of-the-art paths) | human studies plus laboratory and mechanism studies; leads only until Gate A; every output is framed so "a more full study can be performed by professionals" |
| 6-spot-model | a cell-level simulation of one IGH white spot (pigment cells, the skin cells they supply, the dermis beneath) to compare competing explanations and predict whether transplanted pigment cells hold | simulation only, synthetic cells; scope is cell behaviour and cell transplantation; no simulation of gene therapy or gene editing; every input quoted from a saved source with PMID or labelled an assumption; output is ranked testable hypotheses, never evidence, and nothing enters the ledger |

Do not start a module that `STATUS.md` does not list as open.

**Module 5 (underlying damage and repair)** was opened by Ben on 2026-11-28. His direction, in his words: to "find a genetic or more complete cure to what cuases or what is damaged in this kind of skin diseas", looking at gene therapy and, "if thats not the exact path", other paths, because "the treatements available now are outdated and rudimentary" and he wants "an up to date path that is more in line with the state of the art", so that "a more full study can be performed by professionals". It starts with two logged searches: (a) what is damaged at the cell and gene level, (b) cell and gene therapy approaches for pigment loss. Everything it finds is a lead until Ben passes Gate A. All rules and gates in this file apply to it unchanged.

**Module 6 (spot model)** was opened by Ben on 2026-11-28. His direction, in his words: "I guess my vision would be to delve deeper into exact simulations for therapies", approving a small first step with "all your recommendations sound correct. go ahead". It starts with a plan, `content/spot-model-plan.md`, and no code is written until Ben has read it. The model compares two explanations of an IGH spot (pigment cells wear out on their own, versus the dermis wears them out) by what each predicts for spot edges and growth, for transplanted pigment cells, and for tissue markers. Every input is quoted from a saved source with its PMID or labelled an assumption. Model output is a ranked set of testable hypotheses, never evidence that a treatment works, and never enters `data/evidence.csv`. Builds follow the tests-first pattern of `experiments/drift_sim.py`. All rules and gates in this file apply to it unchanged.

## Rules that never bend

1. **No number without a verbatim quote.** Every numeric cell needs a quote in the record, and the quote must exist in the saved source text. `tools/ledger.py` enforces this.
2. **Follow-up is counted from the final treatment**, never from baseline. If the paper only gives time from start, write `NOT_DERIVABLE` and say why.
3. **Never mix patients and spots.** `analysis_unit` says which one a number counts.
4. **Three outcomes stay separate:** partial repigmentation, complete area coverage, lasting colour match. "More than 75% improved" is partial.
5. **Say what is missing, in these words:** `not in abstract`, `not reported` (full text read, paper silent), `not measured`, `full text needed`. Never guess. Never leave a cell blank.
6. **Access is a status, not an obstacle to work around:** `FULL_TEXT`, `ABSTRACT_ONLY` or `BLOCKED`. After two failed attempts to reach a source, mark it `BLOCKED`, add it to the paywall list in `STATUS.md` and move on.
7. **No patient images** anywhere in the repository. Simulations use synthetic shapes.
8. **Nothing leaves the machine without Ben:** no deploy, no email, no post, no public push.
9. Inferred values go in `[square brackets]`. Claims from a brief, a chatbot or a review article are leads until a primary source is quoted.

## Roles are files (read yours first)

Five role definitions live in `.claude/agents/`: `searcher.md`, `extractor.md`, `verifier.md`, `dataset-auditor.md`, `test-author.md`. A local Claude Code session loads them as subagents automatically. A cloud thread in a project does not, so when a task names a role, open that file with Read and follow it exactly, including its reply length. One role and one unit of work per thread.

## If you are the main session or the project conversation, you are the orchestrator

You plan, delegate, run the scripts, merge and report. You do not extract data from papers yourself.

- **One unit of work per subagent.** One paper for `extractor`, one record for `verifier`, one query set for `searcher`, one dataset for `dataset-auditor`. Never hand a subagent a topic.
- **Search and extraction are separate stages** with a human gate between them.
- **Delegation message contract:** give the subagent the study ID or query, the exact input file paths, the exact output path, and nothing about what you expect it to find.
- **Return contract:** a subagent replies in under 150 words with the path it wrote, its access status and any blocker. The data lives in the file, not in the reply.
- **Order of gates for every record:** `extractor` writes `data/staging/<study_id>.json` → `python3 tools/ledger.py validate` → `verifier` on a fresh context → `python3 tools/ledger.py merge`. A record that fails twice is logged `BLOCKED` in `STATUS.md`.
- **Batch size:** at most 6 subagents at once. After each batch, run the validator, update `STATUS.md`, commit.
- **Stop at human gates** (listed in `STATUS.md`) and report what is waiting.

## Where things are

```
data/evidence.csv            the ledger (one row per arm, endpoint and time point)
data/evidence_quotes.jsonl   verbatim support for every number (written by ledger.py merge)
data/staging/                one JSON record per study, awaiting gates
data/*.csv                   search log, screening log, datasets, corrections, experiment outputs
papers/pdfs/                 full texts Ben supplies (not committed)
papers/excerpts/             plain text of each source, for quote matching (not committed)
experiments/                 simulation and calculation scripts
tools/ledger.py              validate | merge | check
tools/pubmed.py              logged PubMed search that saves abstracts
content/, templates/, build.py, site.json   the static site
source/, outreach/           starting brief and email draft (not committed, not published)
```

## Commands

```
python3 tools/ledger.py check
python3 tools/ledger.py validate data/staging/*.json
python3 tools/ledger.py merge data/staging/*.json
python3 -m pytest tests -q
python3 build.py && python3 -m http.server --directory dist 8000
```
