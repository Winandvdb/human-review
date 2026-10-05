"""A `path:from-to` reference opens as a range: the page sends `endLine` beside `line`, the
server checks it and passes it on unchanged, and the editor bridge selects the range and
fades the rest. A single-line reference goes out exactly as it always did."""
from __future__ import annotations

import http.server
import json
import shutil
import subprocess
import threading
from pathlib import Path

import pytest

from test_action_server import _call, build, server, srv  # noqa: F401  (fixture)

SHA = "cbaa17bdf354be94b36996c6c7efbd02e6b4c057"


def _file(root: Path) -> Path:
    f = root / "src" / "OwnerListTest.java"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("class OwnerListTest {}\n" * 80)
    return f


def _record(monkeypatch):
    opened, asked = [], []
    monkeypatch.setattr(srv, "open_in_editor", lambda *a, **k: opened.append((a, k)))
    monkeypatch.setattr(srv, "review_open", lambda *a, **k: asked.append((a, k)) or None)
    return opened, asked


# ── the server ────────────────────────────────────────────────────────────────────────────

def test_a_range_reaches_the_editor_with_its_end(server, tmp_path, monkeypatch):
    f = _file(tmp_path)
    opened, _ = _record(monkeypatch)

    status, _ = _call(server, "GET", f"{srv.OPEN}?path={f}&line=49&endLine=51")

    assert status == 204 and opened == [((f, 49), {"end_line": 51})]


def test_a_guide_with_its_commit_asks_the_bridge_for_the_range(server, tmp_path, monkeypatch):
    f = _file(tmp_path)
    opened, asked = _record(monkeypatch)

    _call(server, "GET", f"{srv.OPEN}?path={f}&line=49&endLine=51&sha={SHA}&root={tmp_path}")

    assert asked == [((f, 49, SHA, str(tmp_path), ""), {"end_line": 51})]
    # No bridge answered, so the file opens the old way — still as a range.
    assert opened == [((f, 49), {"end_line": 51})]


def test_a_single_line_sends_no_end(server, tmp_path, monkeypatch):
    f = _file(tmp_path)
    opened, _ = _record(monkeypatch)

    _call(server, "GET", f"{srv.OPEN}?path={f}&line=49")

    assert opened == [((f, 49), {})]


@pytest.mark.parametrize("end", ["49", "48", "x", "-51", "51.5", "0", "2049"])
def test_a_bad_end_is_dropped_and_the_line_kept(server, tmp_path, monkeypatch, end):
    f = _file(tmp_path)
    opened, _ = _record(monkeypatch)

    status, _ = _call(server, "GET", f"{srv.OPEN}?path={f}&line=49&endLine={end}")

    assert status == 204 and opened == [((f, 49), {})]


def test_the_span_cap_is_inclusive():
    assert srv.line_span({"line": ["1"], "endLine": [str(srv.MAX_SPAN)]}) == (1, srv.MAX_SPAN)
    assert srv.line_span({"line": ["1"], "endLine": [str(srv.MAX_SPAN + 1)]}) == (1, None)
    assert srv.line_span({"line": ["junk"], "endLine": ["3"]}) == (1, 3)
    assert srv.line_span({}) == (1, None)


# ── what goes to the bridge ───────────────────────────────────────────────────────────────

def _bridge():
    got = []

    class H(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            got.append((self.path, json.loads(self.rfile.read(int(self.headers["Content-Length"])))))
            data = b'{"ok": true}'
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *a):
            pass

    httpd = http.server.HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, got


def test_open_file_carries_end_line_only_for_a_range(tmp_path, monkeypatch):
    httpd, got = _bridge()
    try:
        entry = {"port": httpd.server_address[1], "token": "t"}
        monkeypatch.setattr(srv, "owning_windows", lambda target: [(entry, {})])
        f = _file(tmp_path)

        assert srv.open_in_editor(f, 49, end_line=51) == "relay"
        assert srv.open_in_editor(f, 49) == "relay"

        assert got == [("/open-file", {"path": str(f), "line": 49, "focus": True, "endLine": 51}),
                       ("/open-file", {"path": str(f), "line": 49, "focus": True})]
    finally:
        httpd.shutdown()


def test_review_open_carries_end_line(tmp_path, monkeypatch):
    httpd, got = _bridge()
    try:
        registry = tmp_path / ".walkie-talkie" / "ide"
        registry.mkdir(parents=True)
        (registry / "vscode-1.json").write_text(json.dumps({"port": httpd.server_address[1], "token": "t"}))
        monkeypatch.setattr(srv.Path, "home", classmethod(lambda cls: tmp_path))

        srv.review_open(Path("/r/src/A.java"), 49, SHA, "/r", "test-pr", end_line=51)

        assert got == [("/review-open", {"file": "/r/src/A.java", "line": 49, "sha": SHA,
                                         "root": "/r", "branch": "test-pr", "endLine": 51})]
    finally:
        httpd.shutdown()


# ── the page ──────────────────────────────────────────────────────────────────────────────

def _end_of(face: str, line: str, tip: str = ""):
    """Run the page's own `endOf` in node against a stand-in for the clicked anchor."""
    if not shutil.which("node"):
        pytest.skip("node is not installed")
    js = build.EDITOR_JS
    start = js.index("  function endOf(link, line) {")
    stop = js.index("  function endQuery(link, line) {")
    script = (js[start:stop]
              + f"var link = {{textContent: {json.dumps(face)}, getAttribute: function () "
                f"{{ return {json.dumps(tip)}; }}}};\n"
              + f"process.stdout.write(JSON.stringify(endOf(link, {json.dumps(line)})));")
    out = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def test_the_page_reads_the_end_off_a_range_face():
    assert _end_of("OwnerListTest.java:49-51", "49") == "51"
    assert _end_of("  VisitMapper.java:51-53\n", "51") == "53"


def test_a_multi_span_face_ends_on_its_last_line():
    assert _end_of("LogTest.java:89,93-95", "89") == "95"


def test_no_end_for_a_single_line_or_a_face_about_another_line():
    assert _end_of("OwnerListTest.java:49", "49") is None
    assert _end_of("OwnerListTest.java", "1") is None
    assert _end_of("OwnerListTest.java:40-51", "49") is None
    assert _end_of("↗", "33", tip="Open VisitMapper.toVisitDto(Visit) in VS Code") is None


def test_the_end_can_come_from_the_tooltip():
    assert _end_of("↗", "12", tip="Foo.java:12-20") == "20"


def test_both_open_routes_send_the_end():
    js = build.EDITOR_JS
    assert "'&line=' + ref2.line\n            + endQuery(link, ref2.line)" in js
    assert "'&line=' + aimed.line + endQuery(link, aimed.line)" in js
