"""The colour theme a reader can choose, and the brand font a project can give the page.

Dark mode used to follow the system setting and nothing else: every dark rule on the page
sits in a `@media (prefers-color-scheme: dark)` block, and no button can switch a media
query. `themed_styles` gives each such block two forms at build time, both keyed on a
`data-theme` attribute of the root element that `assets/theme.js` sets in the head:

  * the block itself, its selectors narrowed to `:root:not([data-theme=light])` — the
    system's dark, unless the reader chose light;
  * a copy outside any media query, narrowed to `:root[data-theme=dark]` — dark, whatever
    the system says.

The rewrite is done on the finished page rather than on the asset files, so the files stay
what an editor and `test_build_split_identity.py` expect, and the dark blocks a fragment
brings in its own `<style>` (an `includeHtml` producer, a tab's inline sheet) switch too.
"""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path

DARK_QUERY = re.compile(r"@media\s*\(\s*prefers-color-scheme\s*:\s*dark\s*\)\s*\{")
STYLE_BLOCK = re.compile(r"(<style[^>]*>)(.*?)(</style>)", re.S)
COMMENT = re.compile(r"/\*.*?\*/", re.S)

AUTO_ROOT, AUTO_ATTR = ":root:not([data-theme=light])", ":not([data-theme=light])"
DARK_ROOT, DARK_ATTR = ":root[data-theme=dark]", "[data-theme=dark]"


def _block_end(css: str, i: int) -> int:
    """The index of the `}` that closes the block whose `{` is just before `i`."""
    depth = 1
    while i < len(css):
        if css.startswith("/*", i):
            end = css.find("*/", i + 2)
            i = len(css) if end < 0 else end + 2
            continue
        ch = css[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return len(css)


def _selectors(prelude: str) -> list[str]:
    """A selector list split on its top-level commas: `:is(.b,.c)` stays one selector."""
    out, depth, cur = [], 0, ""
    for ch in prelude:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    return out + [cur]


def _narrow(selector: str, root: str, attr: str) -> str:
    s = selector.strip()
    if s.startswith(":root"):
        return root + s[len(":root"):]
    if re.match(r"html(?![\w-])", s):
        # `html` is the root element: it takes the attribute itself, never as a descendant.
        return "html" + attr + s[len("html"):]
    return f"{root} {s}"


def _rules(body: str, root: str, attr: str) -> str:
    """Every rule of a dark block, its selectors narrowed; a nested at-rule recursed into."""
    body = COMMENT.sub("", body)
    out, i = [], 0
    while True:
        brace = body.find("{", i)
        if brace < 0:
            out.append(body[i:])
            break
        end = _block_end(body, brace + 1)
        prelude, inner = body[i:brace], body[brace + 1:end]
        if prelude.strip().startswith("@"):
            out.append(f"{prelude}{{{_rules(inner, root, attr)}}}")
        else:
            lead = prelude[:len(prelude) - len(prelude.lstrip())]
            sel = ",".join(_narrow(s, root, attr) for s in _selectors(prelude))
            out.append(f"{lead}{sel} {{{inner}}}")
        i = end + 1
    return "".join(out)


def switchable(css: str) -> str:
    """`css` with every `prefers-color-scheme: dark` block in its auto and forced forms."""
    out, i = [], 0
    for m in DARK_QUERY.finditer(css):
        if m.start() < i:
            continue  # inside a block already rewritten
        end = _block_end(css, m.end())
        body = css[m.end():end]
        out.append(css[i:m.start()])
        out.append(m.group(0) + _rules(body, AUTO_ROOT, AUTO_ATTR) + "}")
        out.append(_rules(body, DARK_ROOT, DARK_ATTR))
        i = end + 1
    out.append(css[i:])
    return "".join(out)


def themed_styles(doc: str) -> str:
    """Every `<style>` block of the page made switchable; nothing outside them touched."""
    return STYLE_BLOCK.sub(lambda m: m.group(1) + switchable(m.group(2)) + m.group(3), doc)


#: The theme button; its label is set by theme.js, and "Theme: Auto" is what a page without
#: JavaScript, or before it runs, would truthfully say.
THEME_BUTTON = '<button type="button" class="chip chip-theme" id="hr-theme">Theme: Auto</button>'


FONT_TYPES = {".ttf": "truetype", ".otf": "opentype", ".woff": "woff", ".woff2": "woff2"}


def font_css(root: Path) -> str:
    """The project's brand font, inlined, from `human-review.json`'s `font` block:

        "font": {"family": "Sofia", "files": {"400": "path/Sofia-Regular.ttf",
                                              "600": "path/Sofia-SemiBold.ttf"}}

    Paths are relative to the checkout, absolute, or `~`. The files are inlined as data
    URIs because the page is one file: it is opened from disk, served, and zipped, and a
    font that lives beside it is a font one of those three loses. Kept out of the skill's
    own files on purpose — a brand font is licensed to whoever bought it, not to a
    public repository. No block, or a file that is not there: no font, and the page keeps
    Arial."""
    try:
        cfg = json.loads((Path(root) / "human-review.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    font = cfg.get("font") if isinstance(cfg, dict) else None
    if not isinstance(font, dict) or not font.get("family"):
        return ""
    faces = []
    for weight, raw in (font.get("files") or {}).items():
        path = Path(str(raw)).expanduser()
        path = path if path.is_absolute() else Path(root) / path
        try:
            data = base64.b64encode(path.read_bytes()).decode()
        except OSError:
            return ""
        kind = FONT_TYPES.get(path.suffix.lower(), "truetype")
        mime = "font/" + path.suffix.lower().lstrip(".")
        faces.append(f'@font-face{{font-family:"{font["family"]}";font-weight:{weight};'
                     f"font-style:normal;font-display:swap;"
                     f'src:url(data:{mime};base64,{data}) format("{kind}")}}')
    if not faces:
        return ""
    return "".join(faces) + f':root{{--font-sans:"{font["family"]}",Arial,Helvetica,sans-serif}}'
