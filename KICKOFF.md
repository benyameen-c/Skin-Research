# Running this project in Claude Code

The standing rules live in `CLAUDE.md` and the state lives in `STATUS.md`, so each session prompt can be short. Claude Code loads `CLAUDE.md` automatically, and the subagents in `.claude/agents/` load it too.

## One-time setup

```
cd igh-site
git init && git add -A && git commit -m "Session 1: evidence ledger, experiments, site, orchestration kit"
pip install -r requirements.txt pytest
python3 tools/ledger.py check && python3 -m pytest tests -q
```

Put any full-text PDFs you can get into `papers/pdfs/`, named `<study_id>.pdf` (the list is in `STATUS.md`). Then start Claude Code in this folder.

## Who does what

| Role | Runs as | Model | Job |
|---|---|---|---|
| Orchestrator | main session | your strongest | plans, delegates, runs scripts, merges, reports; extracts nothing |
| searcher | subagent | sonnet | one query set → search log and screening list |
| extractor | subagent | sonnet | one study → one staging record with quotes |
| verifier | subagent | opus | one record → PASS or FAIL, from the source text alone |
| dataset-auditor | subagent | sonnet | one dataset → one line in `datasets.csv` |
| test-author | subagent | inherit | tests from the spec, before the code |

The verifier uses a different model from the extractor on purpose, so the two are less likely to share a blind spot. Change any `model:` line in `.claude/agents/` to suit your plan.

Every record passes three gates in order: the validator script, the verifier, then you.

## Session 2: close Module 1

```
Read CLAUDE.md and STATUS.md. You are the orchestrator.

Goal: finish the "To close Module 1" list in STATUS.md.

1. Run `python3 tools/ledger.py check` and `python3 -m pytest tests -q` and show me the output.
2. For each extracted study that has no verbatim quotes yet, launch one extractor subagent, at most 6 at a time. Give each only its study_id and file paths.
3. Run the validator on data/staging. For each record that passes, launch one verifier subagent on a fresh context. Do not pass it the extractor's reply.
4. Merge PASS records. Retry a failed record once with the verifier's notes, then mark it BLOCKED.
5. Update STATUS.md, rebuild the site, commit.
6. Stop at Gate B. Report: every cell where the new extraction disagrees with the old row, the blocked list, and the updated paywall list.

Do not start Module 2. Do not deploy or send anything.
```

## Session 3: extend the simulation

```
Read CLAUDE.md and STATUS.md. You are the orchestrator.

Extend experiments/alignment_pixel_sim.py. Specification:
- spot diameters 2, 3, 5 and 8 mm
- alignment shifts as now, combined with a 5% and a 10% exposure drift and a white-balance drift
- colour in CIELAB; report area error and delta-E error
- five regimes: unchanged white spot, fading white spot, shrinking white spot, white spot turning darker than skin, fading brown spot on a mottled background
- a grey reference patch in the scene, used to correct drift, with results shown with and without the correction

First have the test-author subagent write the tests from this specification and commit them. Then implement until the tests pass without changing them. Write data/sim_results.csv, add the results to content/experiments.md, rebuild, commit. Stop and show me the pytest log and the three largest errors.
```

## Session 4: Module 2 search (stops at Gate A)

```
Read CLAUDE.md and STATUS.md. You are the orchestrator. Open module 2-hyperpigmentation in STATUS.md.

Have searcher subagents run and log searches for off-face solar lentigines and mottled pigmentation: systematic reviews first, then controlled trials on forearm, hand, chest or lower leg. One query set per subagent. No extraction.

Stop at Gate A. Give me the screening counts by decision, the included list with DOIs, and the full texts I need to supply.
```

## Session 5: Module 2 extraction

Same prompt as Session 2, with "the included studies in data/screening_log.csv for module 2" in place of the Module 1 list.

## Session 6: site

```
Read CLAUDE.md and STATUS.md. Rework build.py and content/ so the site is hub-and-spoke: an overview, then one evidence view per open module, all generated from data/evidence.csv by its `module` column. Keep the four section names. Stop at Gate B.
```
