"""The Sequence step's copy of what its traced run drew survives commits that did not touch it.

`run-steps.py` `_sequence` files each picture it drew in `.human-review/assets/genseq/` and
pins the copy to the commit it traced (`.head`). Every reader of the copy — the page
(`hrbuild/shared/genseq.py`), the delta drawer (`puml-diff.sh`), the C2 projection
(`c2-from-sequence.py`) — used to drop it whole the moment HEAD moved. The visit-vet review
(6 Oct 2026) traced its two auto-picked JUnit tests, `VisitTest#create_withVet` and
`#create_withoutVet`, got a trace for each, and then committed `review-points.md` and merged
`main`: neither touched a diagram, but HEAD moved, the copy was ignored, and since a test the
branch wrote is traced untagged and leaves nothing in the work tree, both pictures were simply
gone from the Sequence tab. A later commit is the newer truth only for the files it changed.
"""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("build_review_html", HERE / "build-review-html.py")
build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build)
_spec = importlib.util.spec_from_file_location("c2_from_sequence", HERE / "c2-from-sequence.py")
c2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(c2)

TAGGED = "generated/AddVisitApiTest.java.adds-a-visit.genseq.puml"
PICKED = "generated/VisitTest.java.create-withvet.genseq.puml"


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *args],
                          cwd=root, check=True, capture_output=True, text=True).stdout.strip()


def _puml(callee: str) -> str:
    return f"@startuml\nparticipant Test\nparticipant {callee}\nTest -> {callee}: POST /api/visits\n@enduml\n"


def _traced_then_committed(root: Path) -> Path:
    """A branch whose run traced one tagged test (committed diagram) and one test the branch
    wrote (no committed diagram), then made a commit that touched no diagram."""
    (root / "generated").mkdir(parents=True)
    (root / TAGGED).write_text(_puml("Committed"))
    (root / ".gitignore").write_text(".human-review/\n")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "base")
    overlay = root / ".human-review/assets/genseq"
    (overlay / "generated").mkdir(parents=True)
    (overlay / TAGGED).write_text(_puml("Traced"))
    (overlay / PICKED).write_text(_puml("VisitBackend"))
    (overlay / ".head").write_text(_git(root, "rev-parse", "HEAD") + "\n")
    (root / "review-points.md").write_text("base: abc\n")
    _git(root, "add", "review-points.md")
    _git(root, "commit", "-qm", "review-points: base moves")
    return overlay


def test_a_commit_that_touched_no_diagram_keeps_every_traced_picture(tmp_path):
    overlay = _traced_then_committed(tmp_path)
    assert build.genseq_file(PICKED, tmp_path) == overlay / PICKED, \
        "the picture of a test the branch wrote exists only in the copy"
    assert build.genseq_file(TAGGED, tmp_path) == overlay / TAGGED, \
        "this run's trace still beats the committed bytes no commit since replaced"
    drawn = build.genseq_by_test(tmp_path)
    assert PICKED in [p for pumls in drawn.values() for p in pumls], \
        "the Sequence tab pairs the auto-picked test with its picture"


def test_a_diagram_a_later_commit_changed_is_read_from_the_work_tree(tmp_path):
    overlay = _traced_then_committed(tmp_path)
    (tmp_path / TAGGED).write_text(_puml("Recommitted"))
    _git(tmp_path, "commit", "-qam", "regenerate the tagged diagram")
    assert build.genseq_file(TAGGED, tmp_path) == tmp_path / TAGGED, "that commit is newer"
    assert build.genseq_file(PICKED, tmp_path) == overlay / PICKED, "this one it did not touch"


def test_a_copy_pinned_to_no_commit_of_this_history_is_ignored(tmp_path):
    overlay = _traced_then_committed(tmp_path)
    (overlay / ".head").write_text("0" * 40 + "\n")
    assert build.genseq_file(PICKED, tmp_path) == tmp_path / PICKED
    assert build.genseq_file(TAGGED, tmp_path) == tmp_path / TAGGED


def test_the_c2_projection_reads_the_copy_by_the_same_rule(tmp_path):
    overlay = _traced_then_committed(tmp_path)
    state = c2.traced_overlay(tmp_path, overlay)
    assert c2.overlay_file(state, PICKED) == overlay / PICKED
    assert sorted(c2.overlay_sources(state, ["**/*.genseq.puml"], [])) == [TAGGED, PICKED]
    (tmp_path / TAGGED).write_text(_puml("Recommitted"))
    _git(tmp_path, "commit", "-qam", "regenerate the tagged diagram")
    state = c2.traced_overlay(tmp_path, overlay)
    assert c2.overlay_file(state, TAGGED) is None
    assert c2.overlay_sources(state, ["**/*.genseq.puml"], []) == [PICKED]


@pytest.mark.skipif(not shutil.which("plantuml"), reason="puml-diff.sh renders with plantuml")
def test_the_delta_drawer_still_draws_the_auto_picked_test_after_a_commit(tmp_path):
    _traced_then_committed(tmp_path)
    out = tmp_path / ".human-review/assets/diagrams"
    subprocess.run(["bash", str(HERE / "puml-diff.sh"), "HEAD~1", str(out)], cwd=tmp_path,
                   check=True, capture_output=True, text=True)
    rows = [line.split("\t") for line in (out / "MANIFEST.tsv").read_text().splitlines()[1:]]
    status = {r[1]: r[3] for r in rows}
    assert status.get(PICKED) == "added", "the overlay-only picture is drawn as a new diagram"
    assert status.get(TAGGED) == "modified", "and the re-traced tagged one as a delta"
