# IGH Repair Notebook

Open research notes on one question: **which treatments help a small white spot (idiopathic guttate hypomelanosis) match the surrounding skin, and does the match last?**

Research notes, not medical advice.

## Build and preview

```
pip install -r requirements.txt        # markdown, numpy
python3 build.py                       # writes dist/
python3 -m http.server --directory dist 8000
```

Open http://localhost:8000. `dist/` is a plain static site (one HTML page plus data and code files) and can be served by any static host.

## Change a finding once

Everything on the page is generated.

| To change | Edit | Then |
|---|---|---|
| A study result, a timing, a verification status | `data/evidence.csv` | `python3 build.py` |
| A correction, dataset lead, hypothesis or project path | the matching CSV in `data/` | `python3 build.py` |
| Explanatory text or a progress entry | `content/*.md` | `python3 build.py` |
| Contact route, contributors, section order | `site.json` | `python3 build.py` |
| Simulation settings | `experiments/alignment_pixel_sim.py`, re-run it | `python3 build.py` |

`evidence.csv` uses the 27-column header from the starting brief plus six columns: `module`, `outcome_tier`, `citation`, `source_url`, `treatment_class`, `months_after_final_tx`. One row per arm, endpoint and time point. Missing information is written out: "not in abstract" (only the abstract was read), "not captured this session" (full text read, field not extracted), "not measured", "full text needed".

## Experiments

```
python3 experiments/alignment.py                       # seed formula, unchanged
python3 experiments/alignment_pixel_sim.py --out data  # about 2 minutes
python3 experiments/clustering_sensitivity.py --out data
python3 experiments/denominator_audit.py --out data
```

The simulation uses synthetic disks only. No patient data is used anywhere in this repository.

## Layout

```
content/      Markdown for the five sections ({{shortcodes}} pull in data)
data/         CSV files: the single source for every table and card
experiments/  Python scripts that produce the experiment CSVs
templates/    page shell, stylesheet, script
source/       the unchanged starting brief (NOT copied into dist/)
outreach/     draft email for review (NOT copied into dist/)
build.py      static site generator
site.json     title, contact route, contributors, sections
```

## Orchestrated work in Claude Code

`CLAUDE.md` holds the standing rules, `STATUS.md` the current state, `.claude/agents/` five subagent definitions, and `KICKOFF.md` the per-session prompts. `tools/ledger.py` is the deterministic gate every evidence record must pass before a verifier sees it. `tools/pubmed.py` has not been run yet.

```
python3 tools/ledger.py check
python3 -m pytest tests -q
```

## Before going public

- Set `contact.issues_url` or `contact.email` in `site.json`. Until then the site shows a marked placeholder.
- `source/IGH_Research_Base.md` contains researcher email addresses and a draft message. Keep `source/` and `outreach/` out of a public repository, or redact them first.
- Spot-check the rows whose verification status says "machine-read PDF" against the PDF tables.
- The site accepts no uploads. Do not add patient photographs.

## Deploying (not done)

Any static host works. For GitHub Pages, publish the contents of `dist/` (a `.nojekyll` file is included). Nothing has been deployed and no outreach has been sent.
