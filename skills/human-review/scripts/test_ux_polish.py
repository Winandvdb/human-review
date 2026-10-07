"""The adversarial UX review of 7 Oct 2026, held: each finding the page fixed, pinned to the
rule that fixes it, so a later edit to the same stylesheet cannot quietly bring it back.

The numbers in the test names are the review's own finding numbers."""
import importlib.util
import re
from pathlib import Path

HERE = Path(__file__).parent
CSS = HERE / "hrbuild" / "assets" / "css"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _load(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _rule(css: str, selector: str) -> str:
    """The declarations of every rule whose selector list is exactly `selector`, joined."""
    out = []
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        sel = re.sub(r"/\*.*?\*/", "", m.group(1), flags=re.S).strip()
        if sel == selector:
            out.append(re.sub(r"/\*.*?\*/", "", m.group(2), flags=re.S))
    return " ".join(out)


def test_3_a_quiet_tab_is_faded_not_struck_through():
    rule = _rule(_read(CSS / "frame.css"), "button.tab.quiet")
    assert "line-through" not in rule and "text-decoration:none" in rule
    assert "opacity:.5" in rule


def test_4_the_active_half_of_new_old_has_no_underline_to_cut_the_pill():
    css = _read(CSS / "diagrams.css")
    on = _rule(css, ".dgmbar .dgm-newold u.on")
    assert on and "underline" not in on and "opacity:1" in on
    assert "opacity:.5" in _rule(css, ".dgmbar .dgm-newold u")


def test_5_the_extension_column_is_one_width():
    rule = _rule(_read(HERE / "reqmap" / "reqmap.css"), ".reqmap .rm-tw")
    assert "min-width:51px" in rule and "text-align:right" in rule


def test_6_the_filter_pills_are_one_width():
    rule = _rule(_read(HERE / "reqmap" / "reqmap.css"), ".reqmap .rm-cats .rm-cat")
    assert "min-width:70px" in rule and "justify-content:center" in rule


def test_8_unchanged_sits_beside_the_file_name():
    assert "margin-left:auto" in _rule(_read(CSS / "diagrams.css"), ".diagram .head > b + .badge")


def test_10_tooltips_are_opaque():
    js = _read(HERE / "hrbuild" / "assets" / "tip.js")
    bg = re.search(r"\.tip\{[^}]*?background:([^;]+);", js).group(1)
    assert bg == "#141416", bg


def test_11_the_branch_badge_does_not_make_the_masthead_taller():
    css = _read(CSS / "masthead.css")
    assert "align-items:center" in _rule(css, ".masthead .scopebar")
    badge = _rule(css, ".chip.refchip .sn-badge")
    assert "line-height:inherit" in badge and "padding:0 0 0 .3rem" in badge and "border:0" in badge


def test_12_tests_fan_and_caret_are_readable_on_dark():
    css = _read(HERE / "reqmap" / "reqmap.css")
    assert "opacity:.8" in _rule(css, ".reqmap .rm-link")
    assert "opacity:.8" in _rule(css, ".reqmap .rm-chev")


def test_12_the_api_toolbar_follows_the_scheme_and_info_reads_on_dark():
    src = _read(HERE / "openapi-visual-diff.py")
    bar = re.search(r"\.dv-bar \{(.*?)\n  \}", src, re.S).group(1)
    assert "background: var(--dv-bar-bg); color: var(--dv-bar-fg);" in bar
    assert "#1b1b1f" not in bar
    # light first (the page's default), then the dark value in both dark blocks
    assert "--dv-bar-bg: #e9ebf1;" in src
    assert src.count("--dv-bar-bg: #1b1b1f;") == 2 and src.count("--dv-lvl1: #4ade80;") == 2
    assert ".dv-change.l1 .lvl { background: rgba(46,158,91,.12); color: var(--dv-lvl1); }" in src
    assert ".dv-chip.off { opacity: .6; }" in src


def test_15_a_monospace_link_underline_clears_its_underscores():
    src = _read(HERE / "codeowners-check.py")
    assert ".cow-file { text-underline-offset:4px; text-decoration-thickness:1px; }" in src


def test_16_a_link_gets_the_hand_not_the_question_mark():
    rule = _rule(_read(CSS / "review.css"), "a.specref")
    assert "cursor:pointer" in rule and "cursor:help" not in rule
    # the UX tab's "19 of 19 screens changed" toggles a box: a hand too
    assert ".dsa-count { text-decoration: underline dotted; text-underline-offset: 3px; " \
           "cursor: pointer; }" in _read(HERE / "ds-audit.py")


def test_17b_change_count_pills_are_one_width():
    src = _read(HERE / "openapi-visual-diff.py")
    badge = re.search(r"\.dv-badge \{(.*?)\n  \}", src, re.S).group(1)
    assert "min-width: 80px; text-align: center;" in badge


def test_17c_voices_are_emoji_faces_each_with_a_spoken_name():
    """Superseded by Victor (7 Oct 2026): no word beside the 🐘 — every voice is an emoji
    (👩 standard, 🐘, 🌍 Discovery), each still named for a screen reader."""
    demo = _load("hr_demo_for_ux", "build-review-html.py")
    html = demo.voice_switch("assets/feature.webm",
                             [("trump", "assets/f.voice-trump.webm", "\U0001F418", [], "")])
    assert ('aria-label="cloned voice"> <span class="vs-emoji">\U0001F418</span></label>') in html
    assert demo.voice_face("discovery", "Discovery") == (
        '<span class="vs-emoji">\U0001F30D</span>', "Discovery")
    assert demo.voice_face("", "standard")[1] == "Standard voice"
    assert "font-size:1.3em" in _rule(_read(CSS / "demo.css"), ".voice-switch .vs-emoji")
