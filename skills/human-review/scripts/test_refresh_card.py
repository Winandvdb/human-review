#!/usr/bin/env python3
"""A draw.io card's own ring: redraw one picture and splice it into the page, in about a
second instead of forty — and land on exactly the page the slow way builds.

The slow way is the tab's ring: `refresh-report.py --steps diagrams`, every PlantUML delta
re-rendered and the whole page rebuilt. The fast way (`refresh-card.py`) re-runs the one
`drawio-diff.py` the card was drawn by and replaces the card in `review.html`. Nothing about
it is allowed to show: the page it leaves must be the page a full build writes, byte for
byte, manifest included. The first tests here build both and compare them.

The rest pin what makes it fast: draw.io's exports kept by what they were drawn from (a hit
is the file the app wrote, so a hit and a miss cannot differ), the history walk in one
`git cat-file --batch`, the server answering the press with the card itself, and the
watcher that has the pictures drawn before the press.

Run with:  python3 -m pytest test_refresh_card.py
"""
from __future__ import annotations

import functools
import http.client
import importlib.util
import json
import os
import socketserver
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dd = _load("drawio_diff_card", "drawio-diff.py")
srv = _load("serve_review_card", "serve-review.py")

BASE = ('<mxfile host="t"><diagram id="d" name="p"><mxGraphModel><root><mxCell id="0"/>'
        '<mxCell id="1" parent="0"/>'
        '<object label="Owner" concept="Owner" id="c-owner"><mxCell parent="1" '
        'style="rounded=0;" vertex="1"><mxGeometry x="40" y="0" width="120" height="40" '
        'as="geometry"/></mxCell></object>'
        '<object label="Pet" concept="Pet" id="c-pet"><mxCell parent="1" style="rounded=0;" '
        'vertex="1"><mxGeometry x="{pet}" y="0" width="120" height="40" as="geometry"/>'
        '</mxCell></object></root></mxGraphModel></diagram></mxfile>')

CONTENT = {"title": "t",
           "sections": [{"id": "conceptual", "title": "", "body": "{{drawio:conceptual}}"}],
           "tabs": [{"id": "data", "label": "Data",
                     "blocks": [{"type": "section", "id": "conceptual"}]}]}


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                          text=True).stdout


def _env(tmp_path):
    """The build's environment with the machine held still (see test_build_review._build):
    no transcripts to cost, no session, no shared render cache."""
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_SESSION_ID"}
    env["HOME"] = str(tmp_path / "home")
    env["HUMAN_REVIEW_DRAWIO_CACHE"] = str(tmp_path / "cache")
    (tmp_path / "home").mkdir(exist_ok=True)
    return env


def _run(repo, env, *argv):
    proc = subprocess.run([sys.executable, *map(str, argv)], cwd=repo, env=env,
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return proc


def _review(tmp_path, pet_on_branch=260):
    """A checkout with a drawing committed, moved on the branch, diffed and built — the
    state a reader is in when they open the card."""
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    for k, v in (("user.email", "t@t"), ("user.name", "t"), ("commit.gpgsign", "false")):
        _git(repo, "config", k, v)
    (repo / "docs" / "M.drawio").write_text(BASE.format(pet=240), encoding="utf-8")
    (repo / "docs" / "M.puml").write_text("@startuml\nclass Owner\nclass Pet\n@enduml\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base")
    (repo / "docs" / "M.drawio").write_text(BASE.format(pet=pet_on_branch), encoding="utf-8")
    env = _env(tmp_path)
    review = repo / ".human-review"
    review.mkdir()
    (review / "content.json").write_text(json.dumps(CONTENT), encoding="utf-8")
    _run(repo, env, HERE / "drawio-diff.py", "--base", "HEAD", "--diagram", "docs/M.drawio",
         "--concepts", "docs/M.puml", "--out-dir", ".human-review/assets",
         "--name", "conceptual", "--renderer", "builtin")
    _build(repo, env)
    return repo, env


def _build(repo, env):
    _run(repo, env, HERE / "build-review-html.py", ".human-review/content.json",
         "--out", ".human-review/review.html")


def _page(repo):
    review = repo / ".human-review"
    return ((review / "review.html").read_text(encoding="utf-8"),
            json.loads((review / ".actions.json").read_text(encoding="utf-8")))


# ── the fast way lands on the slow way's page ─────────────────────────────────────

def test_the_card_carries_its_own_ring_and_the_tab_s_is_not_added_beside_it(tmp_path):
    repo, _ = _review(tmp_path)
    page, acts = _page(repo)
    assert page.count('data-drawio="conceptual"') == 1
    assert page.count('data-card="conceptual"') == 1
    head = page[page.index('data-drawio="conceptual"'):]
    head = head[:head.index("</b>") + 200]
    assert 'data-tab="data"' not in head, "the tab's ring was stamped on the card as well"
    cmd = acts["actions"]["__rerun__:card:conceptual"]["command"]
    assert "refresh-card.py" in cmd and "--name conceptual" in cmd


def test_the_fast_path_writes_the_page_a_full_build_writes(tmp_path):
    repo, env = _review(tmp_path)
    before, _ = _page(repo)
    (repo / "docs" / "M.drawio").write_text(BASE.format(pet=300), encoding="utf-8")
    out = _run(repo, env, HERE / "refresh-card.py", "--dir", ".human-review",
               "--name", "conceptual").stdout
    assert "redrawn in place" in out, out
    fast, fast_acts = _page(repo)
    assert fast != before, "the card did not change"
    card = (repo / ".human-review" / ".card-conceptual.html").read_text(encoding="utf-8")
    assert card in fast, "the card handed to the page is not the one on disk"
    _build(repo, env)
    slow, slow_acts = _page(repo)
    assert fast == slow
    assert fast_acts == slow_acts


def test_the_splice_keeps_what_was_written_to_the_page_meanwhile(tmp_path):
    """Other hands patch `review.html` in place; the redraw replaces its card and only it."""
    repo, env = _review(tmp_path)
    path = repo / ".human-review" / "review.html"
    path.write_text(path.read_text(encoding="utf-8").replace(
        "</footer>", "<!-- patched by hand --></footer>"), encoding="utf-8")
    (repo / "docs" / "M.drawio").write_text(BASE.format(pet=320), encoding="utf-8")
    _run(repo, env, HERE / "refresh-card.py", "--dir", ".human-review", "--name", "conceptual")
    assert "<!-- patched by hand -->" in path.read_text(encoding="utf-8")


def test_a_drawing_put_back_to_the_base_rebuilds_the_whole_page(tmp_path):
    """Identical to the base strikes the tab through, which is outside the card: the fast
    way gives up and builds the page, and leaves no card for the page to swap in."""
    repo, env = _review(tmp_path)
    (repo / "docs" / "M.drawio").write_text(BASE.format(pet=240), encoding="utf-8")
    out = _run(repo, env, HERE / "refresh-card.py", "--dir", ".human-review",
               "--name", "conceptual").stdout
    assert "rebuilding the whole page" in out
    assert not (repo / ".human-review" / ".card-conceptual.html").exists()
    fast, _ = _page(repo)
    _build(repo, env)
    assert fast == _page(repo)[0]


# ── what makes it fast ────────────────────────────────────────────────────────────

def test_a_cached_export_is_the_file_the_app_wrote(tmp_path, monkeypatch):
    calls = tmp_path / "calls"
    app = tmp_path / "draw.io"
    app.write_text("#!/bin/sh\necho x >> '%s'\n"
                   "while [ \"$1\" != -o ]; do shift; done\n"
                   "printf '<svg>%%s</svg>' \"$(cat \"$3\" | wc -c)\" > \"$2\"\n" % calls)
    app.chmod(0o755)
    monkeypatch.setattr(dd, "DRAWIO_APP", app)
    monkeypatch.setattr(dd, "RENDER_CACHE", tmp_path / "cache")
    first = dd.drawio_export("<mxfile>a</mxfile>")
    again = dd.drawio_export("<mxfile>a</mxfile>")
    other = dd.drawio_export("<mxfile>bb</mxfile>")
    assert first == again and first.startswith("<svg>") and other != first
    assert calls.read_text().count("x") == 2, "the same XML was exported twice"


def test_a_new_app_version_is_not_served_the_old_one_s_exports(tmp_path, monkeypatch):
    monkeypatch.setattr(dd, "_app_identity", lambda: "draw.io 1")
    one = dd.export_key("<mxfile/>")
    monkeypatch.setattr(dd, "_app_identity", lambda: "draw.io 2")
    assert dd.export_key("<mxfile/>") != one


def test_the_history_in_one_batch_reads_what_one_show_per_revision_read(tmp_path,
                                                                         monkeypatch):
    repo = tmp_path / "h"
    (repo / "docs").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    for k, v in (("user.email", "t@t"), ("user.name", "t"), ("commit.gpgsign", "false")):
        _git(repo, "config", k, v)
    shas = []
    for pet in (240, 250, 260):
        (repo / "docs" / "M.drawio").write_text(BASE.format(pet=pet), encoding="utf-8")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-qm", str(pet))
        shas.append(_git(repo, "rev-parse", "HEAD").strip())
    monkeypatch.chdir(repo)
    got = dd.read_many([(s, "docs/M.drawio") for s in shas])
    assert got == {s: dd.read_at(s, "docs/M.drawio") for s in shas}
    assert dd.read_many([(shas[0], "docs/Gone.drawio")]) == {shas[0]: dd.EMPTY_MODEL}


# ── the server answers the press with the card ────────────────────────────────────

@pytest.fixture
def served(tmp_path):
    srv._manifest.update(mtime=None, actions={})
    srv.RUNS.clear()
    srv.ROOT = tmp_path
    srv.Handler.root = str(tmp_path)
    srv.Handler.token = "t"
    (tmp_path / "review.html").write_text("built", encoding="utf-8")
    srv.WATCHER = srv.Watcher(tmp_path, quiet=0)
    httpd = socketserver.ThreadingTCPServer(
        ("127.0.0.1", 0), functools.partial(srv.Handler, directory=str(tmp_path)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        yield httpd.server_address
    finally:
        httpd.shutdown()
        httpd.server_close()
        srv.WATCHER = None


def _post(address, body):
    conn = http.client.HTTPConnection(*address, timeout=30)
    conn.request("POST", srv.RERUN, json.dumps(body),
                 {"Host": f"127.0.0.1:{address[1]}", "Sec-Fetch-Site": "same-origin",
                  "X-Human-Review-Token": "t", "Content-Type": "application/json"})
    r = conn.getresponse()
    out = r.status, r.read().decode()
    conn.close()
    return out


def test_the_press_is_answered_with_the_new_card_and_the_stamp_it_left(served, tmp_path):
    (tmp_path / srv.ACTIONS_FILE).write_text(json.dumps({"version": 1, "actions": {
        "__rerun__:card:conceptual": {
            "command": "printf '<div data-drawio=\"conceptual\">new</div>' > "
                       f"'{tmp_path}/.card-conceptual.html' && echo spliced > "
                       f"'{tmp_path}/review.html'", "params": {}, "reload": True}}}))
    status, payload = _post(served, {"card": "conceptual"})
    assert status == 200, payload
    snap = json.loads(payload)
    assert snap["state"] == "done"
    assert snap["card"] == '<div data-drawio="conceptual">new</div>'
    # The stamp the page adopts is the tree the redraw left, published now: the watcher
    # does not then hand the same change to the page as a reload.
    assert snap["stamp"] == srv.WATCHER.stamp == srv.fingerprint(tmp_path)


def test_a_card_the_build_did_not_declare_is_refused(served, tmp_path):
    (tmp_path / srv.ACTIONS_FILE).write_text(json.dumps({"version": 1, "actions": {}}))
    status, _ = _post(served, {"card": "conceptual"})
    assert status == 404
    status, _ = _post(served, {"card": "../../etc"})
    assert status == 404


# ── the pictures are drawn before the press ───────────────────────────────────────

def test_a_saved_drawing_is_warmed_and_nothing_else_is_written(tmp_path):
    root = tmp_path
    (root / "docs").mkdir()
    drawing = root / "docs" / "M.drawio"
    drawing.write_text("v1")
    fake = root / "drawio-diff.py"
    fake.write_text("#!/bin/sh\necho \"$@\" >> '%s/warmed'\n" % root)
    fake.chmod(0o755)
    assets = root / ".human-review" / "assets"
    assets.mkdir(parents=True)
    (assets / "conceptual-diff.json").write_text(json.dumps({
        "diagram": "docs/M.drawio",
        "rerun": {"cwd": str(root), "command": f"{fake} --name conceptual"}}))
    warmer = srv.DrawioWarmer(root / ".human-review", root, settle=0.0)
    warmer.tick(now=1)
    assert warmer.started == 0, "the page was drawn from this one: nothing to warm"
    drawing.write_text("v2, moved a box")
    warmer.tick(now=2)
    warmer.tick(now=3)
    assert warmer.started == 1
    deadline = time.time() + 5
    while not (root / "warmed").exists() and time.time() < deadline:
        time.sleep(0.02)
    assert (root / "warmed").read_text().split() == ["--name", "conceptual", "--warm"]
