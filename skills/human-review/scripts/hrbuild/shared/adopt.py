"""The "Prompt to get this" buttons: one per adoptable piece, inside the card it is about.

Every tab is its own module with its own producer, and several tabs are more than one
mechanism — the Data tab's domain model is drawn by reflection over the classes, its ERD
from the migration scripts, its conceptual model by hand. A reader who likes one of them
wants that one in their own repository, so each piece offers a prompt they paste into
their own coding agent, from the corner of the card that shows it.

Minimal on purpose (5 Oct 2026, Victor): the agent on the other end is a smart model with
the repository at hand. It needs to know which piece, where it starts, and that it should
take that piece and nothing else — not a tutorial on how the piece works.

Placed after rendering, by anchor, rather than emitted by each renderer: five of these
cards come out of producer scripts (`includeHtml` fragments cached under `.human-review/`),
and a button that needed a producer change would also need every cached fragment
regenerated — the DS audit through Docker, the Tests matrix through a model. Here the
producers stay unaware of the button; the cost is that `PLACES` names their classes, and
`test_adopt.py` fails the day one of those classes stops being emitted.
"""
from __future__ import annotations

import html
import re

from .footer import HOME_URL

#: Not the 📋 the copy commands wear: this one is a message for an agent, not a command.
ROBOT = "\U0001F916"   # 🤖

PETCLINIC = "https://github.com/victorrentea/petclinic/blob/main/petclinic-backend/"

#: piece → (what the button gets you, where it starts). A path is under
#: `skills/human-review/`; a URL is a reference implementation in another repository.
PIECES: dict[str, tuple[str, str]] = {
    "review.assumed": (
        "the coder's assumptions listed for a human reviewer — every place the ticket did "
        "not decide, the reading the coding agent chose, how sure it was, and the "
        "alternative it did not take",
        "reference/review-points.md, scripts/authoring-sessions.py, scripts/review-points.py"),
    "review.open": (
        "an AI code review of the branch that leaves its open issues for a human, each "
        "with its severity, the reviewer that raised it and the code it is about",
        "reference/review-prompt.md, reference/review-points.md, scripts/review-points.py"),
    "review.fixed": (
        "an auto-fix round after that review: the issues it accepted, fixed in one commit "
        "and shown with their diffs",
        "reference/review-prompt.md, scripts/rerun-review.py, scripts/review-points.py"),
    "behaviour": (
        "a narrated film of the feature working, recorded by a Playwright script, with its "
        "captions as a clickable transcript beside the player",
        "reference/film-prompt.md, reference/feature-script.md, "
        "scripts/record-feature-video.sh"),
    "api": (
        "the REST contract at the merge-base against the branch, as a visual OpenAPI diff "
        "with a breaking-change verdict", "scripts/openapi-visual-diff.py, "
        "scripts/openapi-compat.py"),
    "diagram.domain": (
        "the domain-model class diagram generated from your domain classes by Java "
        "reflection, committed as PlantUML and diffed base against branch",
        PETCLINIC + "src/test/java/victor/training/petclinic/guardrail/"
        "DomainModelExtractorTest.java, scripts/puml-diff.sh"),
    "diagram.db": (
        "the ERD generated from your DB migration scripts, committed as PlantUML and "
        "diffed base against branch, with the schema changes it cannot draw listed under it",
        PETCLINIC + "docs/scripts/db/db_schema_to_puml.py, scripts/puml-diff.sh"),
    "diagram.drawio": (
        "the hand-drawn draw.io {title} diagram, checked against the code by a test and "
        "diffed base against branch",
        PETCLINIC + "src/test/java/victor/training/petclinic/guardrail/"
        "ConceptualModelDiagramTest.java, " + PETCLINIC + "src/test/java/victor/training/"
        "petclinic/guardrail/DeploymentDiagramTest.java, scripts/drawio-diff.py"),
    "diagram.packages": (
        "the package diagram, kept as PlantUML, enforced on the code by ArchUnit and "
        "diffed base against branch", PETCLINIC + "src/test/java/victor/training/petclinic/"
        "guardrail/PackagesArchTest.java, scripts/puml-diff.sh"),
    "diagram.modules": (
        "the module graph generated from your build files, committed as PlantUML and "
        "diffed base against branch",
        PETCLINIC + "docs/scripts/mavenmodules/maven_modules_to_puml.py, scripts/puml-diff.sh"),
    "diagram.c2": (
        "the C4 container (C2) diagram projected from traced test runs — every arrow an "
        "observed call — diffed base against branch",
        "scripts/c2-from-sequence.py, scripts/puml-diff.sh"),
    "diagram": (
        "the {title} diagram, kept in the repository as PlantUML and diffed base against "
        "branch", "scripts/puml-diff.sh"),
    "requirements": (
        "the ticket's requirements mapped to the tests that prove each one, side by side, "
        "with the changed lines no test runs",
        "reference/matrix-prompt.md, scripts/rerun-model.py, scripts/testcov.py"),
    "sequence": (
        "sequence diagrams drawn from traced test runs, each beside the test that drew it",
        "scripts/hrbuild/shared/genseq.py, scripts/puml-diff.sh"),
    "city": ("a 3D Code City of the classes, coloured by what the branch changed",
             "scripts/regenerate-codecity.sh, https://github.com/victorrentea/code-city"),
    "dsaudit": ("every UI screen at the base against the branch, audited for controls from "
                "outside the design system", "scripts/ds-audit.py"),
    "complexity": ("the cognitive complexity of every entry point the branch touched, "
                   "before and after", "scripts/endpoint-complexity-delta.py"),
    "logging": ("every log statement the branch added, found by syntax-aware search and "
                "checked for privacy problems", "scripts/logextract.py"),
    "owners": ("a check that CODEOWNERS still covers every file the branch touched, and "
               "who must approve it", "scripts/codeowners-check.py"),
    "cost": ("what writing and reviewing the change cost in model tokens",
             "scripts/review-cost.py, scripts/harness_cost.py"),
}

#: A diagram card's piece, read off its head (title and source file), first match wins.
DIAGRAM_KINDS = (
    ("diagram.drawio", re.compile(r"\.drawio\b", re.I)),
    ("diagram.domain", re.compile(r"domain\s*model", re.I)),
    ("diagram.db", re.compile(r"\bDB\b|\bERD\b|\bschema\b", re.I)),
    ("diagram.c2", re.compile(r"\bC2\b", re.I)),
    ("diagram.modules", re.compile(r"\bmodules?\b", re.I)),
    ("diagram.packages", re.compile(r"\bpackages?\b", re.I)),
)

#: tab → where its buttons go: (piece, how, the opening tag it anchors on, which match).
#: `in` — a row at the end of that card, inside its border; `after` — a row right under
#: it; `col` — under it in a column of its own (the Demo's transcript, beside the player);
#: `float` — over the bottom-right corner of the Tests panes, which fill the viewport and
#: have no height to give; `upto` — a row closing the region that starts at the anchor and
#: runs to the next Round kicker (the Review tab's three piles). Piece None is a diagram
#: card, whose piece is read off its head. A tab whose anchor is missing gets one row at
#: the end of the panel, so a renamed class costs placement, never the button.
DIAGRAM_CARD = r'<div class="diagram(?![^"]*\bdgm-bare\b)[^"]*"'
PLACES: dict[str, tuple[tuple[str | None, str, str, str], ...]] = {
    "review": (("review.assumed", "upto", r'<h2 id="assumed"', "first"),
               ("review.open", "upto", r'<h2 id="first"', "first"),
               ("review.fixed", "upto", r'<h2 id="fixed"', "first")),
    "behaviour": (("behaviour", "col", r'<ol class="transcript"', "first"),),
    "api": (("api", "after", r'<iframe class="oaviframe"', "first"),),
    "data": ((None, "in", DIAGRAM_CARD, "all"),),
    "packages": ((None, "in", DIAGRAM_CARD, "all"),),
    "requirements": (("requirements", "float", r'<div class="rm-side"', "first"),),
    "sequence": (("sequence", "after", r'<details class="testpair"', "last"),),
    "city": (("city", "after", r'<a class="city"', "first"),),
    "dsaudit": (("dsaudit", "in", r'<div class="dsa"', "first"),),
    "complexity": (("complexity", "in", r'<div class="cx-list"', "last"),),
    "logging": (("logging", "after", r'<figure class="snippet"', "last"),),
    "owners": (("owners", "in", r'<div class="cow-row\b', "last"),),
    "cost": (("cost", "after", r'<table class="costtab\b', "first"),),
}

# One token of markup: a comment, a whole script/style element (whose text may say `<div`
# without opening one), or a tag — attribute values may hold a `>`.
_TAG = re.compile(r'<!--.*?-->|<(script|style)\b.*?</\1\s*>'
                  r'|<(/?)([a-zA-Z][\w-]*)(?:"[^"]*"|\'[^\']*\'|[^\'">])*>', re.S | re.I)


def _close(doc: str, start: int) -> tuple[int, int] | None:
    """Where the element opening at `start` closes: (start, end) of its closing tag."""
    first = _TAG.match(doc, start)
    if not first or not first.group(3):
        return None
    name, depth = first.group(3).lower(), 1
    for m in _TAG.finditer(doc, first.end()):
        if (m.group(3) or "").lower() != name or m.group(0).endswith("/>"):
            continue
        depth += -1 if m.group(2) else 1
        if not depth:
            return m.start(), m.end()
    return None


def adopt_prompt(piece: str, title: str = "") -> str | None:
    """The prompt a button copies, or None for a piece with nothing to get."""
    if piece not in PIECES:
        return None
    what, start = PIECES[piece]
    what = what.format(title=title or "this")
    starts = ", ".join(s if s.startswith("http") else f"skills/human-review/{s}"
                       for s in start.split(", "))
    return (f"Get {what} into this repository — one piece of the review page of "
            f"{HOME_URL}. Start from {starts}. Take only that piece, adapt it to this "
            "project's stack, run it on the current branch against its merge-base and "
            "show me the result.")


def adopt_html(piece: str, title: str = "", how: str = "in") -> str:
    prompt = adopt_prompt(piece, title)
    if not prompt:
        return ""
    return (f'<div class="adoptline adopt-{how}"><button type="button" class="adopt copycmd" '
            f'data-piece="{html.escape(piece)}" data-copy="{html.escape(prompt, quote=True)}" '
            'data-say="Copied — paste it to your coding agent" '
            'data-tip="Copy a prompt for your coding agent to get this into your project">'
            f'{ROBOT} Prompt to get this</button></div>')


def place_prompts(tid: str, body: str) -> str:
    """The panel body with every one of its pieces' buttons in place."""
    places = PLACES.get(tid)
    if not places:
        return body
    edits = []                      # (at, cut_to, text): applied back to front
    for piece, how, anchor, which in places:
        hits = list(re.finditer(anchor, body))
        hits = hits if which == "all" else hits[-1:] if which == "last" else hits[:1]
        taken = []                  # a card inside a card already given its button
        for hit in hits:
            if any(a < hit.start() < b for a, b in taken):
                continue
            if how == "upto":
                nxt = re.compile(r'<p class="pileround"').search(body, hit.end())
                at = nxt.start() if nxt else len(body)
                edits.append((at, at, adopt_html(piece, how="after")))
                continue
            span = _close(body, hit.start())
            if not span:
                continue
            taken.append((hit.start(), span[1]))
            name, title = piece, ""
            if piece is None:       # a diagram card: its piece is read off its head
                head = re.search(r'<div class="head">(.*?)</div>', body[hit.start():span[0]],
                                 re.S)
                text = html.unescape(re.sub(r"<[^>]+>", " ", head.group(1) if head else ""))
                b = re.search(r"<b>(.*?)</b>", head.group(1) if head else "", re.S)
                title = html.unescape(re.sub(r"<[^>]+>", "", b.group(1))).strip() if b else ""
                name = next((k for k, rx in DIAGRAM_KINDS if rx.search(text)), "diagram")
            if how == "in":
                edits.append((span[0], span[0], adopt_html(name, title, "in")))
            elif how == "col":
                edits.append((hit.start(), hit.start(), '<div class="adoptcol">'))
                edits.append((span[1], span[1], adopt_html(name, title, "after") + "</div>"))
            else:
                edits.append((span[1], span[1], adopt_html(name, title, how)))
    if not edits:
        # The anchor moved: the button loses its place, not its existence.
        first = next(p for p, *_ in places)
        return body + (adopt_html(first, how="after") if first else "")
    for at, to, text in sorted(edits, key=lambda e: e[0], reverse=True):
        body = body[:at] + text + body[to:]
    return body
