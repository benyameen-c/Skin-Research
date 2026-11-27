#!/usr/bin/env python3
"""Build the IGH research site.

Reads site.json, content/*.md and data/*.csv and writes dist/index.html plus
copies of the data, code and source files. Edit a number in a CSV, run this
again, and every table and card that uses it is regenerated.

Run:     python3 build.py
Preview: python3 -m http.server --directory dist 8000   then open http://localhost:8000
Needs:   Python 3.9+, the 'markdown' package (pip install -r requirements.txt)
"""
import csv
import html
import json
import re
import shutil
from collections import Counter, OrderedDict
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
DATA, CONTENT, TPL, DIST = ROOT / "data", ROOT / "content", ROOT / "templates", ROOT / "dist"
E = html.escape


def rows(name):
    with open(DATA / name, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def table(headers, body, num_cols=()):
    out = ['<div class="scroll"><table><thead><tr>']
    out += [f"<th>{E(h)}</th>" for h in headers]
    out.append("</tr></thead><tbody>")
    for r in body:
        out.append("<tr>")
        for i, c in enumerate(r):
            cls = ' class="num"' if i in num_cols else ""
            if isinstance(c, tuple):  # (text, css class)
                cls, c = f' class="{c[1]}"', c[0]
            out.append(f"<td{cls}>{c}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def link(url, text):
    return f'<a href="{E(url, quote=True)}" rel="noopener">{E(text)}</a>'


def study_label(sid):
    m = re.match(r"([a-z]+)(\d{4})", sid)
    return f"{m.group(1).capitalize()} {m.group(2)}" if m else sid


def short(text):
    return re.split(r",| \(| for ", text)[0].strip()


def grouped(evidence):
    g = OrderedDict()
    for r in evidence:
        g.setdefault(r["study_id"], []).append(r)
    return g


# ---- shortcodes -------------------------------------------------------------
def sc_evidence_counts(ctx):
    ev = ctx["evidence"]
    g = grouped(ev)
    extracted = [s for s, rs in g.items() if not rs[0]["verification_status"].startswith("lead")]
    lasting = [r for r in ev if r["outcome_tier"] == "lasting_color_match"]
    complete = [r for r in ev if r["outcome_tier"] == "complete_area_coverage"]
    months = [float(r["months_after_final_tx"]) for r in ev
              if r["diagnosis"].startswith("IGH") and re.fullmatch(r"\d+(\.\d+)?", r["months_after_final_tx"])]
    longest = f"{max(months):g}" if months else "n/a"
    return (
        '<div class="counts">'
        f'<div><b>{longest} mo</b><span>longest gap between a final treatment and an assessment, IGH rows</span></div>'
        f'<div><b>{len(extracted)}</b><span>studies extracted ({len(g) - len(extracted)} more logged as leads)</span></div>'
        f'<div><b>{len(ev)}</b><span>evidence rows, one per arm and time point</span></div>'
        f'<div class="zero"><b>{len(complete)}</b><span>rows that measured complete area coverage</span></div>'
        f'<div class="zero"><b>{len(lasting)}</b><span>rows that measured a colour match six months after the last treatment</span></div>'
        "</div>"
        f'<p class="status">Generated from data/evidence.csv · last updated {E(ctx["site"]["updated"])}</p>'
    )


TIER_WORDS = {
    "partial_repigmentation": "Partial repigmentation",
    "complete_area_coverage": "Complete area coverage",
    "lasting_color_match": "Lasting colour match",
    "lesion_count": "Count of white spots",
    "instrument_color": "Instrument colour reading",
    "unquantified": "Repigmentation, not quantified",
    "not_extracted": "Not extracted yet",
}


def sc_gap_map(ctx):
    body = []
    for sid, rs in grouped(ctx["evidence"]).items():
        r = rs[0]
        tiers = "; ".join(dict.fromkeys(TIER_WORDS.get(x["outcome_tier"], x["outcome_tier"]) for x in rs))
        lasting = any(x["outcome_tier"] == "lasting_color_match" for x in rs)
        body.append([
            f'<a href="#study-{E(sid)}">{E(study_label(sid))}</a>', E(short(r["intervention"])),
            E(r["time_from_last_treatment"]), E(tiers), ("" if lasting else "No", "no"),
        ])
    return table(["Study", "Treatment", "Assessed how long after the last treatment", "What was measured",
                  "Lasting match measured"], body)


def sc_study_cards(ctx):
    study_fields = (("diagnosis", "Diagnosis"), ("design", "Design"), ("patients_enrolled", "Patients"),
                    ("patients_evaluable", "Patients evaluable"), ("body_site", "Body site"), ("skin_tone", "Skin tone"),
                    ("endpoint_definition", "Success defined as"), ("assessment_method", "Assessed by"),
                    ("attrition", "Attrition"))
    arm_fields = (("lesions_enrolled", "Spots"), ("comparator", "Compared with"), ("time_from_start", "Time from start"),
                  ("complete_match", "Complete match"), ("dark_overshoot", "Excess pigment"),
                  ("texture_or_scar", "Scar or texture"), ("patient_noticeability", "Patient view"))
    out = ['<div class="cards">']
    for sid, rs in grouped(ctx["evidence"]).items():
        r = rs[0]
        lead = r["verification_status"].startswith("lead")
        out.append(f'<article class="card{" lead" if lead else ""}" id="study-{E(sid)}">')
        out.append(f'<header><h4>{E(short(r["intervention"]).capitalize())} · {E(study_label(sid))}</h4>'
                   f'<span class="tag human">{"Lead, not extracted" if lead else "Published human finding"}</span></header>')
        out.append(f'<p class="cite">{E(r["citation"])} · {link(r["source_url"], "source")} · {E(r["source_location"])}</p>')
        out.append(f'<p class="cite">{E(r["diagnosis"])} · {E(r["design"])} · patients: {E(r["patients_enrolled"])} · site: {E(r["body_site"])}</p>')
        for a in rs:
            out.append(f'<div class="arm"><h5>{E(a["intervention"])}</h5>')
            out.append(f'<span class="pill">After last treatment: {E(a["time_from_last_treatment"])}</span>')
            out.append(f'<p class="result">{E(a["arm_result"])}</p>')
            if not lead:
                out.append(f'<dl><dt>Excess pigment</dt><dd>{E(a["dark_overshoot"])}</dd>'
                           f'<dt>Complete match</dt><dd>{E(a["complete_match"])}</dd></dl>')
            out.append(f'<p class="issue">{E(a["uncertainty"])}</p></div>')
        if not lead:
            out.append("<details><summary>All extracted fields</summary><dl>")
            out += [f"<dt>{lab}</dt><dd>{E(r[k])}</dd>" for k, lab in study_fields]
            out.append("</dl>")
            for a in rs:
                out.append(f'<p class="status">{E(short(a["intervention"]))}</p><dl>')
                out += [f"<dt>{lab}</dt><dd>{E(a[k])}</dd>" for k, lab in arm_fields]
                out.append("</dl>")
            out.append("</details>")
        out.append(f'<p class="status">{E(r["verification_status"])} · {E(r["access_level"])} · {E(r["doi_or_pmid"])}</p>')
        out.append("</article>")
    out.append("</div>")
    return "".join(out)


def sc_corrections(ctx):
    out = ['<div class="cards">']
    for r in rows("corrections.csv"):
        out.append(f'<article class="card"><h4>{E(r["item"])}</h4><dl>'
                   f'<dt>Brief said</dt><dd>{E(r["seed_brief_said"])}</dd>'
                   f'<dt>Source shows</dt><dd>{E(r["what_the_source_shows"])}</dd>'
                   f'<dt>Effect</dt><dd>{E(r["effect"])}</dd></dl>'
                   f'<p class="status">{E(r["source"])}</p></article>')
    return "".join(out) + "</div>"


def sc_search_log(ctx):
    body = [[E(r["source"]), f'<code>{E(r["query_or_action"])}</code>' if r["hits"] else E(r["query_or_action"]),
             E(r["hits"]), E(r["result"]), E(r["notes"])] for r in rows("search_log.csv")]
    return table(["Source", "Query or action", "Hits", "Result", "Notes"], body, num_cols=(2,))


def sc_screening(ctx):
    sc = rows("screening_log.csv")
    counts = Counter(r["decision"] for r in sc)
    summary = "; ".join(f"{v} {E(k)}" for k, v in counts.most_common())
    body = [[E(r["record_id"]), E(r["title"]), E(r["decision"]), E(r["reason"])] for r in sc]
    return (f"<details><summary>Screening decisions for {len(sc)} records ({summary})</summary>"
            + table(["Record", "Title", "Decision", "Reason"], body) + "</details>")


def sc_hypotheses(ctx):
    out = ['<div class="cards">']
    for r in rows("hypotheses.csv"):
        out.append(f'<article class="card hypo"><header><h4>{E(r["hypothesis"])}</h4>'
                   f'<span class="tag hypo">{E(r["status"])}</span></header><dl>'
                   f'<dt>Observation</dt><dd>{E(r["supporting_observation"])}</dd>'
                   f'<dt>Would weaken it</dt><dd>{E(r["what_would_weaken_it"])}</dd></dl>'
                   f'<p class="status">{E(r["source"])}</p></article>')
    return "".join(out) + "</div>"


def sc_paths(ctx):
    out = ['<div class="cards">']
    for r in rows("paths.csv"):
        out.append(f'<article class="card path"><header><h4>{E(r["rank"])}. {E(r["path"])}</h4></header><dl>'
                   f'<dt>Real owner or dataset</dt><dd>{E(r["real_owner_or_dataset"])}</dd>'
                   f'<dt>Confirmed contents</dt><dd>{E(r["confirmed_contents"])}</dd>'
                   f'<dt>Access today</dt><dd>{E(r["access_today"])}</dd>'
                   f'<dt>Seven-day result</dt><dd>{E(r["seven_day_result"])}</dd>'
                   f'<dt>Could change</dt><dd>{E(r["what_it_could_change"])}</dd>'
                   f'<dt>Main risk</dt><dd>{E(r["main_risk"])}</dd></dl></article>')
    return "".join(out) + "</div>"


def sc_datasets(ctx):
    out = ['<div class="cards">']
    for r in rows("datasets.csv"):
        out.append(f'<article class="card data"><header><h4>{E(r["lead"])}</h4>'
                   f'<span class="pill">{E(r["path"])}</span></header>'
                   f'<p class="cite">{E(r["owner"])}</p><dl>'
                   f'<dt>What exists</dt><dd>{E(r["what_exists"])}</dd>'
                   f'<dt>IGH-specific</dt><dd>{E(r["igh_specific"])}</dd>'
                   f'<dt>Same spot before and after</dt><dd>{E(r["same_spot_before_after"])}</dd>'
                   f'<dt>Access</dt><dd>{E(r["access"])}</dd>'
                   f'<dt>One question</dt><dd>{E(r["one_question_for_owner"])}</dd></dl>'
                   f'<p class="status">Checked: {E(r["checked_how"])}</p></article>')
    return "".join(out) + "</div>"


def sc_validation_table(ctx):
    v = [r for r in rows("alignment_validation.csv") if r["check"] == "equal_circles" and r["px_per_mm"] == "40"]
    body = [[r["diameter_mm"].rstrip("0").rstrip(".") + " mm", r["shift_mm"] + " mm", f'{float(r["analytic_loss_pct"]):.1f}%',
             f'{float(r["raster_loss_pct"]):.1f}%', f'{float(r["difference_pct_points"]):+.3f}'] for r in v]
    return table(["Spot", "Outline off by", "Formula", "Pixel model (40 px/mm)", "Gap, points"], body, num_cols=(2, 3, 4))


SCEN_WORDS = OrderedDict([
    ("unchanged", "Nothing changed"), ("genuine_fading", "Contrast truly halves"),
    ("shrinking", "Spot shrinks to 0.7 of its diameter"), ("dark_overshoot", "Spot ends darker than skin"),
    ("nearby_skin_darkens", "Nearby skin darkens, spot unchanged"),
])
OUTLINE_WORDS = OrderedDict([
    ("fixed_misaligned", "Fixed outline, misplaced"), ("registered", "Outline re-registered"),
    ("traced_mean", "Redrawn outline, mean contrast"), ("traced_integrated", "Redrawn outline, contrast x area"),
])


def sc_results_table(ctx):
    res = [r for r in rows("alignment_results.csv") if r["shift_mm"] == "0.25"]
    body = []
    for sc, sw in SCEN_WORDS.items():
        true = next(r["true_change_pct"] for r in res if r["scenario"] == sc)
        for ol, ow in OUTLINE_WORDS.items():
            cells = []
            for d in ("2.0", "3.0", "5.0"):
                r = next(x for x in res if x["scenario"] == sc and x["outline"] == ol and x["diameter_mm"] == d)
                if r["signed_bias_pct_points"] == "":
                    cells.append((f'rejected {r["rejected"]}/{r["trials"]}', "no"))
                else:
                    cells.append((f'{float(r["signed_bias_pct_points"]):+.1f} ± {float(r["sd_pct_points"]):.1f}', "num"))
            body.append([E(sw) + f' <span class="status">(true {float(true):+.0f}%)</span>', E(ow)] + cells)
    ms = {r["outline"]: r["ms_per_measurement"] for r in res if r["diameter_mm"] == "3.0" and r["scenario"] == "unchanged"}
    note = (f'<p class="status">Cells show signed bias ± spread, in percentage points of baseline contrast, at 0.25 mm displacement. '
            f'Time per measurement on a 256 × 256 image: fixed {ms["fixed_misaligned"]} ms, re-registered {ms["registered"]} ms, '
            f'redrawn {ms["traced_mean"]} ms.</p>')
    return table(["Situation", "Outline method", "2 mm spot", "3 mm spot", "5 mm spot"], body) + note


def sc_alignment_widget(ctx):
    res = [r for r in rows("alignment_results.csv") if r["scenario"] == "unchanged" and r["outline"] == "fixed_misaligned"]
    sim = {f'{float(r["diameter_mm"]):.1f}|{float(r["shift_mm"]):.2f}': float(r["measured_mean_pct"]) for r in res}
    return f'''<div class="widget" id="align-widget" data-sim="{E(json.dumps(sim), quote=True)}">
<p><span class="tag sim">Simulation</span> Adjust the spot and the placement error. The filled disk is the spot. The dashed ring is the outline as placed at the second visit.</p>
<svg viewBox="0 0 300 200" role="img" aria-label="A light spot on skin with a displaced dashed outline">
<rect width="300" height="200" fill="#c59a7c"/>
<circle id="aw-spot" cx="150" cy="100" r="30" fill="#ead6c6"/>
<circle id="aw-base" cx="150" cy="100" r="30" fill="none" stroke="#ffffff" stroke-opacity=".55" stroke-width="1"/>
<circle id="aw-outline" cx="157.5" cy="100" r="30" fill="#1b282d" fill-opacity=".12" stroke="#1b282d" stroke-width="1.6" stroke-dasharray="5 4"/>
<line x1="16" y1="184" x2="46" y2="184" stroke="#1b282d" stroke-width="2"/>
<text x="52" y="188" font-family="monospace" font-size="11" fill="#1b282d">1 mm</text>
</svg>
<div class="controls">
<label for="aw-d">Spot diameter <output id="aw-d-out" for="aw-d">2.0 mm</output>
<input type="range" id="aw-d" min="1" max="6" step="0.5" value="2"></label>
<label for="aw-s">Outline placed off-centre by <output id="aw-s-out" for="aw-s">0.25 mm</output>
<input type="range" id="aw-s" min="0" max="1.5" step="0.05" value="0.25"></label>
</div>
<div class="readout">
<div><b id="aw-loss">15.9%</b><span>apparent fading, sharp-edge formula, with nothing changed</span></div>
<div><b id="aw-px">10.0%</b><span>pixel model with blur and noise (run at 2, 3, 5 mm and 0, 0.25, 0.5 mm only)</span></div>
<div><b id="aw-ratio">13%</b><span>placement error as a share of spot diameter</span></div>
</div>
</div>'''


def sc_clustering_table(ctx):
    cl = rows("clustering_sensitivity.csv")
    diff = [r for r in cl if r["kind"] == "difference_between_arms"]
    body = [[r["assumed_icc"], r["design_effect"], r["effective_spots_per_arm"], f'{r["estimate_pct"]} points',
             f'{r["ci95_low_pct"]} to {r["ci95_high_pct"]}', r["p_two_sided"]] for r in diff]
    t1 = table(["Assumed within-person correlation", "Design effect", "Effective spots per arm",
                "Cryotherapy minus TCA, >75% repigmented", "95% interval", "p"], body, num_cols=(0, 1, 2, 5))
    single = [r for r in cl if r["kind"] == "single_arm_proportion" and r["assumed_icc"] in ("0.0", "0.5", "1.0")]
    body = [[E(r["quantity"]), r["assumed_icc"], f'{r["estimate_pct"]}%', f'{r["ci95_low_pct"]} to {r["ci95_high_pct"]}'] for r in single]
    t2 = table(["Excimer series", "Assumed correlation", "Estimate", "95% interval"], body, num_cols=(1,))
    src = "; ".join(sorted({r["source"] for r in cl}))
    return t1 + t2 + f'<p class="status">Counts from {E(src)}. Normal approximation.</p>'


def sc_denominator_table(ctx):
    body = [[E(study_label(r["study_id"])), E(r["quantity"]), r["published_pct"] + "%", f'{r["stated_n"]} {E(r["unit"])}',
             E(r["nearest_whole_counts"]), (r["consistent_with_stated_n"], "no" if r["consistent_with_stated_n"] == "NO" else "")]
            for r in rows("denominator_audit.csv")]
    return table(["Study", "Quantity", "Published", "Stated number", "Nearest whole counts", "Fits"], body)


def code_block(lines):
    return "<pre><code>" + E("\n".join(lines)) + "</code></pre>"


def sc_reproduce_sim(ctx):
    return ("<p><strong>Reproduce it.</strong> Needs Python 3.9 or later and numpy. Runs in about two minutes.</p>"
            + code_block(["python3 experiments/alignment.py            # the seed brief's formula, unchanged",
                          "python3 experiments/alignment_pixel_sim.py --out data"])
            + files(ctx, ["alignment_results.csv", "alignment_validation.csv"], ["alignment.py", "alignment_pixel_sim.py"]))


def sc_reproduce_calc(ctx):
    return (code_block(["python3 experiments/clustering_sensitivity.py --out data",
                        "python3 experiments/denominator_audit.py --out data"])
            + files(ctx, ["clustering_sensitivity.csv", "denominator_audit.csv"],
                    ["clustering_sensitivity.py", "denominator_audit.py"]))


def files(ctx, data_files, code_files=()):
    out = ['<ul class="files">']
    for name in data_files:
        n = len(rows(name))
        ctx["embed"].add(name)
        out.append(f'<li><span>{link("data/" + name, name)}<small>{n} rows · CSV</small></span>'
                   f'<button class="copy" type="button" data-src="csv-{E(name)}">Copy CSV</button></li>')
    for name in code_files:
        out.append(f'<li><span>{link("experiments/" + name + ".txt", name)}<small>Python source, shown as text</small></span></li>')
    return "".join(out) + "</ul>"


def sc_downloads_evidence(ctx):
    src = rows("sources.csv")
    body = [[link(r["url"], r["url"].split("//")[1][:46] + ("…" if len(r["url"]) > 54 else "")), E(r["what_it_is"]),
             E(r["how_it_was_checked"]), E(r["origin"])] for r in src]
    seed = sum(1 for r in src if r["origin"] == "seed brief")
    return (files(ctx, ["evidence.csv", "sources.csv", "screening_log.csv", "search_log.csv", "corrections.csv",
                        "datasets.csv", "paths.csv", "hypotheses.csv"])
            + '<p class="status">File links download when the site is hosted. Inside a preview frame use Copy CSV.</p>'
            + f"<details><summary>All {len(src)} source links ({seed} from the starting brief, each kept)</summary>"
            + table(["Link", "What it is", "How it was checked", "Origin"], body) + "</details>")


def sc_contact(ctx):
    c = ctx["site"]["contact"]
    what = ("<p>A useful correction names the <code>study_id</code>, the field, the value you believe is right and "
            "where it appears in the source (table, figure or abstract section).</p>")
    if c.get("issues_url") or c.get("email"):
        ways = []
        if c.get("issues_url"):
            ways.append(f'Open an issue: {link(c["issues_url"], c["issues_url"])}')
        if c.get("email"):
            ways.append(f'Email: {link("mailto:" + c["email"], c["email"])} ({E(c["email"])})')
        return "<ul>" + "".join(f"<li>{w}</li>" for w in ways) + "</ul>" + what
    return ('<div class="placeholder"><strong>Contact route not set yet.</strong> This site has not been launched. '
            "An issue tracker link or an email address will appear here before it is. "
            "(Set <code>contact</code> in <code>site.json</code> and rebuild.)</div>" + what)


def sc_contributors(ctx):
    items = "".join(f'<li><strong>{E(p["name"])}</strong>. {E(p["role"])}</li>' for p in ctx["site"]["contributors"])
    return f'<div class="people"><p class="eyebrow">Contributors</p><ul>{items}</ul></div>'


SHORTCODES = {k[3:]: v for k, v in list(globals().items()) if k.startswith("sc_")}


def render(md_text, ctx):
    body = markdown.markdown(md_text, extensions=["tables", "sane_lists"])

    def sub(m):
        name = m.group(1)
        if name not in SHORTCODES:
            raise SystemExit(f"unknown shortcode {{{{{name}}}}}")
        return SHORTCODES[name](ctx)
    return re.sub(r"<p>\{\{(\w+)\}\}</p>", sub, body)


def main():
    site = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
    ctx = {"site": site, "evidence": rows("evidence.csv"), "embed": set()}
    sections, nav = [], []
    for i, s in enumerate(site["sections"]):
        inner = render((CONTENT / s["file"]).read_text(encoding="utf-8"), ctx)
        sections.append(f'<section class="view{" active" if i == 0 else ""}" id="{E(s["id"])}">{inner}</section>')
        cur = ' aria-current="page"' if i == 0 else ""
        nav.append(f'<a href="#{E(s["id"])}"{cur}>{E(s["nav"])}</a>')
    embeds = "".join(
        f'<textarea hidden readonly id="csv-{E(n)}">{E((DATA / n).read_text(encoding="utf-8"))}</textarea>'
        for n in sorted(ctx["embed"]))
    page = (TPL / "base.html").read_text(encoding="utf-8")
    for key, val in {
        "TITLE": E(site["title"]), "QUESTION": E(site["question"], quote=True), "UPDATED": E(site["updated"]),
        "NAV": "".join(nav), "SECTIONS": "\n".join(sections), "EMBEDS": embeds,
        "STYLE": (TPL / "style.css").read_text(encoding="utf-8"), "SCRIPT": (TPL / "app.js").read_text(encoding="utf-8"),
    }.items():
        page = page.replace("{{" + key + "}}", val)
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    (DIST / "index.html").write_text(page, encoding="utf-8")
    shutil.copytree(DATA, DIST / "data")
    shutil.copytree(ROOT / "experiments", DIST / "experiments", ignore=shutil.ignore_patterns("__pycache__"))
    for py in (DIST / "experiments").glob("*.py"):  # .txt twins open in a browser tab instead of downloading
        shutil.copyfile(py, py.with_name(py.name + ".txt"))
    (DIST / ".nojekyll").write_text("", encoding="utf-8")
    n_files = sum(1 for p in DIST.rglob("*") if p.is_file())
    print(f"built dist/index.html ({len(page) / 1024:.0f} KB) and {n_files - 1} supporting files")


if __name__ == "__main__":
    main()
