"""The "adopt this tab" button at the foot of every panel.

Every tab is its own module with its own producer, so a reader who likes one of them does
not want the whole skill — they want that one piece in their own repository. The footer
already says "Adopt what you like in your project"; this is the same offer made where the
reader is looking, one per tab, as a prompt they paste into their own coding agent.

Minimal on purpose (5 Oct 2026, Victor): the agent on the other end is a smart model with
the repository at hand. It needs to know which piece, where it starts, and that it should
take that piece and nothing else — not a tutorial on how the piece works.
"""
from __future__ import annotations

import html

from .commands import CMD_COPY
from .footer import HOME_URL

#: tab id → (what the tab shows, where it starts under `skills/human-review/`).
ADOPT: dict[str, tuple[str, str]] = {
    "review": ("the findings an AI review of the branch leaves for a human, each with the "
               "code it is about", "reference/review-prompt.md, scripts/review-points.py"),
    "behaviour": ("a narrated film of the feature working, recorded by a Playwright script",
                  "reference/film-prompt.md, scripts/record-feature-video.sh"),
    "api": ("the REST contract at the base against the branch, as a visual diff with a "
            "compatibility verdict", "scripts/openapi-visual-diff.py, scripts/openapi-compat.py"),
    "data": ("the domain model and the DB schema at the base against the branch, as "
             "diagram diffs", "scripts/puml-diff.sh, scripts/drawio-diff.py, "
             "scripts/schema_tree.py"),
    "requirements": ("each requirement of the change mapped to the tests that prove it, "
                     "with the changed lines no test runs",
                     "reference/matrix-prompt.md, scripts/rerun-model.py, scripts/testcov.py"),
    "sequence": ("sequence diagrams drawn from traced test runs, beside the test that "
                 "drew each one", "scripts/hrbuild/shared/genseq.py, scripts/puml-diff.sh"),
    "packages": ("the package and container diagrams, the containers projected from the "
                 "traced sequences", "scripts/c2-from-sequence.py, scripts/puml-diff.sh"),
    "city": ("a 3D Code City of the classes, coloured by what the branch changed",
             "scripts/regenerate-codecity.sh, https://github.com/victorrentea/code-city"),
    "dsaudit": ("the UI screens at the base against the branch, audited against the design "
                "system", "scripts/ds-audit.py"),
    "complexity": ("the complexity of every endpoint the branch touched, before and after",
                   "scripts/endpoint-complexity-delta.py"),
    "logging": ("what the branch logs, and whether any of it is a privacy problem",
                "scripts/logextract.py"),
    "owners": ("whether CODEOWNERS still covers every file the branch touched",
               "scripts/codeowners-check.py"),
    "cost": ("what writing and reviewing the change cost in model tokens",
             "scripts/review-cost.py, scripts/harness_cost.py"),
}


def adopt_prompt(tid: str, label: str) -> str | None:
    """The prompt the button copies, or None for a tab with nothing to adopt."""
    if tid not in ADOPT:
        return None
    what, start = ADOPT[tid]
    return (f"Adopt one piece of {HOME_URL} in this repository: the {label} tab of its "
            f"review page — {what}. Start from {start} under skills/human-review/. "
            "Take only that piece, adapt it to this project's stack, run it on the "
            "current branch against its merge-base and show me the result.")


def adopt_html(tid: str, label: str) -> str:
    prompt = adopt_prompt(tid, label)
    if not prompt:
        return ""
    return ('<div class="adoptline"><button type="button" class="adopt copycmd" '
            f'data-copy="{html.escape(prompt, quote=True)}" '
            'data-say="Copied — paste it to your coding agent" '
            'data-tip="Copy a prompt for your coding agent to bring this tab into your '
            f'project">{CMD_COPY} Adopt this tab</button></div>')
