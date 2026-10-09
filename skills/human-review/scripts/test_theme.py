"""The page's colour theme: dark mode that a reader can force either way, and the brand font.

Dark mode used to follow the system setting only: every dark rule sat in a
`@media (prefers-color-scheme: dark)` block, which no button can switch. The build now
gives each such block a second form keyed on `data-theme` on the root element, and a
script in the head sets that attribute from the reader's last choice before the first
paint.
"""
from __future__ import annotations

import base64
import importlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
theme = importlib.import_module("hrbuild.shared.theme")

AUTO = ":root:not([data-theme=light])"
DARK = ":root[data-theme=dark]"


def test_a_dark_block_gets_an_auto_form_and_a_forced_form():
    css = (":root{--a:1}"
           "@media (prefers-color-scheme: dark) { :root { --a:2; } .x, .y > b { color:red; } }"
           ".z{color:blue}")
    out = theme.switchable(css)
    auto = out[out.index("@media"):out.index(DARK)]
    assert f"{AUTO}{{ --a:2; }}" in auto.replace(" {", "{")
    assert f"{AUTO} .x,{AUTO} .y > b" in auto, "every selector of a list is prefixed"
    forced = out[out.index(DARK):out.index(".z{")]
    assert f"{DARK}{{ --a:2; }}" in forced.replace(" {", "{")
    assert f"{DARK} .x,{DARK} .y > b" in forced
    assert "@media" not in forced, "the forced form applies whatever the system says"
    assert out.startswith(":root{--a:1}") and out.endswith(".z{color:blue}"), \
        "rules outside a dark block are untouched, and the order is kept"


def test_the_rewrite_reads_the_query_however_it_is_spaced_and_keeps_other_media():
    out = theme.switchable("@media (prefers-color-scheme:dark){.a{color:red}}"
                           "@media (max-width:600px){.b{color:red}}")
    assert f"{AUTO} .a" in out and f"{DARK} .a" in out
    assert "@media (max-width:600px){.b{color:red}}" in out


def test_html_and_root_selectors_take_the_attribute_themselves():
    out = theme.switchable("@media (prefers-color-scheme: dark){html.x b{color:red}"
                           ":root .y{color:red}}")
    assert "html[data-theme=dark].x b" in out and "html:not([data-theme=light]).x b" in out
    assert f"{DARK} .y" in out and f"{AUTO} .y" in out
    assert ":root[data-theme=dark] html" not in out, "html is the root: never its descendant"


def test_a_comma_inside_a_pseudo_class_does_not_split_the_selector():
    out = theme.switchable("@media (prefers-color-scheme: dark){.a:is(.b,.c){color:red}}")
    assert f"{DARK} .a:is(.b,.c)" in out


def test_only_style_blocks_are_rewritten():
    doc = ("<style>@media (prefers-color-scheme: dark){.a{color:red}}</style>"
           "<p>@media (prefers-color-scheme: dark){.b{color:red}}</p>")
    out = theme.themed_styles(doc)
    assert f"{DARK} .a" in out and f"{DARK} .b" not in out


def test_the_brand_font_is_embedded_from_the_project_config(tmp_path):
    (tmp_path / "fonts").mkdir()
    (tmp_path / "fonts" / "r.ttf").write_bytes(b"regular")
    (tmp_path / "fonts" / "s.ttf").write_bytes(b"semibold")
    (tmp_path / "human-review.json").write_text(json.dumps({"font": {
        "family": "Sofia", "files": {"400": "fonts/r.ttf", "600": "fonts/s.ttf"}}}))
    css = theme.font_css(tmp_path)
    assert css.count("@font-face") == 2
    assert base64.b64encode(b"regular").decode() in css, "inlined: the page is one file"
    assert "font-weight:600" in css
    assert '--font-sans:"Sofia",Arial,Helvetica,sans-serif' in css


def test_without_a_font_in_the_config_the_page_keeps_arial(tmp_path):
    assert theme.font_css(tmp_path) == ""
    (tmp_path / "human-review.json").write_text(json.dumps({"font": {
        "family": "Sofia", "files": {"400": "missing.ttf"}}}))
    assert theme.font_css(tmp_path) == "", "a missing file is no font, not a broken page"
