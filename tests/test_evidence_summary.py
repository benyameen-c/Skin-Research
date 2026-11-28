import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT, PAGE = ROOT / "tools" / "evidence_summary.py", ROOT / "content" / "evidence-summary.md"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, cwd=ROOT)


def test_counts_run():
    r = run()
    assert r.returncode == 0 and "ledger rows:" in r.stdout


def test_page_numbers_are_quoted():
    r = run("--check", str(PAGE))
    assert r.returncode == 0, r.stdout


def test_unquoted_number_is_caught(tmp_path):
    page = tmp_path / "page.md"
    page.write_text(PAGE.read_text(encoding="utf-8").replace("115 patients (47.9%)", "115 patients (47.8%)"),
                    encoding="utf-8")
    r = run("--check", str(page))
    assert r.returncode == 1 and "47.8" in r.stdout


def test_uncited_number_is_caught(tmp_path):
    page = tmp_path / "page.md"
    page.write_text("## Page\n\nA treatment worked in 93% of spots.\n", encoding="utf-8")
    r = run("--check", str(page))
    assert r.returncode == 1 and "none cited" in r.stdout
