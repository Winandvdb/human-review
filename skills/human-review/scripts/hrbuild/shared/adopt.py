"""The "Prompt to get this" buttons: one per adoptable piece, where that piece ends.

Every tab is its own module with its own producer, and several tabs are more than one
mechanism — the Data tab's domain model is drawn by reflection over the classes, its ERD
from the migration scripts, its conceptual model by hand. A reader who likes one of them
wants that one in their own repository, so each piece offers a prompt they paste into
their own coding agent, from the corner of the card that shows it — or, when the piece is
the whole tab, from the right end of the tab's title row.

Minimal on purpose (5 Oct 2026, Victor): the agent on the other end is a smart model with
the repository at hand. It needs to know which piece, where it starts, and that it should
take that piece and nothing else — not a tutorial on how the piece works.

Placed after rendering, by anchor, rather than emitted by each renderer: five of these
cards come out of producer scripts (`includeHtml` fragments cached under `.human-review/`),
and a button that needed a producer change would also need every cached fragment
regenerated — the DS audit through Docker, the Tests matrix through a model. Here the
producers stay unaware of the button; the cost is that `PLACES` names the classes of the
cards that carry one, and `test_adopt.py` fails the day one of those stops being emitted.
"""
from __future__ import annotations

import html
import json
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
        "with every test that runs the changed lines",
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


#: The (i) beside every pill: what the reader is looking at, before they copy a prompt for
#: it (7 Oct 2026, Victor: "whoever goes to click Prompt to get this should first
#: understand what they're looking at"). Static, the same on every PR, so no line may
#: state what only one PR shows; an example is marked "e.g.". 2-4 short lines, plain
#: English, a tiny petclinic example: an ADHD-friendly read, not documentation.
#: Keyed by piece, or by "piece:Card title" when one piece covers unlike cards (the two
#: draw.io diagrams). `move`: the tab's own "how this was made" line, a CSS selector,
#: moved into the box so the visible page stays calm (its counts stay live).
#: `li` lines, then `ex` (one muted example line) and/or `code` (a tiny snippet; HTML).
EXPLAIN: dict[str, dict[str, object]] = {
    'review.assumed': {
        "li": [
            'Where the ticket was vague: the guess the coder made, and how sure it was.',
            'Read these first: a wrong guess is a wrong feature, however clean the code.',
        ],
        "ex": 'e.g. the ticket says "link a vet to a visit" but not whether the vet is optional.',
    },
    'review.open': {
        "li": [
            'What AI reviewers flagged that nobody has fixed yet.',
            '<b>must look</b> › <b>worth a look</b> › <b>nit</b>. Agree or disagree with each.',
        ],
    },
    'review.fixed': {
        "li": [
            'Issues the reviewers raised that an agent already fixed, one diff each.',
            'Skim them: a fix can be wrong too.',
        ],
    },
    'behaviour': {
        "li": [
            'A film of the feature: a script clicks through the real app; a voice explains.',
            'Click a transcript line to jump there.',
            '<b>Running app</b> (top): start this exact build and try it yourself.',
        ],
    },
    'api': {
        "li": [
            'The REST contract (OpenAPI) on main vs this branch, diffed by oasdiff.',
            '<b>Breaking</b>: a client written for main can now fail. <b>Info</b>: harmless, e.g. a new optional field.',
        ],
        "code": (
            '<span class="c">e.g. GET /api/owners/1</span>\n'
            '<span class="c">main:  </span>{ "name": "Leo" }\n'
            '<span class="c">branch:</span>{ "firstName": "Leo" }   <span class="p">breaking</span><span class="c">: clients reading "name" get nothing</span>'
        ),
    },
    'diagram.domain': {
        "li": [
            'The JPA entities and their links, generated from the Java classes.',
            'The badge says whether this PR changed it.',
        ],
        "ex": 'e.g. <code>Owner 1─* Pet 1─* Visit</code>: an owner has pets, a pet has visits.',
    },
    'diagram.db': {
        "li": [
            'The database tables, rebuilt from the migration scripts.',
            '"Also changed, not drawn": indexes and constraints the picture can\'t show.',
        ],
        "ex": 'e.g. <code>pets.owner_id «FK» → owners.id</code>: each pet row points at its owner.',
    },
    'diagram.drawio': {
        "li": [
            'The business concepts and how they relate, hand-drawn in draw.io.',
            'No code here: the words a vet or a pet owner would use.',
        ],
        "ex": 'e.g. an Owner has Pets; a Vet has Specialties.',
    },
    'diagram.drawio:Deployment': {
        "li": [
            'What runs where at runtime, and who calls whom. Hand-drawn in draw.io.',
            "A test checks every traced arrow really appears in the tests' traces.",
        ],
        "ex": 'e.g. Backend → Notification Service: booking a visit sends an SMS.',
    },
    'diagram.packages': {
        "li": [
            'How the backend code is split into Java packages. Arrow = "depends on".',
            'ArchUnit tests fail the build if the code stops matching the drawing.',
        ],
        "ex": "e.g. a new import from <code>..domain</code> into <code>..rest</code> isn't drawn, so a test fails.",
    },
    'diagram.modules': {
        "li": [
            'The Maven modules and which one depends on which.',
            "Generated from <code>mvn dependency:tree</code>, so it can't drift from the build.",
        ],
        "ex": 'e.g. <code>petclinic-backend → petclinic-commons</code>: shared code lives in commons.',
    },
    'diagram.c2': {
        "li": [
            'The C4 "containers" view: the apps and databases, and the calls between them.',
            "Drawn from the tests' traces, not by hand: every arrow was really called.",
        ],
        "ex": 'e.g. Browser → Backend: <code>GET /api/owners</code>.',
    },
    'diagram': {
        "li": [
            'A diagram kept in the repository as PlantUML.',
            'The badge says whether this PR changed it.',
        ],
    },
    'requirements': {
        "li": [
            "Left: the ticket's requirements. Right: the tests that check them.",
            'Requirement colour: <b>green</b> = a test proves it, <b>orange</b> = partly, <b>red</b> = no test.',
            '<b>E2E</b> = browser · <b>API</b> = HTTP call · <b>Unit</b> = direct call.',
        ],
    },
    'sequence': {
        "move": 'details.seqhow',
        "li": [
            'One diagram per test: each HTTP call and SQL query, in order.',
            'Watch for the same SELECT once per row: an N+1.',
        ],
        "code": (
            '<span class="c">e.g. what a bad one looks like:</span>\n'
            'GET /api/owners?page=0\n'
            '  → OwnerRestController.listOwners\n'
            '    → SELECT … FROM owners LIMIT 10\n'
            '    → SELECT … FROM pets WHERE owner_id=?   <span class="p">×10 ← N+1</span>'
        ),
    },
    'city': {
        "li": [
            'Code City: one building per class, grouped into districts by package.',
            'By default: area = lines of code · height = cognitive complexity · colour = test coverage.',
            'Tall and thin = small but tangled. Changed classes are highlighted.',
        ],
    },
    'dsaudit': {
        "li": [
            'Every screen, opened on main and on this branch with the same data, side by side.',
            "<b>Changed</b>: an element added, removed or restyled. Moving alone doesn't count.",
            '<b>+1 gap</b>: one more control built outside the design system.',
        ],
        "ex": 'e.g. a raw <code>&lt;select&gt;</code> where the design system has its own dropdown.',
    },
    'complexity': {
        "move": 'p.cx-lede',
        "li": [
            '<b>Cognitive complexity</b>: how hard code is to follow. Nesting is what costs.',
            'One row per endpoint: its whole call chain, summed. Green = added by this PR.',
        ],
        "code": (
            'for (Owner o : owners) {            <span class="p">// +1</span>  <span class="c">loop</span>\n'
            '  if (o.getPets().isEmpty()) {      <span class="p">// +2</span>  <span class="c">if, nested once</span>\n'
            '    for (Visit v : visits) {        <span class="p">// +3</span>  <span class="c">loop, nested twice</span>\n'
            '      if (v.getVet() == null) {}    <span class="p">// +4</span>  <span class="c">if, 3 deep → total 10</span>'
        ),
    },
    'logging': {
        "move": 'p.tabsub',
        "li": [
            'Every log statement this PR adds or changes.',
            'Check: right level? No secrets or personal data? Enough context to debug?',
        ],
        "code": (
            '<span class="c">e.g. ✗</span> log.info("Saved {}", owner);  <span class="p">// prints the owner\'s phone and address</span>'
        ),
    },
    'owners': {
        "li": [
            'Files this PR touches that <code>.github/CODEOWNERS</code> assigns to a team.',
            "That team's review is requested; branch protection can make it required.",
        ],
        "code": (
            'openapi.yaml   @org/tech-leads   <span class="c">← API changes need a tech lead</span>'
        ),
    },
    'cost': {
        "li": [
            'AI spend on this PR: writing, reviewing, fixing, and building this page.',
            '$ = Claude tokens at API list price, not what a subscription bills.',
            'Time = model thinking + tools running (builds, tests, Docker).',
        ],
    },
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
#: The rule (5 Oct 2026, Victor): a prompt about ONE card sits inside that card, in its
#: bottom-right; a tab that holds one piece of knowledge, one generation, has its prompt
#: on the right of that tab's title. So: `in` — a row at the end of that card, inside its
#: border; `title` — the anchor is the tab's first row (its `h2.tabtitle`, or whatever row
#: opens a tab that has none: the API verdict band, the UX audit's count line, the Tests
#: key over the card), and it becomes a flex row with that row on the left and the pill on
#: the right (a row too long to share its line wraps its own text beside the pill); `col` — under it
#: in a column of its own (the Demo's transcript, beside the player); `upto` — a row
#: closing the region that starts at the anchor and runs to the next Round kicker (the
#: Review tab's three piles). Piece None is a diagram card, whose piece is read off its
#: head. A tab whose anchor is missing gets one row at the end of the panel, so a renamed
#: class costs placement, never the button.
DIAGRAM_CARD = r'<div class="diagram(?![^"]*\bdgm-bare\b)[^"]*"'
PLACES: dict[str, tuple[tuple[str | None, str, str | None, str | None], ...]] = {
    "review": (("review.assumed", "upto", r'<h2 id="assumed"', "first"),
               ("review.open", "upto", r'<h2 id="first"', "first"),
               ("review.fixed", "upto", r'<h2 id="fixed"', "first")),
    "behaviour": (("behaviour", "col", r'<ol class="transcript"', "first"),),
    "api": (("api", "title", r'<div class="apiverdict\b', "first"),),
    "data": ((None, "in", DIAGRAM_CARD, "all"),),
    "packages": ((None, "in", DIAGRAM_CARD, "all"),),
    "requirements": (("requirements", "title", r'<p class="rm-cats"', "first"),),
    "sequence": (("sequence", "title", r'<h2 class="tabtitle\b', "first"),),
    "city": (("city", "title", r'<h2 class="tabtitle\b', "first"),),
    "dsaudit": (("dsaudit", "title", r'<h2 class="tabtitle\b', "first"),),
    "complexity": (("complexity", "title", r'<h2 class="tabtitle\b', "first"),),
    "logging": (("logging", "title", r'<h2 class="tabtitle\b', "first"),),
    "owners": (("owners", "title", r'<h2 class="tabtitle\b', "first"),),
    "cost": (("cost", "title", r'<h2 class="tabtitle\b', "first"),),
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


#: The one-line captions a diagram card can end on: its legend, or a producer's note.
_CAPTION = re.compile(r'<p class="(?:cmlegend|sub dgm-(?:stale|unseen))\b[^"]*"')


def _last_caption(doc: str, start: int, end: int) -> int | None:
    """Where the caption that closes the card [start, end) opens, if it ends on one:
    the pill then sits at the right end of that line (Victor, 6 Oct 2026) instead of on
    a row of its own under it."""
    last = None
    for m in _CAPTION.finditer(doc, start, end):
        last = m
    if not last:
        return None
    span = _close(doc, last.start())
    return last.start() if span and not doc[span[1]:end].strip() else None


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


def adopt_html(piece: str, title: str = "", how: str = "in", page: bool = False) -> str:
    prompt = adopt_prompt(piece, title)
    if not prompt:
        return ""
    # A pill on the tab's title row (`page`) is about the whole tab; every other placement,
    # a diagram card's included, is about a smaller area of a screen and keeps the short label.
    label = "Prompt to get this page" if page else "Prompt to get this"
    return (f'<div class="adoptline adopt-{how}"><button type="button" class="adopt copycmd" '
            f'data-piece="{html.escape(piece)}" data-copy="{html.escape(prompt, quote=True)}" '
            'data-say="Copied — paste it to your coding agent" '
            'data-tip="Copy a prompt for your coding agent to get this into your project">'
            f'{ROBOT} {label}</button>{explain_button(piece, title)}</div>')


def explain_key(piece: str, title: str = "") -> str | None:
    """The `EXPLAIN` entry for a piece's card, or None when there is none."""
    for key in (f"{piece}:{title}", piece):
        if key in EXPLAIN:
            return key
    return None


def explain_button(piece: str, title: str = "") -> str:
    """The blue (i) right after the pill. `explain.js` opens its box on click."""
    key = explain_key(piece, title)
    if not key:
        return ""
    return (f'<button type="button" class="hrx-i" aria-pressed="false" '
            f'data-explain="{html.escape(key, quote=True)}" aria-label="What am I looking at?" '
            'data-tip="What am I looking at?"></button>')


def explain_data() -> str:
    """`EXPLAIN` as the JSON block `explain.js` reads; `</` escaped so no text can close it."""
    return ('<script type="application/json" id="hr-explain">'
            + json.dumps(EXPLAIN, ensure_ascii=False).replace("</", "<\\/") + "</script>")


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
                cap = _last_caption(body, hit.start(), span[0])
                if cap:             # the card ends on a caption line: the pill shares it
                    edits.append((cap, cap, '<div class="adoptfoot">'))
                    edits.append((span[0], span[0],
                                  adopt_html(name, title, "title") + "</div>"))
                else:
                    edits.append((span[0], span[0], adopt_html(name, title, "in")))
            elif how == "title":
                edits.append((hit.start(), hit.start(), '<div class="adopthead">'))
                edits.append((span[1], span[1], adopt_html(
                    name, title, "title", page=piece is not None) + "</div>"))
            elif how == "col":
                edits.append((hit.start(), hit.start(), '<div class="adoptcol">'))
                edits.append((span[1], span[1], adopt_html(name, title, "after") + "</div>"))
            else:
                edits.append((span[1], span[1], adopt_html(name, title, how)))
    if not edits:
        # The anchor moved: the button loses its place, not its existence.
        first = next(p for p, *_ in places)
        return body + (adopt_html(first, how="end") if first else "")
    for at, to, text in sorted(edits, key=lambda e: e[0], reverse=True):
        body = body[:at] + text + body[to:]
    return body
