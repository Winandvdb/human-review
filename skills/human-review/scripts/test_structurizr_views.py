"""The Structurizr C4 cards: what the producer decides without Docker, and how they land."""
from __future__ import annotations

import base64
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("structurizr_views", HERE / "structurizr-views.py")
sv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sv)

from hrbuild.shared.c4 import render_c4            # noqa: E402
from hrbuild.shared.layout import own_layout       # noqa: E402
from hrbuild.shared.adopt import DIAGRAM_KINDS     # noqa: E402


def _ws(components, rels, desc="All components"):
    comps = [{"id": str(i + 10), "name": n, "tags": "Element,Component",
              "relationships": [{"id": f"r{j}", "sourceId": str(i + 10),
                                 "destinationId": str(components.index(d) + 10),
                                 "description": "uses"}
                                for j, (s, d) in enumerate(rels) if s == n]}
             for i, n in enumerate(components)]
    return {"model": {"softwareSystems": [{"id": "1", "name": "Sys", "containers": [
        {"id": "2", "name": "Backend", "components": comps}]}]},
        "views": {"componentViews": [{
            "key": "C3", "description": desc, "containerId": "2", "automaticLayout": {},
            "elements": [{"id": c["id"]} for c in comps],
            "relationships": [{"id": r["id"]} for c in comps for r in c["relationships"]]}]}}


def test_a_fragment_is_not_a_workspace():
    assert sv.is_workspace('# C1\nworkspace "x" {\n}')
    assert sv.is_workspace('/* header */\n// note\nworkspace {}')
    assert not sv.is_workspace('a = component "A"\n!include x.dsl')


def test_a_view_is_unchanged_when_ids_move_but_the_model_does_not():
    a = sv.view_signatures(_ws(["A", "B"], [("A", "B")]))
    b = sv.view_signatures(_ws(["A", "B"], [("A", "B")]))
    assert a["C3"]["sig"] == b["C3"]["sig"]
    moved = sv.view_signatures(_ws(["Z", "A", "B"], [("A", "B")]))   # ids shift by one
    assert moved["C3"]["sig"] != a["C3"]["sig"], "a new component must change the view"


def test_a_new_arrow_changes_the_view():
    a = sv.view_signatures(_ws(["A", "B"], [("A", "B")]))
    b = sv.view_signatures(_ws(["A", "B"], [("A", "B"), ("B", "A")]))
    assert a["C3"]["sig"] != b["C3"]["sig"]


def test_the_note_says_which_level_a_test_checks():
    tests = [{"path": "src/test/C3ArchTest.java", "levels": ["Component"]}]
    assert "checked against the code by C3ArchTest.java" in sv.tested_note("Component", tests)
    c2 = sv.tested_note("Container", tests)
    assert c2.startswith("Hand-maintained") and "checks only its components" in c2
    assert sv.tested_note("Container", []).startswith("Hand-maintained: no test")


def _svg(tmp, name, bg):
    (tmp / name).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" '
                            f'style="background: {bg}"></svg>', encoding="utf-8")


def _manifest(tmp, rows):
    cols = sv.COLUMNS
    (tmp / "MANIFEST.tsv").write_text("\t".join(cols) + "\n" + "".join(
        "\t".join(r.get(c, "") for c in cols) + "\n" for r in rows), encoding="utf-8")
    (tmp / "verdict.json").write_text('{"state": "drawn"}', encoding="utf-8")


def test_an_unchanged_view_is_one_picture_in_both_schemes(tmp_path):
    assets = tmp_path / "assets" / "c4"
    assets.mkdir(parents=True)
    _svg(assets, "C2.new.light.svg", "#ffffff")
    _svg(assets, "C2.new.dark.svg", "#111111")
    _manifest(assets, [{"name": "C2", "description": "Containers", "type": "Container",
                        "status": "unchanged", "source": "docs/w.dsl",
                        "new_light": "C2.new.light.svg", "new_dark": "C2.new.dark.svg",
                        "note": "Hand-maintained."}])
    out, weight, changes = render_c4({}, tmp_path, tmp_path)
    assert (weight, changes) == (1, 0)
    assert 'class="c4-light"' in out and 'class="c4-dark"' in out
    assert "dgmviews" not in out and "UNCHANGED".lower() in out
    assert 'width="400"' in out, "half of Structurizr's canvas size"
    light = out.split('class="c4-light" src="data:image/svg+xml;base64,')[1].split('"')[0]
    assert "#ffffff" in base64.b64decode(light).decode(), "the SVG travels untouched"


def test_a_changed_view_toggles_new_and_old_with_no_diff_pane(tmp_path):
    assets = tmp_path / "assets" / "c4"
    assets.mkdir(parents=True)
    for side in ("new", "old"):
        for mode in ("light", "dark"):
            _svg(assets, f"C3.{side}.{mode}.svg", "#fff")
    _manifest(assets, [{"name": "C3", "type": "Component", "status": "modified",
                        "source": "docs/w.dsl", **{f"{s}_{m}": f"C3.{s}.{m}.svg"
                                                   for s in ("new", "old")
                                                   for m in ("light", "dark")}}])
    out, _, changes = render_c4({}, tmp_path, tmp_path)
    assert changes == 1 and "dgm-toggles" in out
    assert 'data-go="newold"' in out and 'data-go="diff"' not in out
    assert 'data-state="new"' in out


def test_no_docker_is_said_in_place(tmp_path):
    assets = tmp_path / "assets" / "c4"
    assets.mkdir(parents=True)
    (assets / "verdict.json").write_text(json.dumps({
        "state": "unavailable", "reason": "Docker is not running",
        "workspaces": ["docs/w.dsl"]}), encoding="utf-8")
    out, weight, changes = render_c4({}, tmp_path, tmp_path)
    assert "Docker is not running" in out and (weight, changes) == (1, 0)


def test_the_structure_tab_gets_the_block_once_the_step_wrote_its_verdict(tmp_path):
    spec = {"tabs": [{"id": "packages", "label": "Structure",
                      "blocks": [{"type": "puml", "src": "x.puml"}]}]}
    own_layout(spec, tmp_path)
    assert [b["type"] for b in spec["tabs"][0]["blocks"]] == ["puml"]
    (tmp_path / "assets" / "c4").mkdir(parents=True)
    (tmp_path / "assets" / "c4" / "verdict.json").write_text("{}", encoding="utf-8")
    spec = {"tabs": [{"id": "packages", "label": "Structure",
                      "blocks": [{"type": "puml", "src": "x.puml"}]}]}
    own_layout(spec, tmp_path)
    assert [b["type"] for b in spec["tabs"][0]["blocks"]] == ["puml", "c4"]


def test_a_structurizr_card_gets_its_own_prompt_not_the_projected_c2s():
    head = "C2-Containers Structurizr · Containers c4model.c1+c2.dsl"
    assert next(k for k, rx in DIAGRAM_KINDS if rx.search(head)) == "diagram.c4"
