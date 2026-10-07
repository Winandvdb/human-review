#!/usr/bin/env python3
"""The contract tab's affected-operation list, pinned — because it fails silently.

The failure this guards against left no mark on the page. `openapi-compat.py` built its
list out of OpenAPITools/openapi-diff's `changedOperations` key, which is computed one
`paths` entry at a time and does not follow a `$ref`. On the change that exposed it the
whole delta lived in `components.schemas`, the `paths` section was byte-identical, and
the tab reported **4** affected operations behind a confident COMPATIBLE seal. Eleven had
moved. Nothing looked wrong: the four rows that were there rendered perfectly.

That shape — a list that is right about what it shows and silent about what it drops — is
exactly what a test has to hold, because no reviewer can catch it by reading the page. So:

  * the eleven operations of the petclinic `VisitDto` change, by name, from the real
    `$ref` topology (`OwnerDto -> PetDto -> VisitDto`, three levels of nesting);
  * every one of them rendering its *actual* added fields, not an empty row — a list that
    is long but blank is the same lie with more scrolling;
  * the honest-degradation path: with `oasdiff` gone the seal must stop claiming to be
    the whole story.

Run it directly (`python3 test_openapi_compat.py`) or under pytest. The oasdiff-backed
tests skip when the binary is not installed; the rest never touch a subprocess.
"""
from __future__ import annotations

import html as html_module
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMPAT = HERE / "openapi-compat.py"


def _load(stem: str, filename: str):
    spec = importlib.util.spec_from_file_location(stem, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[stem] = module
    spec.loader.exec_module(module)
    return module


oac = _load("openapi_compat", "openapi-compat.py")

HAVE_OASDIFF = bool(shutil.which(os.environ.get("OASDIFF_BIN", "oasdiff")))
SKIP_REASON = "oasdiff is not installed — the ref-resolving engine cannot be exercised"


# ── the fixture: petclinic's ref topology, reduced to what the bug needs ──────────
# Deliberately the real graph and not a flat pair: the four operations the old code
# found are the ones that name VisitDto/VisitFieldsDto directly, and the seven it lost
# are the ones that reach them through PetDto and OwnerDto. A flatter fixture would
# pass under the bug.
BASE_SPEC = """
openapi: 3.0.1
info: {title: petclinic, version: "1"}
paths:
  /api/owners:
    get:
      operationId: listOwners
      responses:
        "200":
          content:
            application/json:
              schema: {type: array, items: {$ref: '#/components/schemas/OwnerDto'}}
  /api/owners/{ownerId}:
    get:
      operationId: getOwner
      parameters:
        - {name: ownerId, in: path, required: true, schema: {type: integer}}
      responses:
        "200":
          content:
            '*/*': {schema: {$ref: '#/components/schemas/OwnerDto'}}
  /api/owners/{ownerId}/pets/{petId}:
    get:
      operationId: getOwnersPet
      parameters:
        - {name: ownerId, in: path, required: true, schema: {type: integer}}
        - {name: petId, in: path, required: true, schema: {type: integer}}
      responses:
        "200":
          content:
            '*/*': {schema: {$ref: '#/components/schemas/PetDto'}}
  /api/owners/{ownerId}/pets/{petId}/visits:
    post:
      operationId: addVisit
      parameters:
        - {name: ownerId, in: path, required: true, schema: {type: integer}}
        - {name: petId, in: path, required: true, schema: {type: integer}}
      requestBody:
        content:
          application/json: {schema: {$ref: '#/components/schemas/VisitFieldsDto'}}
      responses:
        "204": {description: done}
  /api/pets:
    get:
      operationId: listPets
      responses:
        "200":
          content:
            application/json:
              schema: {type: array, items: {$ref: '#/components/schemas/PetDto'}}
  /api/pets/{petId}:
    get:
      operationId: getPet
      parameters:
        - {name: petId, in: path, required: true, schema: {type: integer}}
      responses:
        "200":
          content:
            '*/*': {schema: {$ref: '#/components/schemas/PetDto'}}
    put:
      operationId: updatePet
      parameters:
        - {name: petId, in: path, required: true, schema: {type: integer}}
      requestBody:
        content:
          application/json: {schema: {$ref: '#/components/schemas/PetDto'}}
      responses:
        "204": {description: done}
  /api/visits:
    get:
      operationId: listVisits
      responses:
        "200":
          content:
            application/json:
              schema: {type: array, items: {$ref: '#/components/schemas/VisitDto'}}
    post:
      operationId: addStandaloneVisit
      requestBody:
        content:
          application/json: {schema: {$ref: '#/components/schemas/VisitDto'}}
      responses:
        "204": {description: done}
  /api/visits/{visitId}:
    get:
      operationId: getVisit
      parameters:
        - {name: visitId, in: path, required: true, schema: {type: integer}}
      responses:
        "200":
          content:
            '*/*': {schema: {$ref: '#/components/schemas/VisitDto'}}
    put:
      operationId: updateVisit
      parameters:
        - {name: visitId, in: path, required: true, schema: {type: integer}}
      requestBody:
        content:
          application/json: {schema: {$ref: '#/components/schemas/VisitFieldsDto'}}
      responses:
        "204": {description: done}
  /api/vets:
    get:
      operationId: listVets
      responses:
        "200":
          content:
            application/json:
              schema: {type: array, items: {$ref: '#/components/schemas/VetDto'}}
components:
  schemas:
    OwnerDto:
      type: object
      properties:
        id: {type: integer, format: int32}
        lastName: {type: string}
        pets:
          type: array
          items: {$ref: '#/components/schemas/PetDto'}
      required: [id, lastName]
    PetDto:
      type: object
      properties:
        id: {type: integer, format: int32}
        name: {type: string}
        visits:
          type: array
          items: {$ref: '#/components/schemas/VisitDto'}
      required: [id, name]
    VisitDto:
      type: object
      properties:
        id: {type: integer, format: int32}
        description: {type: string}
      required: [description, id]
    VisitFieldsDto:
      type: object
      properties:
        description: {type: string}
      required: [description]
    VetDto:
      type: object
      properties:
        id: {type: integer, format: int32}
        lastName: {type: string}
"""

# The real change, to the byte: three fields on the response DTO (two of them readOnly),
# one on the request DTO. `paths` is untouched — that is the whole point.
HEAD_SPEC = BASE_SPEC.replace(
    """    VisitDto:
      type: object
      properties:
        id: {type: integer, format: int32}
        description: {type: string}
      required: [description, id]""",
    """    VisitDto:
      type: object
      properties:
        id: {type: integer, format: int32}
        description: {type: string}
        vetFirstName: {type: string, readOnly: true}
        vetId: {type: integer, format: int32, minimum: 0}
        vetLastName: {type: string, readOnly: true}
      required: [description, id]""",
).replace(
    """    VisitFieldsDto:
      type: object
      properties:
        description: {type: string}
      required: [description]""",
    """    VisitFieldsDto:
      type: object
      properties:
        description: {type: string}
        vetId: {type: integer, format: int32, minimum: 0}
      required: [description]""",
)

# Five name VisitDto/VisitFieldsDto themselves; six reach them only through OwnerDto or
# PetDto and are precisely the ones a differ that stops at a `$ref` cannot see.
DIRECT = {
    ("GET", "/api/visits"),
    ("POST", "/api/visits"),
    ("GET", "/api/visits/{visitId}"),
    ("PUT", "/api/visits/{visitId}"),
    ("POST", "/api/owners/{ownerId}/pets/{petId}/visits"),
}
TRANSITIVE = {
    ("GET", "/api/owners"),
    ("GET", "/api/owners/{ownerId}"),
    ("GET", "/api/owners/{ownerId}/pets/{petId}"),
    ("GET", "/api/pets"),
    ("GET", "/api/pets/{petId}"),
    ("PUT", "/api/pets/{petId}"),
}
AFFECTED = DIRECT | TRANSITIVE
ADDED_FIELDS = {"vetFirstName", "vetId", "vetLastName"}


def specs(tmp: Path):
    base, head = tmp / "before.yaml", tmp / "after.yaml"
    base.write_text(BASE_SPEC, encoding="utf-8")
    head.write_text(HEAD_SPEC, encoding="utf-8")
    return base, head


def compat(*args, **env) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(COMPAT), *args],
                          capture_output=True, text=True, env={**os.environ, **env})


# ── the list ─────────────────────────────────────────────────────────────────────
def test_every_operation_the_schema_change_reaches_is_listed():
    if not HAVE_OASDIFF:
        print(f"skip {SKIP_REASON}")
        return
    with tempfile.TemporaryDirectory() as tmp:
        base, head = specs(Path(tmp))
        proc = compat(str(base), str(head), "--json")
        assert proc.returncode == 0, proc.stderr
        report = json.loads(proc.stdout)

    listed = {(o["method"], o["path"]) for o in report["breaks"] + report["additive"]}
    assert listed == AFFECTED, (
        f"expected {len(AFFECTED)} affected operations, got {len(listed)}\n"
        f"  missing: {sorted(AFFECTED - listed)}\n"
        f"  unexpected: {sorted(listed - AFFECTED)}"
    )
    # The six that a paths-only differ cannot see are the reason this test exists.
    assert TRANSITIVE <= listed
    assert report["complete"] is True and report["source"] == "oasdiff"


def test_optional_additions_stay_non_breaking():
    if not HAVE_OASDIFF:
        print(f"skip {SKIP_REASON}")
        return
    with tempfile.TemporaryDirectory() as tmp:
        base, head = specs(Path(tmp))
        proc = compat(str(base), str(head), "--state")
        assert proc.returncode == 0, proc.stderr
    # Optional properties in both directions: a longer list must not become a scarier one.
    assert proc.stdout.strip() == oac.COMPATIBLE


def test_a_required_addition_to_a_request_body_is_breaking():
    """The verdict still has to be able to say no — a list of 11 safe rows proves nothing
    if the engine cannot fail."""
    if not HAVE_OASDIFF:
        print(f"skip {SKIP_REASON}")
        return
    breaking = HEAD_SPEC.replace("      required: [description]",
                                 "      required: [description, vetId]")
    with tempfile.TemporaryDirectory() as tmp:
        base, head = Path(tmp) / "before.yaml", Path(tmp) / "after.yaml"
        base.write_text(BASE_SPEC, encoding="utf-8")
        head.write_text(breaking, encoding="utf-8")
        proc = compat(str(base), str(head), "--state")
        assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == oac.INCOMPATIBLE


# ── the rows ─────────────────────────────────────────────────────────────────────
def rows_by_operation(fragment: str) -> dict:
    """Each `oac-row` keyed by its operation, so a row can be asked what it drew."""
    out = {}
    for chunk in re.split(r'(?=<div class="oac-row)', fragment):
        head = re.search(r'oac-verb oac-\w+">(\w+)</span><code class="oac-path">([^<]+)',
                         chunk)
        if head:
            out[(head.group(1), head.group(2))] = chunk
    return out


def test_every_listed_operation_draws_the_fields_that_moved():
    """A row with no shape under it teaches the reader the panels are empty."""
    if not HAVE_OASDIFF:
        print(f"skip {SKIP_REASON}")
        return
    with tempfile.TemporaryDirectory() as tmp:
        base, head = specs(Path(tmp))
        proc = compat(str(base), str(head))
        assert proc.returncode == 0, proc.stderr
        fragment = proc.stdout

    rows = rows_by_operation(fragment)
    assert set(rows) == AFFECTED, sorted(set(rows) ^ AFFECTED)
    for key, chunk in sorted(rows.items()):
        drawn = set(re.findall(r'oat-added" style="--d:\d+"><span class="oat-key">([^<]+)',
                               chunk))
        assert drawn, f"{key[0]} {key[1]} rendered an empty row — no added field is drawn"
        assert drawn <= ADDED_FIELDS, f"{key} drew something unexpected: {drawn}"
        assert "vetId" in drawn, f"{key} does not draw vetId, which every one of them gains"


# ── honest degradation ───────────────────────────────────────────────────────────
def test_a_list_that_may_be_short_never_gets_a_clean_seal():
    """The fallback engine's list is a lower bound; the seal has to say so on its face."""
    partial = {"state": oac.COMPATIBLE, "breaks": [], "deprecated": [], "elsewhere": [],
               "additive": [{"method": "GET", "path": "/api/visits", "note": "changed"}],
               "complete": False, "source": f"openapi-diff {oac.VERSION}"}
    fragment = oac.render(partial, "provenance", "")

    seal = re.search(r'oac-seal">([^<]+)', fragment).group(1)
    assert seal != "COMPATIBLE", "a bare COMPATIBLE seal over a list we know can be short"
    assert "PARTIAL" in seal, seal
    assert "oac-incomplete" in fragment, "no band explaining why the list may be short"
    assert "brew install oasdiff" in fragment, "the band does not say how to fix it"
    assert "$ref" in fragment, "the band does not say what the fallback cannot follow"

    whole = oac.render({**partial, "complete": True}, "provenance", "")
    assert re.search(r'oac-seal">([^<]+)', whole).group(1) == "COMPATIBLE"
    assert "oac-incomplete" not in whole, "the band shows up when the list is complete"


def test_no_changes_does_not_claim_two_different_specs_are_identical():
    """A reworded description moves the spec without moving the contract. Both halves of
    that sentence have to survive, or the seal contradicts the tab next to it."""
    moved = oac.render({"state": oac.NO_CHANGES, "breaks": [], "additive": [],
                        "deprecated": [], "elsewhere": [], "complete": True,
                        "identical": False}, "provenance", "")
    assert "structurally identical" not in moved
    assert "The specs differ" in moved

    same = oac.render({"state": oac.NO_CHANGES, "breaks": [], "additive": [],
                       "deprecated": [], "elsewhere": [], "complete": True,
                       "identical": True}, "provenance", "")
    assert "structurally identical" in same


def test_the_fallback_engine_declares_itself_incomplete():
    """Whatever `read_report` returns, it must never claim to be the whole list."""
    result = oac.read_report({"changedOperations": [], "newEndpoints": [],
                              "missingEndpoints": [], "incompatible": False})
    assert result["complete"] is False


def test_missing_oasdiff_is_a_fallback_not_a_crash():
    saved = oac.OASDIFF
    try:
        oac.OASDIFF = "oasdiff-that-is-not-installed"
        assert oac.oasdiff_changelog(Path("a.yaml"), Path("b.yaml")) is None
        assert oac.oasdiff_version() is None
    finally:
        oac.OASDIFF = saved


# ── the one line at the top of the tab ───────────────────────────────────────────
# It shipped for months as a hand-typed string in the content file: "25 changes, none
# breaking", green, over whatever the branch actually did. It happened to be right on the
# day it was written. These tests exist so it cannot go back to being a sentence somebody
# has to remember to update.
def _panel_text(fragment: str) -> str:
    stripped = re.sub("<[^>]+>", "", fragment.split("</style>")[-1])
    return re.sub(r"\s+", " ", html_module.unescape(stripped)).strip()


def _panel_class(fragment: str) -> str:
    return re.search(r'class="apiverdict (\w+)"', fragment).group(1)


def _result(state, breaks=(), additive=(), **extra):
    return {"state": state, "breaks": list(breaks), "additive": list(additive),
            "deprecated": [], "elsewhere": [], "complete": True, "source": "oasdiff",
            **extra}


def _op(method, path, n_reasons):
    return {"method": method, "path": path,
            "reasons": [([f"rule-{i}"], f"change {i}") for i in range(n_reasons)]}


def test_the_panel_has_exactly_three_colours():
    """Three states, three treatments. A fourth class means a fourth palette."""
    nothing = oac.panel(_result(oac.NO_CHANGES, identical=True))
    safe = oac.panel(_result(oac.COMPATIBLE, additive=[_op("GET", "/api/owners", 3)]))
    broken = oac.panel(_result(oac.INCOMPATIBLE, breaks=[_op("GET", "/api/owners", 2)]))
    assert [_panel_class(f) for f in (nothing, safe, broken)] == ["none", "green", "red"]

    # Grey, and struck through — the CSS has to carry the strike, not just the class.
    assert ".apiverdict.none .v,.apiverdict.none .n{text-decoration:line-through}" in nothing
    # Both themes, through the mechanism the rest of the page uses.
    assert "@media (prefers-color-scheme:dark)" in safe
    # The green/red are the score chip's own values, not a fifth pair invented here.
    assert "rgba(46,158,91,.16)" in safe and "#6fce93" in safe
    assert "rgba(215,38,61,.16)" in broken and "#f0757f" in broken
    # Grey is not a hex at all: it is the page's tokens.
    for token in ("var(--code-bg)", "var(--muted)", "var(--line)"):
        assert token in nothing, token


def test_the_panel_counts_what_the_differ_found_and_nothing_else():
    """The count is the bug this panel was rewritten for: it must move with the result."""
    result = _result(oac.COMPATIBLE, additive=[_op("GET", "/api/owners", 3),
                                               _op("GET", "/api/pets", 22)])
    assert oac.change_count(result) == 25
    # The band counts endpoints (7 Oct 2026), not the 25 changes inside them.
    assert "2 endpoints changed" in _panel_text(oac.panel(result))
    # One more endpoint and the sentence moves with it. No fixture pins "2".
    result["additive"].append(_op("GET", "/api/vets", 1))
    assert "3 endpoints changed" in _panel_text(oac.panel(result))
    # More changes on an endpoint already counted do not move it.
    result["additive"].append(_op("GET", "/api/vets", 4))
    assert "3 endpoints changed" in _panel_text(oac.panel(result))
    # A single endpoint is not "1 endpoints".
    one = _result(oac.COMPATIBLE, additive=[_op("GET", "/api/vets", 1)])
    assert "1 endpoint changed" in _panel_text(oac.panel(one))


def test_the_breaking_panel_counts_the_endpoints_broken_and_nothing_else():
    """7 Oct 2026: "9 changes, 1 breaking across 1 endpoint · checked by oasdiff,
    double-checked by …" wrapped onto two lines. The band says how many
    endpoints break; the changes inside them are what the tab below lists."""
    result = _result(oac.INCOMPATIBLE,
                     breaks=[_op("DELETE", "/api/visits/{id}", 2)],
                     additive=[_op("GET", "/api/owners", 3)])
    text = _panel_text(oac.panel(result))
    # verdict · counts · who checked it — the same shape as the green line.
    assert text.startswith("Breaking changes · 1 endpoint broken · checked by"), text
    assert text == "Breaking changes · 1 endpoint broken · checked by oasdiff", text
    assert "double-checked" not in text and "change," not in text, text

    single = _result(oac.INCOMPATIBLE, breaks=[_op("DELETE", "/api/visits/{id}", 1)])
    assert _panel_text(oac.panel(single)).startswith(
        "Breaking change · 1 endpoint broken ·")
    two = _result(oac.INCOMPATIBLE, breaks=[_op("DELETE", "/api/visits/{id}", 1),
                                            _op("GET", "/api/owners", 1)])
    assert "· 2 endpoints broken ·" in _panel_text(oac.panel(two))


def _entry(level, rule, op="GET", path="/api/owners"):
    return {"id": rule, "operation": op, "path": path, "level": level, "text": rule}


def test_one_break_among_additions_counts_as_one_break():
    """Run 5: oasdiff rated one entry breaking (the 200 body went array → object) and five
    INFO (three optional params, two response properties). The band said "6 breaking",
    because every entry of an operation with *any* WARN+ entry was filed as breaking."""
    entries = [_entry(3, "response-body-type-changed")] + [
        _entry(1, f"new-optional-request-parameter-{p}") for p in ("page", "size", "sort")] + [
        _entry(1, f"response-required-property-added-{p}") for p in ("content", "total")]
    result = oac.read_changelog(entries)
    assert result["state"] == oac.INCOMPATIBLE
    assert oac.breaking_count(result) == 1
    assert oac.change_count(result) == 6
    text = _panel_text(oac.panel(result))
    assert text.startswith("Breaking change · 1 endpoint broken ·"), text
    # The INFO entries are not dropped: the operation's compatible movement lists them.
    fragment = oac.render(result, "provenance", "")
    assert re.search(r'What breaks <span class="oac-count">1<', fragment), fragment
    assert "5 compatible changes besides the break above" in fragment
    # A WARN entry is breaking too — oasdiff's own `breaking` command is level >= 2.
    warn = oac.read_changelog([_entry(2, "request-param-enum-value-removed"),
                               _entry(1, "x")])
    assert oac.breaking_count(warn) == 1 and oac.change_count(warn) == 2


def test_the_band_wraps_as_a_sentence_and_never_opens_a_line_on_the_dot():
    """Eval run 8: as a flex row the label sat vertically centred beside a two-line count
    whose second line hung under nothing. The band is running text now, wrapping from the
    left edge; and the spaces either side of the '·' are no-break, so a wrapped line never
    opens on a stray '·' (the reason the row was flex in the first place)."""
    css = oac.PANEL_CSS
    band = re.search(r"\.apiverdict\{([^}]*)\}", css).group(1)
    assert "display:block" in band and "align-items:center" not in band, band
    result = _result(oac.INCOMPATIBLE, breaks=[_op("GET", "/api/owners", 1)])
    html_ = oac.panel(result)
    assert '</span>&nbsp;<span class="n">·&nbsp;' in html_
    assert "Breaking change" in _panel_text(html_)


def test_nothing_moved_says_so_and_gets_out_of_the_way():
    same = oac.panel(_result(oac.NO_CHANGES, identical=True))
    assert _panel_text(same).startswith("No API changes · 0 endpoints changed · checked by")
    # A reworded description moves the spec without moving the contract; the panel must
    # not flatly claim the two files are the same, the way the seal below does not.
    moved = oac.panel(_result(oac.NO_CHANGES, identical=False))
    assert "0 endpoints changed for a caller" in _panel_text(moved)


def test_the_panel_credits_only_the_differ_that_actually_ran():
    """With oasdiff installed the Java tool is never invoked; crediting it would be a
    check that did not happen. The fallback is the other way round."""
    with_oasdiff = oac.panel(_result(oac.COMPATIBLE, additive=[_op("GET", "/api/o", 1)]))
    assert "OpenAPITools/openapi-diff" not in with_oasdiff
    assert "github.com/oasdiff/oasdiff" in with_oasdiff

    fallback = _result(oac.COMPATIBLE, source=f"openapi-diff {oac.VERSION}", complete=False,
                       additive=[{"method": "GET", "path": "/api/owners", "note": "changed"}])
    text = _panel_text(oac.panel(fallback))
    assert "OpenAPITools/openapi-diff" in text
    assert "oasdiff" in text and "lower bound" in text, (
        "a count from a list that cannot follow a $ref must not look whole")
    # An operation nobody itemised is still one endpoint changed, not zero.
    assert "1 endpoint changed" in text



def test_the_band_names_one_differ_and_it_is_not_ours():
    """7 Oct 2026: our own `openapi-diff.py` used to sit beside oasdiff as a second opinion
    and turn the band red as "Verdict disputed" whenever the two disagreed. An eval on 121
    spec pairs (`reference/openapi-differ-eval.md`) showed it wrong far more often than the
    tool it checked, so it was deleted; what it alone caught was reported to oasdiff. The
    band credits the one differ that ran, with its report — and nothing home-made."""
    with tempfile.TemporaryDirectory() as tmp:
        assets = Path(tmp)
        (assets / oac.REPORTS["engine"]).write_text("x", encoding="utf-8")
        band = oac.panel(_result(oac.INCOMPATIBLE, breaks=[_op("GET", "/api/owners", 1)]),
                         assets)
    assert _panel_text(band) == ("Breaking change · 1 endpoint broken · "
                                 "checked by oasdiff (report ↗)"), _panel_text(band)
    assert not (HERE / "openapi-diff.py").exists(), "the home-made differ is back"
    source = COMPAT.read_text(encoding="utf-8")
    for gone in ("our_verdict", "cross_check", "--no-cross-check"):
        assert gone not in source, gone
    band_code = source[source.index("def panel("):source.index("# ── the tool's markdown")]
    assert "disputed" not in band_code.lower(), "a second differ is arguing with the tool again"


def test_the_panel_count_matches_what_oasdiff_reported():
    """End to end: the number on the page is the number the binary emitted."""
    if not HAVE_OASDIFF:
        print(f"skip {SKIP_REASON}")
        return
    with tempfile.TemporaryDirectory() as tmp:
        base, head = specs(Path(tmp))
        rendered = compat(str(base), str(head), "--panel")
        assert rendered.returncode == 0, rendered.stderr
        raw = subprocess.run([os.environ.get("OASDIFF_BIN", "oasdiff"), "changelog",
                              str(base), str(head), "-f", "json"],
                             capture_output=True, text=True)
        entries = json.loads(raw.stdout.strip() or "[]")
    ops = {(e["operation"], e["path"]) for e in entries if e.get("operation")}
    n = len(ops)
    assert f"{n} endpoint{'' if n == 1 else 's'} changed" in _panel_text(rendered.stdout)


def test_no_number_in_the_panel_is_typed_into_the_content_file():
    """The regression this replaced: `"25 changes, none breaking"` sat in content.json.
    Nothing in the generator may contain a literal count."""
    source = COMPAT.read_text(encoding="utf-8")
    body = source[source.index("def panel("):source.index("# ── the tool's markdown")]
    # "0 endpoints" is allowed: it is the no-change state's own honest constant, and it is
    # guarded by `state == NO_CHANGES`, not by somebody remembering to retype it.
    assert not re.search(r"[1-9]\d* (change|endpoint)", body), "a count is hardcoded in the panel"



# ── run 6: the band and the visual diff under it count one way ───────────────────
SWAP_BEFORE = """
openapi: 3.0.1
info: {title: petclinic, version: "1"}
paths:
  /api/owners:
    get:
      responses:
        "200":
          content:
            application/json: {schema: {type: array, items: {type: string}}}
        "400":
          content:
            '*/*': {schema: {type: string}}
"""
SWAP_AFTER = """
openapi: 3.0.1
info: {title: petclinic, version: "1"}
paths:
  /api/owners:
    get:
      parameters:
        - {name: page, in: query, schema: {type: integer}}
      responses:
        "200":
          content:
            application/json: {schema: {type: array, items: {type: string}}}
        "400":
          content:
            application/problem+json: {schema: {type: string}}
  /api/vets:
    get:
      responses:
        "200": {description: ok}
"""


def _swap_entries():
    """What oasdiff emitted on hr-claude-6 for the 400 response: one swap, two entries."""
    return [
        _entry(3, "response-body-type-changed"),
        {"id": "response-media-type-removed", "operation": "GET", "path": "/api/owners",
         "level": 3, "text": "removed the media type `*/*` for the response with the "
                             "status `400`"},
        _entry(1, "new-optional-request-parameter"),
        {"id": "response-media-type-added", "operation": "GET", "path": "/api/owners",
         "level": 1, "text": "added the media type `application/problem+json` for the "
                             "response with the status `400`"},
    ]


def test_a_swapped_media_type_is_one_change_on_the_band_as_in_the_visual_diff():
    """Run 6: the band said "8 changes, 2 breaking" over a visual diff listing 7 rows and a
    toggle reading "expand 7 impacted" — oasdiff counts `*/*` → `problem+json` as a removal
    plus an addition, the visual diff folds them into one row. One fold, one count."""
    result = oac.read_changelog(_swap_entries())
    assert oac.change_count(result) == 3, result
    assert oac.breaking_count(result) == 2
    text = _panel_text(oac.panel(result))
    assert text.startswith("Breaking changes · 1 endpoint broken"), text
    # The folded line says what happened, in one sentence, at the higher severity.
    reasons = " ".join(t for b in result["breaks"] for _, t in b["reasons"])
    assert "changed from <code>*/*</code> to <code>application/problem+json</code>" in reasons
    # And it is the visual diff's own fold, not a second copy of the rule.
    ovd = _load("openapi_visual_diff", "openapi-visual-diff.py")
    raw = [dict(e, section="paths") for e in _swap_entries()]
    _, entries, global_changes, _ = ovd.build_model(
        {"paths": {"/api/owners": {"get": {}}}}, {"paths": {"/api/owners": {"get": {}}}}, raw)
    assert ovd.change_total(entries, global_changes) == oac.change_count(result)


def test_the_band_counts_no_changes_so_neither_oasdiff_nor_the_toggle_can_disagree():
    """Runs 6 and 11: the band's change count disagreed first with the visual diff's toggle
    ("8 changes" over "expand 7 impacted"), then with `oasdiff changelog` itself (7 vs 8),
    and needed a hover to own up to the fold. Since 7 Oct 2026 the band counts endpoints,
    which the fold never changes: the swap is on one endpoint however it is counted."""
    band = oac.panel(oac.read_changelog(_swap_entries()))
    assert "data-tip" not in band, band
    text = _panel_text(band)
    assert text.startswith("Breaking changes · 1 endpoint broken ·"), text
    assert not re.search(r"\d+ changes?\b", text), text
    plain = [e for e in _swap_entries() if e["id"] != "response-media-type-added"]
    assert _panel_text(oac.panel(oac.read_changelog(plain))).startswith(
        "Breaking changes · 1 endpoint broken ·")


def test_the_band_counts_the_endpoints_oasdiff_broke_end_to_end():
    if not HAVE_OASDIFF:
        print(f"skip {SKIP_REASON}")
        return
    with tempfile.TemporaryDirectory() as tmp:
        base, head = Path(tmp) / "before.yaml", Path(tmp) / "after.yaml"
        base.write_text(SWAP_BEFORE, encoding="utf-8")
        head.write_text(SWAP_AFTER, encoding="utf-8")
        band = compat(str(base), str(head), "--panel")
        assert band.returncode == 0, band.stderr
        raw = subprocess.run([os.environ.get("OASDIFF_BIN", "oasdiff"), "changelog",
                              str(base), str(head), "-f", "json"],
                             capture_output=True, text=True)
        entries = json.loads(raw.stdout.strip() or "[]")
    broken = {(e["operation"], e["path"]) for e in entries
              if e.get("operation") and int(e.get("level") or 1) >= 2}
    n = re.search(r"· (\d+) endpoints? broken ·", _panel_text(band.stdout))
    assert n and int(n.group(1)) == len(broken), (band.stdout, broken)


def test_the_report_calls_the_review_base_the_review_base():
    """Run 6: the report said "openapi.yaml at the merge-base 5a97353e". 5a97353e is the
    review base `run-steps.py` hands every producer; the merge-base with main is dd9055ef."""
    sha = "5a97353e" + "0" * 32
    assert oac.base_name(sha, sha, sha) == "the review base"
    assert oac.base_name("origin/main", "f" * 40, sha) == \
        "the merge-base with <code>origin/main</code>"
    source = COMPAT.read_text(encoding="utf-8")
    assert "at the merge-base " not in source, "a hardcoded 'merge-base' label is back"


def test_a_differ_name_and_its_report_link_wrap_as_one():
    """Run 6, 1440px: the band broke between a differ's name and its "(report ↗)",
    leaving the arrow alone on the second line."""
    with tempfile.TemporaryDirectory() as tmp:
        assets = Path(tmp)
        for name in oac.REPORTS.values():
            (assets / name).write_text("x", encoding="utf-8")
        frag = oac.panel(_result(oac.INCOMPATIBLE, breaks=[_op("GET", "/api/owners", 2)]), assets)
    units = re.findall(r'<span class="who">(.*?</a>\))</span>', frag)
    assert len(units) == 1 and "oasdiff" in units[0] and "report" in units[0], frag
    assert ".apiverdict .who{white-space:nowrap}" in oac.PANEL_CSS

if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except AssertionError as e:
                failures += 1
                print(f"FAIL {name}: {e}")
    sys.exit(1 if failures else 0)
