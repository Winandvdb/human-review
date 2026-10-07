"""The repository's own C4 views, as Structurizr draws them (`structurizr-views.py`).

One card per view, on the Structure tab, in the gallery's card: title, the view's own
description, the UNCHANGED badge when the branch left it alone, the DSL file on the right,
and — when the DSL moved — the New/Old switch every diagram card wears. There is no Diff
pane: Structurizr draws a workspace, not the difference between two, and a delta drawn by
anything else would no longer be Structurizr's picture. The two sides are its two renders.

The pictures are `<img>`s of the SVGs Structurizr exported, not inlined markup. Its SVG is
a JointJS document with a `<style>` of its own and white text on purpose-picked fills; the
page's inliner (`svg.py`) recolours PlantUML's palette to the page's variables, and run
over this it would repaint Structurizr's boxes in the page's colours. As an image it stays
exactly what Structurizr drew. Both of Structurizr's own renderings travel — its light
mode and its dark mode — and the page's colour scheme picks one (`css/c4.css`), so a dark
page shows Structurizr's dark render rather than a white slab.
"""
from __future__ import annotations

import base64
import html
import json
import re
from pathlib import Path

from .diagrams import UNCHANGED, UNCHANGED_BADGE, _source_link, dgm_views_html, read_manifest

#: Where `structurizr-views.py` writes, relative to the review directory.
C4_DIR = "assets/c4"

C4_VIEWBOX = re.compile(r'viewBox="\s*[-\d.]+\s+[-\d.]+\s+([\d.]+)\s+([\d.]+)\s*"')

#: The scale a Structurizr render is shown at, at most. Its boxes are drawn for a canvas
#: (24px type in a 450px box); at full size one container view is three screens wide. Half
#: size is the size the type reads at on a page; a narrower card shrinks it further.
C4_SCALE = 0.5


def _c4_img(path: Path, cls: str, alt: str) -> str:
    svg = path.read_text(encoding="utf-8")
    m = C4_VIEWBOX.search(svg)
    size = (f' width="{round(float(m[1]) * C4_SCALE)}" height="{round(float(m[2]) * C4_SCALE)}"'
            if m else "")
    data = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return (f'<img class="{cls}" src="data:image/svg+xml;base64,{data}"{size} '
            f'alt="{html.escape(alt, quote=True)}" decoding="async">')


def _c4_picture(row: dict, side: str, assets: Path) -> str:
    """Structurizr's light and dark render of one side, the page's scheme picking one."""
    imgs = []
    for mode in ("light", "dark"):
        name = (row.get(f"{side}_{mode}") or "").strip()
        if name and (assets / name).is_file():
            imgs.append(_c4_img(assets / name, f"c4-{mode}",
                                f"{row['name']} — drawn by Structurizr"))
    if not imgs:
        return ""
    if len(imgs) == 1:          # one mode only: show it in both schemes
        imgs[0] = imgs[0].replace('class="c4-light"', 'class="c4-only"') \
                         .replace('class="c4-dark"', 'class="c4-only"')
    return f'<div class="svgbox c4box">{"".join(imgs)}</div>'


def _c4_body(row: dict, assets: Path) -> tuple[str, bool]:
    """The picture(s) of one view, and whether the card toggles between two of them."""
    new, old = _c4_picture(row, "new", assets), _c4_picture(row, "old", assets)
    if row.get("status") == "modified" and new and old:
        views = dgm_views_html([("new", new), ("old", old)], initial="new")
        # Two renders and no delta: the Diff button would switch to a pane that is not
        # there. The New/Old button alone is the whole control.
        views = re.sub(r'<button type="button" class="dgm-diff"[^>]*>Diff</button>', "",
                       views, count=1)
        return views, True
    return (new or old
            or '<p class="sub">not rendered — re-run the <code>c4</code> step</p>'), False


def _c4_badge(status: str) -> str:
    if status == UNCHANGED:
        return UNCHANGED_BADGE
    if status == "added":
        return '<span class="badge sev-high">new</span>'
    if status == "modified":
        return ""
    return f'<span class="badge sev-low">{html.escape(status)}</span>'


def render_c4(block: dict, root: Path, out_dir: Path) -> tuple[str, int, int]:
    """The `c4` block: (html, weight, changes), as `render_block` wants them."""
    assets = out_dir / (block.get("dir") or C4_DIR)
    try:
        verdict = json.loads((assets / "verdict.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        verdict = {}
    rows = read_manifest(assets / "MANIFEST.tsv")
    if not rows:
        if not verdict:
            return "", 0, 0
        why = verdict.get("reason") or "the c4 step drew nothing"
        dsl = ", ".join(Path(w).name for w in verdict.get("workspaces") or [])
        return (f'<p class="sub c4-none">C4 views{f" in <code>{html.escape(dsl)}</code>" if dsl else ""}'
                f' not drawn by Structurizr — {html.escape(why)}. The next refresh tries again.</p>', 1, 0)
    parts, changed = [], 0
    for r in rows:
        status = r.get("status") or ""
        changed += status != UNCHANGED
        body, toggles = _c4_body(r, assets)
        desc = r.get("description") or r.get("title") or ""
        note = (r.get("note") or "").strip()
        parts.append(
            f'<div class="diagram dgm-c4{" dgm-toggles" if toggles else ""}" '
            f'id="c4-{html.escape(re.sub(r"[^A-Za-z0-9_-]+", "-", r["name"]), quote=True)}">'
            f'<div class="head"><b>{html.escape(r["name"])}</b>'
            # Whose picture this is, before what it shows: the same view names (C2,
            # Containers) are on the projected card above, drawn by another program.
            + f'<span class="c4-desc">Structurizr{" · " + html.escape(desc) if desc else ""}</span>'
            + _c4_badge(status)
            + _source_link(r["source"], root) + '</div>'
            + body
            + (f'<p class="sub dgm-stale">{html.escape(note)}</p>' if note else "")
            + '</div>')
    return "\n".join(parts), len(rows), changed
