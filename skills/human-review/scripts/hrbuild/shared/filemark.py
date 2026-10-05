"""What the branch did to a file, drawn rather than spelled: the one file glyph the page uses.

VS Code's `new-file` page with a mark in its cut corner — a `+` for a file that did not
exist, a pencil for one this branch edited (new lines in an existing file included), a
cross for one it deleted, nothing for one it left alone. It replaces the `NEW FILE` /
`NEW CODE` pills that used to trail a quoted block's file name: a word in caps beside a
name is read before the name is, a label louder than its subject.

One drawing for every place that says it — the source bar of every quoted block (built
by `extract-snippet.py`), the Sequence tab's test rows, the CODEOWNERS list — so a reader
who has learnt it on one tab is not taught it again on another. The Tests tab's
requirement map (`reqmap/reqmap.js`) draws the same paths in its own script, because it
renders in the browser. The words the glyph replaces stay on the hover and in the
accessibility tree, never dropped.
"""
from __future__ import annotations

import html

#: The page, its corner cut for the mark.
FILE_PAGE_D = ("M9.5 1.1l3.4 3.5.1.4v2h-1V6H8V2H3v11h4v1H2.5l-.5-.5"
               "v-12l.5-.5h6.7l.3.1zM9 2v3h2.9L9 2z")
#: The marks that sit in that corner: each is one or more path `d`s.
FILE_MARK_D = {
    "plus": ("M13 16h-1v-3H9v-1h3V9h1v3h3v1h-3v3z",),
    "pencil": ("M8.65 13.65 13.65 8.65 15.55 10.55 10.55 15.55Z"
               "M8.65 13.65 10.55 15.55 7.9 16.3Z",
               "M12.5 9.8 14.4 11.7 13.75 12.35 11.85 10.45Z"),
    # The plus turned 45 degrees — the same fact with the sign flipped.
    "cross": ("M16 9.7 15.3 9 12.5 11.8 9.7 9 9 9.7 11.8 12.5"
              " 9 15.3 9.7 16 12.5 13.2 15.3 16 16 15.3 13.2 12.5Z",),
}


def page_path(cls: str) -> str:
    return f'<path class="{cls}" d="{FILE_PAGE_D}"/>'


def mark_path(mark: str, cls: str) -> str:
    return "".join(f'<path class="{cls}" d="{d}"/>' for d in FILE_MARK_D[mark])


#: The source bar's own classes (`css/snippets.css` colours them).
FILE_PAGE = page_path("fm-page")
FILE_PLUS = mark_path("plus", "fm-mark")
FILE_PENCIL = mark_path("pencil", "fm-mark")


def filemark_kind(label: str) -> str:
    """`new` / `edited` / `unchanged` from the badge's own words.

    Keyed off the words rather than off git's `new`: `new file` and `new code` are both
    `new` to git and are not the same fact — one is a file that did not exist, the other is
    fresh lines inside one that did, which is an edit to that file."""
    return ("new" if label.startswith("new file")
            else "unchanged" if label.startswith("unchanged") else "edited")


def filemark(label: str, tip: str = "") -> str:
    """The glyph a source bar wears right after its file name, in place of a text badge.

    `label` is the words the badge used to print (`new file`, `new code`, `2 lines
    changed`, `unchanged`); they become the hover (`New file`) and the accessible name.
    `tip` is the count the badge's own hover carried, kept after a dash."""
    kind = filemark_kind(label)
    mark = {"new": FILE_PLUS, "edited": FILE_PENCIL, "unchanged": ""}[kind]
    said = f"{label[:1].upper()}{label[1:]}" + (f" &mdash; {html.escape(tip)}" if tip else "")
    return (f'<span class="filemark" data-kind="{kind}" role="img"'
            f' aria-label="{html.escape(label, quote=True)}" data-tip="{said}">'
            f'<svg viewBox="0 0 16 16" aria-hidden="true">{FILE_PAGE}{mark}</svg></span>')
