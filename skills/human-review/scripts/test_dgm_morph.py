#!/usr/bin/env python3
"""Switching the radius of a diff diagram morphs instead of jumping.

Each radius (0, 1, 2, all) is its own PlantUML render with its own layout, so a bare
visibility flip threw every box somewhere new and the reader lost the change. focus.js
now keeps the changed boxes (`dgm-ripple-1`) at the same place on screen by scrolling the
page, slides the boxes both renders share from their old spot to their new one, and fades
the newcomers in with a glow. The morph must leave nothing behind: once it settles, the
picture is exactly the one a plain flip shows.

The page here is the real stylesheet and the real focus.js around two hand-made renders
with different layouts, so it needs no build and no server.

Run with:  python3 -m pytest test_dgm_morph.py
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
_spec = importlib.util.spec_from_file_location("hr_assets", HERE / "hrbuild" / "shared" / "assets.py")
assets = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(assets)


def _entity(name, x, y, fill):
    return (f'<g class="entity" data-qualified-name="{name}"><rect fill="{fill}" x="{x}" y="{y}" '
            f'width="120" height="60" style="stroke:var(--dgm-line);stroke-width:0.5;"/>'
            f'<text x="{x + 10}" y="{y + 30}">{name}</text></g>')


def _svg(h, *entities):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 {h}" width="400px" '
            f'height="{h}px" style="width:400px;height:{h}px"><g>'
            f'<g class="title"><text x="10" y="20">Diff</text></g>{"".join(entities)}'
            f'<g class="link"><path d="M0,0 L10,10"/></g></g></svg>')


# At 0 the change sits at the top; at 1 a neighbour lands above it and pushes it down,
# which is exactly the jump the morph exists to absorb. Gone leaves at 1.
LEVEL0 = _svg(260, _entity("Visit", 40, 40, "var(--dgm-ripple-1)"),
              _entity("Vet", 40, 160, "var(--dgm-ripple-1)"),
              _entity("Gone", 220, 40, "var(--dgm-ripple-2)"))
LEVEL1 = _svg(500, _entity("Pet", 140, 40, "var(--dgm-ripple-2)"),
              _entity("Visit", 200, 220, "var(--dgm-ripple-1)"),
              _entity("Vet", 200, 340, "var(--dgm-ripple-1)"))

PAGE = f"""<!doctype html><html><head><meta charset="utf-8"><style>{assets.CSS}</style></head>
<body><div class="wrap"><div style="height:500px"></div>
<div class="diagram"><div class="dgmviews"><div class="dgmpane" data-view="diff">
<div class="focus"><span class="lbl">Diff + extra neighbours:</span>
<button type="button" data-level="0" aria-pressed="true">0</button>
<button type="button" data-level="1" aria-pressed="false">1</button></div>
<div class="svgbox" data-level="0">{LEVEL0}</div>
<div class="svgbox" data-level="1" hidden>{LEVEL1}</div>
</div></div></div><div style="height:2000px"></div></div>
{assets.FOCUS_JS}</body></html>"""

CENTRE = """(n) => { const g = document.querySelector('.svgbox:not([hidden]) g.entity[data-qualified-name="' + n + '"]');
  const r = g.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }"""
LAYOUT = """() => { const svg = document.querySelector('.svgbox:not([hidden]) svg'), s = svg.getBoundingClientRect();
  return [...svg.querySelectorAll('g.entity')].map(g => { const r = g.getBoundingClientRect();
    return [g.dataset.qualifiedName, Math.round(r.left - s.left), Math.round(r.top - s.top)]; }); }"""
LEFTOVERS = ("() => document.querySelectorAll('[style*=\"transform\"], .dgm-m-new, .dgm-m-fade, "
             ".dgm-m-glow, .dgm-m-ghost, .dgm-morphing').length")


def _open(p, tmp_path, **ctx):
    page_file = tmp_path / "page.html"
    page_file.write_text(PAGE, encoding="utf-8")
    try:
        browser = p.chromium.launch()
    except Exception as e:  # no browser downloaded for this interpreter
        pytest.skip(f"chromium unavailable: {e}")
    page = browser.new_page(viewport={"width": 1152, "height": 625}, **ctx)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(page_file.as_uri())
    page.evaluate("window.scrollTo(0, 400)")
    return browser, page, errors


def test_the_change_stays_put_the_shared_boxes_slide_and_nothing_is_left_behind(tmp_path):
    sync = pytest.importorskip("playwright.sync_api")
    with sync.sync_playwright() as p:
        browser, page, errors = _open(p, tmp_path)
        try:
            before = page.evaluate(CENTRE, "Visit")
            page.click('.focus button[data-level="1"]')
            page.wait_for_timeout(60)
            mid = page.evaluate("""() => ({
              moving: document.querySelectorAll('.svgbox:not([hidden]) g.entity[style*="transform"]').length,
              arriving: [...document.querySelectorAll('.dgm-m-new')].map(g => g.dataset.qualifiedName),
              ghost: document.querySelectorAll('.dgm-m-ghost').length })""")
            page.wait_for_timeout(1900)
            after = page.evaluate(CENTRE, "Visit")
            morphed, left = page.evaluate(LAYOUT), page.evaluate(LEFTOVERS)
            pressed = page.evaluate("() => document.querySelector('.focus button[aria-pressed=true]').dataset.level")
        finally:
            browser.close()
    assert not errors
    assert mid["moving"] >= 1 and mid["arriving"] == ["Pet"] and mid["ghost"] == 1
    assert abs(after[1] - before[1]) <= 1, "the changed box must stay where the eye was"
    assert left == 0 and pressed == "1"
    # The settled picture is the un-animated one.
    with sync.sync_playwright() as p:
        browser, page, _ = _open(p, tmp_path)
        try:
            page.evaluate("""() => document.querySelectorAll('.svgbox[data-level]').forEach(b => {
              b.hidden = b.dataset.level !== '1'; })""")
            plain = page.evaluate(LAYOUT)
        finally:
            browser.close()
    assert morphed == plain


def test_reduced_motion_keeps_the_anchor_and_the_glow_but_does_not_slide(tmp_path):
    sync = pytest.importorskip("playwright.sync_api")
    with sync.sync_playwright() as p:
        browser, page, errors = _open(p, tmp_path, reduced_motion="reduce")
        try:
            before = page.evaluate(CENTRE, "Visit")
            page.click('.focus button[data-level="1"]')
            page.wait_for_timeout(30)
            moving = page.evaluate("() => document.querySelectorAll('g.entity[style*=\"transform\"]').length")
            glowing = page.evaluate("() => [...document.querySelectorAll('.dgm-m-glow')].map(g => g.dataset.qualifiedName)")
            after = page.evaluate(CENTRE, "Visit")
            page.wait_for_timeout(1700)
            left = page.evaluate(LEFTOVERS)
        finally:
            browser.close()
    assert not errors
    assert moving == 0 and glowing == ["Pet"] and left == 0
    assert abs(after[1] - before[1]) <= 1


def test_the_chooser_pins_so_the_anchoring_scroll_never_takes_it_away():
    css = assets.CSS
    assert ".diagram .focus { position:sticky; top:var(--strip-h" in css
