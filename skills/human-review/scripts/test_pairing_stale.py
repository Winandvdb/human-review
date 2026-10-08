#!/usr/bin/env python3
"""A pairing older than the coverage it should have read says so — and never re-runs itself.

The visit-vet demo (5 Oct 2026): the model paired the ticket's sentences at 19:35 over 30
candidate tests, no e2e among them, and the coverage that put the e2e runs on changed lines
was written at 21:10. Every build after that drew the matrix as if the model had read those
tests, and nothing on the page or in the terminal said otherwise. Now:

- `rerun-model.py` records in `test-mapping.json` which tests the model was shown
  (`offered`), and the schema accepts it;
- the build (`semcov.write_fragment`) calls the pairing stale when `test-mapping.json` is
  older than `assets/test-coverage.json`, or when today's candidates include a test it was
  never shown — warns loudly on stderr, puts a small note with the command over the ticket,
  and records why in the merged mapping;
- `refresh-report.py` repeats that warning as its last word;
- nothing here ever calls a model.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from test_semcov import S, _repo  # noqa: E402 — the same throwaway repository


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


M = _load("rerun_model", "rerun-model.py")
R = _load("refresh_report", "refresh-report.py")


def _age(path: Path, seconds: float) -> None:
    """Move a file's mtime `seconds` into the past."""
    t = path.stat().st_mtime - seconds
    os.utime(path, (t, t))


def _mapping(review: Path, **extra) -> Path:
    p = review / S.MAPPING
    p.write_text(json.dumps({"schema": "test-mapping/1", "sentences": [], **extra}),
                 encoding="utf-8")
    return p


def test_no_mapping_is_not_stale(tmp_path):
    _, review = _repo(tmp_path)
    assert S.pairing_stale(review) is None


def test_a_mapping_older_than_the_coverage_is_stale(tmp_path):
    _, review = _repo(tmp_path)
    _age(_mapping(review), 3600)
    why = S.pairing_stale(review)
    assert why and "test-mapping.json" in why and "older than test-coverage.json" in why


def test_a_mapping_newer_than_the_coverage_is_not(tmp_path):
    _, review = _repo(tmp_path)
    _age(review / S.COVERAGE, 3600)
    _mapping(review)
    assert S.pairing_stale(review) is None


def test_a_candidate_the_model_was_never_shown_makes_it_stale_whatever_the_clock_says(tmp_path):
    _, review = _repo(tmp_path)
    _age(review / S.COVERAGE, 3600)
    _mapping(review, offered=["test/VisitTest.java:3"])
    assert S.pairing_stale(review, ["test/VisitTest.java:3"]) is None
    why = S.pairing_stale(review, ["test/VisitTest.java:3", "e2e/add-visit.spec.ts:31"])
    assert why and "1 candidate test(s) the model was never shown: add-visit.spec.ts:31" in why


def test_the_schema_accepts_what_the_model_was_shown():
    doc = {"schema": "test-mapping/1", "sentences": [], "offered": ["a/B.java:3"]}
    assert S.problems(doc) == []
    assert any("offered" in p for p in S.problems({**doc, "offered": "a/B.java:3"}))


def test_rerun_model_records_the_tests_it_offered(tmp_path, monkeypatch):
    """`--answer` is the no-cost path through the same install as a paid run."""
    root, review = _repo(tmp_path)
    monkeypatch.chdir(root)
    g = S.gather(S._spec(review), review, root)
    asked = S.model_input(g["ticket"], g["sentences"], g["rows"], g["scripted"], g["docs"],
                          g["decisions"])
    reply = {"schema": "test-mapping/1", "sentences": [
        {"id": x["id"], "coverage": "missing", "tests": [],
         **({"review": [{"id": t["id"], "verdict": "reject", "why": "no"}
                        for t in x["scripted"]]} if x["scripted"] else {})}
        for x in asked["sentences"]]}
    (tmp_path / "reply.json").write_text(json.dumps(reply), encoding="utf-8")
    assert M.main(["--dir", ".human-review", "--answer", str(tmp_path / "reply.json")]) == 0
    written = json.loads((review / S.MAPPING).read_text())
    assert written["offered"] == [t["id"] for t in asked["tests"]] and written["offered"]
    assert S.load_model_mapping(review) is not None


def test_the_build_warns_and_the_page_says_so(tmp_path, capsys):
    root, review = _repo(tmp_path)
    _age(_mapping(review), 3600)
    S.write_fragment(S._spec(review), review, root)
    err = capsys.readouterr().err
    assert "WARNING: the Tests tab's pairing predates the coverage run" in err
    assert "rerun-model.py" in err
    page = (review / S.FRAGMENT).read_text()
    assert '<span class="rm-stale-badge" role="note"' in page
    assert "<p class=\"rm-stale\"" not in page, "no banner any more"
    assert f"{S.STALE_NOTE} rerun-model.py {S.STALE_TAIL}" in page
    assert 'class="rm-stale-ai"' in page and "\U0001F916</button>" in page
    merged = json.loads((review / S.MERGED).read_text())
    assert merged["stale"]["command"] == "rerun-model.py"
    assert "older than test-coverage.json" in merged["stale"]["why"]


def test_a_fresh_pairing_draws_no_note(tmp_path, capsys):
    root, review = _repo(tmp_path)
    _age(review / S.COVERAGE, 3600)
    _mapping(review)
    S.write_fragment(S._spec(review), review, root)
    assert "predates" not in capsys.readouterr().err
    assert "rm-stale-badge" not in (review / S.FRAGMENT).read_text().split("</style>", 1)[1]
    assert "stale" not in json.loads((review / S.MERGED).read_text())


def test_the_command_names_a_review_directory_that_is_not_the_default(tmp_path):
    root = tmp_path / "repo"
    assert S.rerun_command(root / ".human-review", root) == "rerun-model.py"
    assert S.rerun_command(root / "out" / "hr", root) == "rerun-model.py --dir out/hr"


def test_refresh_repeats_the_warning_only_for_its_own_build(tmp_path, capsys):
    review = tmp_path / ".human-review"
    (review / "assets").mkdir(parents=True)
    merged = review / R.MERGED_MAPPING
    merged.write_text(json.dumps({"sentences": [], "stale": {
        "why": "test-mapping.json (05 Oct 19:35) is older than test-coverage.json",
        "command": "rerun-model.py"}}), encoding="utf-8")
    got = R.stale_pairing(review, since=merged.stat().st_mtime - 1)
    assert got and got["command"] == "rerun-model.py"
    # A merged file an earlier build left says nothing about this one.
    assert R.stale_pairing(review, since=merged.stat().st_mtime + 60) is None
    R.warn_stale_pairing(got)
    err = capsys.readouterr().err
    assert "WARNING: the Tests tab's pairing predates the coverage run" in err
    assert "rerun-model.py" in err and "paid model call" in err


def test_nothing_on_the_stale_path_calls_a_model(tmp_path, monkeypatch):
    """The warning names the command; it never runs it."""
    import subprocess
    root, review = _repo(tmp_path)
    _age(_mapping(review), 3600)
    calls = []
    real = subprocess.run

    def spy(argv, *a, **k):
        if argv and argv[0] == "claude" or "rerun-model.py" in " ".join(map(str, argv)):
            calls.append(argv)
        return real(argv, *a, **k)
    monkeypatch.setattr(subprocess, "run", spy)
    S.write_fragment(S._spec(review), review, root)
    assert calls == []
