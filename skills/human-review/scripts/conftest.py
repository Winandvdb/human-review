"""What the tests next door share.

The layout they build (`_old_layout_unless_asked`), and `page_source()`, which exists
because the page builder stopped being one file. Half a dozen tests are *guardrails over the source text* — "only one place emits this control",
"the green in the palette is the same green the diff painter uses", "every key
`review-points.py` writes is a key the renderer reads". They used to read
`build-review-html.py` and get everything the page is made of, because everything the
page is made of was in it.

It is now a package (`hrbuild/`), so reading that one file gets the orchestration and
none of the rendering. `page_source()` gives those tests what they were actually asking
for: every line the page is built from, in one string.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

# A build reads the PR's description from GitHub (`attach_pr_body`); the suite's fixtures
# name real PR URLs, and a test must not depend on the network or on what a PR says today.
os.environ.setdefault("HR_NO_GITHUB", "1")

HERE = Path(__file__).resolve().parent


@pytest.fixture(autouse=True)
def _old_layout_unless_asked(monkeypatch):
    """The redesigned page is the default, but most tests here were written against the
    old one and still test it: they build it unless a test asks for a layout itself."""
    if "HUMAN_REVIEW_LAYOUT" not in os.environ:
        monkeypatch.setenv("HUMAN_REVIEW_LAYOUT", "old")


def page_source() -> str:
    """The orchestrator, every module of `hrbuild/`, and every asset it inlines.

    Concatenated rather than parsed: these are grep-shaped guardrails, and a guardrail
    that has to understand Python to fire is a guardrail that stops firing the first time
    somebody writes the thing it forbids in a way it did not anticipate."""
    pkg = HERE / "hrbuild"
    parts = [(HERE / "build-review-html.py").read_text(encoding="utf-8")]
    parts += [p.read_text(encoding="utf-8") for p in sorted(pkg.rglob("*.py"))]
    # Text assets only: a binary one (the angry robot's PNG) has no source to grep.
    parts += [p.read_text(encoding="utf-8") for p in sorted((pkg / "assets").rglob("*"))
              if p.is_file() and p.suffix.lower() not in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".woff", ".woff2"}]
    return "\n".join(parts)
