"""The redesigned page (`hrbuild/page/render.py`), switched on by `"page": {"layout": "new"}`.

Built the way the skill builds it, from a content file, with `$HUMAN_REVIEW_LAYOUT` instead
of a project config so the test needs no checkout of its own.
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

SPEC = {
    "title": "#12: Show won tricks as piles",
    "summary": "<p>Each team's won tricks now lie as a pile.</p>",
    "pr": {"number": 73, "title": "#12: Show won tricks as piles",
           "url": "https://github.com/o/r/pull/73", "repo": "https://github.com/o/r",
           "branch": "feature/12-piles", "base": "develop"},
    "verdict": {"score": 7, "bullets": ["No test renders the table."]},
    "assumptions": [
        {"source": "assumption", "title": "Ring in team colour", "alternative": "A label",
         "why": "Colours already mean teams.", "confidence": 0.8},
        {"source": "assumption", "title": "One pile per team", "alternative": "Per seat",
         "why": "A team is two seats.", "confidence": 0.6}],
    "findings": [{"severity": "low", "source": "/code-review", "title": "Counts show",
                  "body": "The pile ignores scores.", "why": "Piles are visible."}],
    "autofixes": [{"severity": "low", "source": "/code-review", "title": "Pile moved",
                   "body": "It moved.", "fix": "Keep the box size."}],
    "sections": [{"id": "notes", "title": "Notes", "body": "<p>a diagram</p>"},
                 {"id": "city", "title": "City", "body": "<p>a city</p>"}],
    "tabs": [{"id": "review", "label": "Review",
              "blocks": [{"type": "findings"}, {"type": "assumptions"}, {"type": "autofixes"}]},
             {"id": "notes", "label": "Notes",
              "blocks": [{"type": "section", "id": "notes"}]},
             {"id": "city", "label": "Code City", "blocks": [{"type": "section", "id": "city"}]}],
}


def _build(tmp_path: Path, spec: dict) -> str:
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_SESSION_ID"}
    env.update(HOME=str(home), HUMAN_REVIEW_LAYOUT="new")
    src = tmp_path / "content.json"
    src.write_text(json.dumps(spec), encoding="utf-8")
    out = tmp_path / "review.html"
    proc = subprocess.run([sys.executable, str(HERE / "build-review-html.py"), str(src),
                           "--out", str(out)], capture_output=True, text=True, env=env)
    assert proc.returncode == 0, proc.stderr
    return out.read_text(encoding="utf-8")


def _panel(page: str, pid: str) -> str:
    start = page.index(f'data-np-panel="{pid}"')
    end = page.find('class="np-panel', start)
    return page[start:end if end > 0 else len(page)]


def test_the_page_opens_on_what_changed_and_has_the_review_tabs(tmp_path):
    page = _build(tmp_path, SPEC)
    tabs = re.findall(r'data-np-tab="([\w-]+)"', page)
    assert tabs[:3] == ["changed", "decide", "fixed"], "the review flow first"
    assert tabs[-1] == "cost" or "cost" not in tabs
    assert page.index('data-np-panel="changed"') < page.index('data-np-panel="decide"')
    assert "won tricks now lie as a pile" in _panel(page, "changed")
    assert "Show won tricks as piles</h1>" in page, "the PR title, without its #12: prefix"


def test_the_least_sure_choice_comes_first_and_every_point_is_numbered(tmp_path):
    """On the renderer itself: the build takes assumptions only from `review-points.md`."""
    sys.path.insert(0, str(HERE))
    render = importlib.import_module("hrbuild.page.render")
    decide, total = render._np_decisions(SPEC, tmp_path)
    assert total == 3
    assert decide.index("One pile per team") < decide.index("Ring in team colour")
    assert decide.index("Ring in team colour") < decide.index("Counts show")
    assert re.findall(r'np-num-sq">(\d+)<', decide) == ["1", "2", "3"]
    assert "60% sure" in decide and "Not fixed because:" in decide


def test_the_fixes_have_a_tab_of_their_own(tmp_path):
    fixed = _panel(_build(tmp_path, SPEC), "fixed")
    assert "Pile moved" in fixed and "Keep the box size." in fixed


def test_a_view_keeps_its_old_panel_and_code_city_is_gone(tmp_path):
    page = _build(tmp_path, SPEC)
    assert 'data-np-tab="notes"' in page and "np-viewtab" in page
    view = page[page.index('data-np-panel="notes"'):]
    assert '<section class="panel" id="notes"' in view[:400] and "a diagram" in view
    assert 'data-np-tab="city"' not in page and "a city" not in page


def test_next_for_you_points_at_the_decisions(tmp_path):
    changed = _panel(_build(tmp_path, SPEC), "changed")
    assert 'data-np-go="decide"' in changed and "Decisions wait for you" in changed


def _rerun_model():
    spec = importlib.util.spec_from_file_location("rerun_model_np", HERE / "rerun-model.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_a_paid_pairing_says_which_model_made_it_and_when(tmp_path):
    """A second "Rerun with AI" once rewrote the map with a different answer, and
    nothing on the page said that the map on screen was the second of two."""
    out = _rerun_model().install(tmp_path, {"sentences": []}, by="sonnet")
    stamp = json.loads(out.read_text())["pairedBy"]
    assert stamp["model"] == "sonnet" and stamp["at"].endswith("+00:00")


def test_the_map_says_which_run_made_it_and_that_an_earlier_one_is_kept(tmp_path):
    sys.path.insert(0, str(HERE))
    render = importlib.import_module("hrbuild.page.render")
    (tmp_path / ".model-runs.json").write_text(json.dumps({"version": 1, "runs": [
        {"when": "2026-10-08T12:23:13+00:00", "model": "sonnet"},
        {"when": "2026-10-08T18:49:13+00:00", "model": "sonnet"}]}))
    mapping = {"pairedBy": {"model": "sonnet", "at": "2026-10-08T18:49:13+00:00"}}
    (tmp_path / ".model-prev").mkdir()
    (tmp_path / ".model-prev" / "test-mapping.json").write_text("{}")
    line = render._np_provenance(tmp_path, mapping)
    assert "Paired by sonnet" in line and "run 2 of 2" in line
    assert ".model-prev/test-mapping.json" in line, "the earlier answer is named"


def test_an_unstamped_map_is_matched_to_its_run_by_time(tmp_path):
    sys.path.insert(0, str(HERE))
    render = importlib.import_module("hrbuild.page.render")
    (tmp_path / ".model-runs.json").write_text(json.dumps({"version": 1, "runs": [
        {"when": "2026-10-08T12:23:13+00:00", "model": "sonnet"},
        {"when": "2026-10-08T18:49:13+00:00", "model": "sonnet"}]}))
    f = tmp_path / "test-mapping.json"
    f.write_text("{}")
    import datetime
    t = datetime.datetime(2026, 10, 8, 12, 23, 14, tzinfo=datetime.timezone.utc).timestamp()
    os.utime(f, (t, t))
    assert "run 1 of 2" in render._np_provenance(tmp_path, {})


def test_the_old_layout_is_still_the_default(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    env = {k: v for k, v in os.environ.items()
           if k not in ("CLAUDE_CODE_SESSION_ID", "HUMAN_REVIEW_LAYOUT")}
    env["HOME"] = str(home)
    src = tmp_path / "content.json"
    src.write_text(json.dumps(SPEC), encoding="utf-8")
    out = tmp_path / "review.html"
    proc = subprocess.run([sys.executable, str(HERE / "build-review-html.py"), str(src),
                           "--out", str(out)], capture_output=True, text=True, env=env)
    assert proc.returncode == 0, proc.stderr
    assert 'class="np"' not in out.read_text(encoding="utf-8")
