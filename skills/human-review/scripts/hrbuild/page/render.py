"""The redesigned review page — the default; `"page": {"layout": "old"}` in
`human-review.json` builds the old one instead.

The old page grew one tab per tool and one chip per number, and a reader had to learn it
before they could use it. This one answers four questions in the order a reviewer asks
them: what changed, does it do what was asked, what is left for me to decide, and what
was already fixed. Then the cost, and then the optional views (Sequence, API, Data …),
which keep the panels the old page built for them.

It is built from the data `build-review-html.py` has already prepared — the resolved
review points, the base, the cost ledger, the old panels — so nothing is measured twice
and the old page stays available while this one replaces it.
"""
from __future__ import annotations

import datetime
import html
import importlib
import json
import os
import re
import subprocess
from pathlib import Path

from hrbuild.shared.chips import (
    REVIEW_BOOKKEEPING, _compare_href, _project_cfg, generated_globs,
)
from hrbuild.shared.snippets import snippet_html
from hrbuild.tabs.review import push_pr_button, push_pr_dialog

#: The tab ids of the content file that this page draws itself; every other declared
#: tab becomes a view and keeps the panel the old page built for it.
NP_NATIVE = {"review", "behaviour", "requirements", "cost"}
#: Views nobody uses: not carried over, even when the content file declares them.
NP_DROPPED = {"city"}
NP_VIEW_LABELS = {"sequence": "Sequence", "api": "API", "data": "Data",
                  "packages": "Structure", "structure": "Structure", "ux": "UX",
                  "complexity": "Complexity", "logging": "Logging", "owners": "Owners"}
#: Coverage words of the test mapping, as the page says them.
NP_COVERAGE = {"covered": ("full", "Tested"), "partial": ("part", "Partly tested"),
               "executed": ("part", "Runs, not checked"), "missing": ("miss", "Not tested"),
               "n/a": ("na", "Not for this ticket")}
NP_MAPPING_FILES = ("assets/test-mapping.merged.json", "test-mapping.json")


def page_layout(root: Path) -> str:
    """`new` or `old`: the project's `human-review.json`, else `$HUMAN_REVIEW_LAYOUT`,
    else `new` — the old page is built only when one of the two asks for it."""
    page = _project_cfg(root).get("page")
    named = page.get("layout") if isinstance(page, dict) else None
    return (named or os.environ.get("HUMAN_REVIEW_LAYOUT") or "new").strip().lower()


# --------------------------------------------------------------------------- helpers

def _np_esc(s) -> str:
    return html.escape(str(s or ""), quote=True)


def _np_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _np_git(root: Path, *args: str) -> str:
    try:
        out = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True,
                             timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return out.stdout if out.returncode == 0 else ""


#: Stroke icons, inline: the page is opened from disk and from a zip, offline as often as
#: not, so an icon font from the network is an icon that shows up as its own name.
NP_ICONS = {
    "check_circle": '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.5 2.5L16 9.5"/>',
    "error": '<circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.5M12 16.5v.5"/>',
    "warning": '<path d="M12 3.5L21.5 20h-19z"/><path d="M12 10v4.5M12 17.5v.5"/>',
    "history": '<path d="M3.5 12a8.5 8.5 0 1 0 2.5-6M3.5 4v4.5H8"/><path d="M12 8v4.5l3 2"/>',
    "done_all": '<path d="M3 13l4 4 8-9M12 16l1 1 8-9"/>',
    "merge": '<circle cx="6" cy="6" r="2"/><circle cx="6" cy="18" r="2"/>'
             '<circle cx="18" cy="18" r="2"/><path d="M6 8v8M18 16V9a3 3 0 0 0-3-3h-4M13 4l-2 2 2 2"/>',
    "task_alt": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="1.5"/>',
    "fork_right": '<circle cx="6" cy="5" r="2"/><circle cx="6" cy="19" r="2"/>'
                  '<circle cx="18" cy="7" r="2"/><path d="M6 7v10M18 9c0 5-12 3-12 8"/>',
    "commit": '<circle cx="12" cy="12" r="3.5"/><path d="M2.5 12h6M15.5 12h6"/>',
    "arrow_right_alt": '<path d="M4 12h15M14 7l5 5-5 5"/>',
    "expand_more": '<path d="M6 9l6 6 6-6"/>',
    "chevron_right": '<path d="M9 6l6 6-6 6"/>',
    "content_copy": '<rect x="8" y="8" width="12" height="12" rx="2"/>'
                    '<path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3"/>',
}


def _np_icon(name: str, cls: str = "") -> str:
    return (f'<svg class="ms{" " + cls if cls else ""}" viewBox="0 0 24 24" aria-hidden="true" '
            'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            f'stroke-linejoin="round">{NP_ICONS[name]}</svg>')


def _np_section(panel: str, title: str, lede: str, body: str, extra: str = "") -> str:
    head = (f'<div class="np-head"><div><h2 class="np-h2">{title}</h2>'
            + (f'<p class="np-lede">{lede}</p>' if lede else "")
            + f"</div>{extra}</div>")
    return (f'<section class="np-panel" id="np-{panel}" data-np-panel="{panel}" '
            f'role="tabpanel" aria-labelledby="np-tab-{panel}">{head}{body}</section>')


def _np_sections(doc: str, tid: str) -> str:
    """The old page's `<section class="panel" id=tid>`, whole — nested sections included."""
    m = re.search(rf'<section class="panel" id="{re.escape(tid)}"[^>]*>', doc)
    if not m:
        return ""
    depth, i = 1, m.end()
    for t in re.finditer(r"<section\b|</section>", doc[i:]):
        depth += 1 if t.group(0) == "<section" else -1
        if depth == 0:
            return doc[m.start():i + t.end()]
    return ""


# --------------------------------------------------------------------------- the frame

def _np_status(out_dir: Path, base_st: dict | None) -> str:
    badges = []
    gate = _np_json(out_dir / ".gate.json") or {}
    verdict = gate.get("verdict")
    if verdict:
        run = (gate.get("workflows") or [{}])[0]
        sha = str(gate.get("sha") or "")[:7]
        ok = verdict == "green"
        word = {"green": "CI green", "red": "CI failed"}.get(verdict, f"CI {verdict}")
        face = (_np_icon("check_circle" if ok else "error") + _np_esc(word)
                + (f" on {_np_esc(sha)}" if sha else ""))
        cls = "np-badge ok" if ok else "np-badge bad"
        badges.append(f'<a class="{cls}" href="{_np_esc(run.get("url"))}">{face}</a>'
                      if run.get("url") else f'<span class="{cls}">{face}</span>')
    ahead = (base_st or {}).get("ahead")
    if ahead:
        ref = str((base_st or {}).get("ref") or "the base").removeprefix("origin/")
        badges.append(f'<span class="np-badge warn">{_np_icon("warning")}Branch is {ahead} '
                      f'commit{"s" if ahead != 1 else ""} behind {_np_esc(ref)}</span>')
    after = _np_json(out_dir / "aftermath.json")
    if isinstance(after, dict):
        tot = after.get("totals") or {}
        n = tot.get("commits") or 0
        if n:
            code = (tot.get("code") or {})
            lines = (code.get("added") or 0) + (code.get("deleted") or 0)
            badges.append(f'<span class="np-badge warn">{_np_icon("history")}{n} '
                          f'commit{"s" if n != 1 else ""} after the review'
                          + (f", {lines} lines of code" if lines else "") + "</span>")
        else:
            badges.append(f'<span class="np-badge">{_np_icon("done_all")}'
                          "No commits after the review</span>")
    return f'<div class="np-status">{"".join(badges)}</div>' if badges else ""


def _np_title(spec: dict) -> str:
    pr = spec.get("pr") or {}
    title = pr.get("title") or spec.get("title") or "Review"
    return re.sub(r"^#\d+:\s*", "", str(title))


def _np_meta(spec: dict, root: Path, base_st: dict | None, ticket: dict | None) -> str:
    pr = spec.get("pr") or {}
    bits = []
    if pr.get("number"):
        bits.append(f'<a class="np-plain" href="{_np_esc(pr.get("url"))}">'
                    f'{_np_icon("merge")}PR #{_np_esc(pr["number"])}</a>')
    if ticket and ticket.get("number"):
        bits.append(f'<a class="np-plain" href="{_np_esc(ticket.get("url"))}">'
                    f'{_np_icon("task_alt")}Issue #{_np_esc(ticket["number"])}</a>')
    if pr.get("branch"):
        base = str(pr.get("base") or "").removeprefix("origin/")
        bits.append(f'<span class="np-branch">{_np_icon("fork_right")}'
                    f'<code>{_np_esc(pr["branch"])}</code>'
                    + (f'<span aria-hidden="true">→</span><code>{_np_esc(base)}</code>'
                       if base else "") + "</span>")
    start = (base_st or {}).get("diffBase") or (base_st or {}).get("mergeBase")
    count = _np_git(root, "rev-list", "--count", f"{start}..HEAD").strip() if start else ""
    if count.isdigit():
        bits.append(f'<span>{_np_icon("commit")}{count} commit{"s" if count != "1" else ""}'
                    "</span>")
    sep = '<span class="np-dot" aria-hidden="true">·</span>'
    return f'<div class="np-meta">{sep.join(bits)}</div>'


def _np_topbar(spec: dict, mode_html: str) -> str:
    pr = spec.get("pr") or {}
    repo = str(pr.get("repo") or "").rstrip("/").rsplit("/", 1)[-1]
    open_pr = (f'<a class="np-btn np-primary" href="{_np_esc(pr.get("url"))}">Open PR '
               f'#{_np_esc(pr.get("number"))}{_np_icon("arrow_right_alt")}</a>'
               if pr.get("url") and pr.get("number") else "")
    actions = (f'<details class="np-actions"><summary class="np-btn">Actions '
               f'{_np_icon("expand_more")}</summary>'
               f'<div class="np-menu np-actionsmenu">{mode_html}</div></details>'
               if mode_html else "")
    return ('<header class="np-top"><div class="np-brand"><b>human-review</b>'
            + (f"<span>{_np_esc(repo)}</span>" if repo else "") + "</div>"
            '<div class="np-topctl">'
            '<button type="button" class="np-btn chip-theme" id="hr-theme">Theme: Auto</button>'
            f"{actions}{open_pr}</div></header>")


def _np_tabbar(core: list[tuple[str, str, str]], views: list[tuple[str, str]]) -> str:
    def btn(tid, label, count, cls=""):
        return (f'<button type="button" role="tab" class="np-tab{cls}" id="np-tab-{tid}" '
                f'data-np-tab="{tid}" aria-controls="np-{tid}" aria-selected="false">'
                f"{label}{count}</button>")
    tabs = [btn(t, label, c) for t, label, c in core if t != "cost"]
    if views:
        tabs.append('<span class="np-sep" aria-hidden="true"></span>')
        tabs += [btn(t, _np_esc(label), "", " np-viewtab") for t, label in views]
        menu = "".join(f'<button type="button" role="menuitem" class="np-menuitem" '
                       f'data-np-go="{t}" data-np-menu-for="{t}">{_np_esc(label)}</button>'
                       for t, label in views)
        tabs.append('<div class="np-more"><button type="button" class="np-tab np-morebtn" '
                    'aria-haspopup="true" aria-expanded="false" hidden>'
                    f'<span class="np-morelabel">More</span>{_np_icon("expand_more")}</button>'
                    f'<div class="np-menu np-moremenu" role="menu" hidden>{menu}</div></div>')
    tabs.append('<span class="np-fill"></span>')
    tabs += [btn(t, label, c) for t, label, c in core if t == "cost"]
    return ('<nav class="np-tabbar"><div class="np-tabs" role="tablist" '
            f'aria-label="Review sections">{"".join(tabs)}</div></nav>')


# --------------------------------------------------------------------------- What changed

def _np_files(root: Path, spec: dict, base_st: dict | None) -> str:
    start = (base_st or {}).get("diffBase") or (base_st or {}).get("mergeBase")
    if not start:
        return ""
    rng = f"{start}...{(base_st or {}).get('head') or 'HEAD'}"
    skip = ([f":(exclude,glob){p}" for p in generated_globs(_project_cfg(root))]
            + [f":(exclude,glob){p}" for p in REVIEW_BOOKKEEPING])
    rows = []
    for line in _np_git(root, "diff", "--numstat", rng, "--", ".", *skip).splitlines():
        cols = line.split("\t")
        if len(cols) == 3:
            a, d = (int(x) if x.isdigit() else 0 for x in cols[:2])
            rows.append((cols[2], a, d))
    if not rows:
        return ""
    booked = sorted({ln for ln in _np_git(root, "diff", "--name-only", rng, "--",
                                         *[f":(glob){p}" for p in REVIEW_BOOKKEEPING]
                                         ).splitlines() if ln.strip()})
    top = max(a + d for _, a, d in rows) or 1
    adds, dels = sum(r[1] for r in rows), sum(r[2] for r in rows)
    body = "".join(
        f'<tr><td><code>{_np_esc(p)}</code></td><td class="np-num">'
        + (f'<span class="np-add">+{a}</span>' if a else "")
        + (f' <span class="np-del">−{d}</span>' if d else "")
        + f'</td><td class="np-barcell"><span class="np-bar"><span class="np-bar-a" '
        f'style="width:{round(100 * a / top)}%"></span><span class="np-bar-d" '
        f'style="width:{round(100 * d / top)}%"></span></span></td></tr>'
        for p, a, d in sorted(rows, key=lambda r: -(r[1] + r[2])))
    href = _compare_href(spec.get("pr"), (base_st or {}).get("diffBase"))
    return ('<div class="np-card np-files"><div class="np-cardhead">'
            f'<b>{len(rows)} file{"s" if len(rows) != 1 else ""} changed '
            f'<span class="np-add">+{adds}</span> <span class="np-del">−{dels}</span></b>'
            + (f'<a href="{_np_esc(href)}">Full diff on GitHub</a>' if href else "")
            + f'</div><div class="np-scroll"><table class="np-table">{body}</table></div>'
            + (f'<div class="np-cardfoot">Not counted: '
               + ", ".join(f"<code>{_np_esc(b)}</code>" for b in booked)
               + " (review records).</div>" if booked else "")
            + "</div>")


def _np_demo(out_dir: Path) -> str:
    video = out_dir / "assets" / "feature.webm"
    if not video.is_file():
        failed = _np_json(out_dir / "assets" / "feature.verdict.json")
        return ('<div class="np-card np-note warn">The demo recording failed. See '
                '<code>assets/feature.run.log</code>.</div>' if failed else "")
    cues = _np_json(out_dir / "assets" / "feature.cues.json") or []
    chapters = "".join(
        f'<li><button type="button" class="np-chapter" data-np-seek="{float(c["t"]):.2f}">'
        f'<span class="np-time">{int(c["t"]) // 60}:{int(c["t"]) % 60:02d}</span>'
        f'<span>{_np_esc(c.get("text"))}</span></button></li>'
        for c in cues if isinstance(c, dict) and "t" in c and c.get("text"))
    return ('<div class="np-demo"><div class="np-video"><video controls preload="metadata" '
            'src="assets/feature.webm"></video></div>'
            + (f'<div class="np-card np-chapters"><div class="np-label">In the demo</div>'
               f"<ol>{chapters}</ol></div>" if chapters else "")
            + "</div>")


def _np_next(cards: list[tuple[str, str, str, str, str]]) -> str:
    """`(tab, number, title, line, tone)` cards that open the tabs holding the rest."""
    if not cards:
        return ""
    out = "".join(
        f'<button type="button" class="np-nextcard {tone}" data-np-go="{tab}">'
        f'<span class="np-nexthead"><span class="np-num-sq">{_np_esc(n)}</span>'
        f"<b>{title}</b></span><span class=\"np-nextline\">{line}</span></button>"
        for tab, n, title, line, tone in cards)
    return f'<div class="np-next"><h3 class="np-h3">Next for you</h3><div class="np-nextgrid">{out}</div></div>'


# --------------------------------------------------------------------------- Asked vs tested

def _np_semcov():
    try:
        return importlib.import_module("semcov")
    except Exception:  # noqa: BLE001 — a page without the map is still a page
        return None


def _np_test_names(out_dir: Path, spec: dict) -> tuple[dict, list[dict]]:
    doc = _np_json(out_dir / (spec.get("testChanges") or "assets/test-changes.json")) or {}
    tests = [t for t in doc.get("tests") or [] if isinstance(t, dict)]
    names = {f'{t.get("path")}:{t.get("line")}': t.get("name") for t in tests}
    return names, tests


def _np_provenance(out_dir: Path, mapping: dict) -> str:
    """Which paid run paired the ticket with the tests, and whether an earlier answer is
    kept. Two runs over one branch can disagree (once, the second found no test for a
    criterion the first had two for), so the page says which answer it shows. The stamp is
    `rerun-model.py`'s `pairedBy`; a map older than the stamp is matched to the run in
    `.model-runs.json` that ended within two minutes of the file's own time."""
    runs = [r for r in (_np_json(out_dir / ".model-runs.json") or {}).get("runs") or []
            if isinstance(r, dict) and r.get("when")]
    stamp = mapping.get("pairedBy") if isinstance(mapping.get("pairedBy"), dict) else None
    when = (stamp or {}).get("at")
    model = (stamp or {}).get("model")
    index = None
    def at(s):
        return datetime.datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()
    try:
        target = at(when) if when else (out_dir / "test-mapping.json").stat().st_mtime
        near = min(range(len(runs)), key=lambda i: abs(at(runs[i]["when"]) - target),
                   default=None)
        if near is not None and abs(at(runs[near]["when"]) - target) <= 120:
            index = near
            when = when or runs[near]["when"]
            model = model or runs[near].get("model")
    except (OSError, ValueError):
        pass
    if not (model or when):
        return ""
    stamp_txt = (f"Paired by {_np_esc(model or 'a model')}"
                 + (f", {_np_esc(str(when)[:16].replace('T', ' '))} UTC" if when else "")
                 + (f" — run {index + 1} of {len(runs)}" if index is not None and len(runs) > 1
                    else ""))
    prev = (out_dir / ".model-prev" / "test-mapping.json").is_file()
    return (f'<p class="np-provenance">{stamp_txt}.'
            + (" Another answer is kept in <code>.model-prev/test-mapping.json</code>."
               if prev else "") + "</p>")


def _np_asked(out_dir: Path, spec: dict) -> tuple[str, int, int]:
    """The ticket beside its tests; and how many criteria are untested, and how many."""
    semcov = _np_semcov()
    ticket = _np_json(out_dir / "ticket-body.json") or {}
    mapping = next((m for m in (_np_json(out_dir / f) for f in NP_MAPPING_FILES) if m), {})
    if not (semcov and ticket.get("body")):
        return "", 0, 0
    blocks = semcov.parse_ticket(ticket["body"])
    cov = {s["id"]: s for s in mapping.get("sentences") or [] if isinstance(s, dict)}
    names, changed = _np_test_names(out_dir, spec)

    def kind(sid):
        return NP_COVERAGE.get((cov.get(sid) or {}).get("coverage"), ("unk", "Not paired"))

    def sentence(s):
        k, label = kind(s["id"])
        return (f'<button type="button" class="np-sent cov-{k}" data-np-sent="{s["id"]}" '
                f'aria-pressed="false" title="{_np_esc(label)}">'
                f'{semcov._inline(s["md"])}</button>')

    left, criteria = [], []
    for b in blocks:
        if b["kind"] == "h":
            left.append(f'<div class="np-label">{_np_esc(semcov._plain(b["text"]))}</div>')
        elif b["kind"] in ("p", "quote"):
            left.append("<p>" + " ".join(sentence(s) for s in b["sentences"]) + "</p>")
        elif b["kind"] in ("ol", "ul"):
            items = "".join("<li>" + " ".join(sentence(s) for s in it["sentences"]) + "</li>"
                            for it in b["items"])
            left.append(f'<{b["kind"]}>{items}</{b["kind"]}>')
            for it in b["items"]:
                criteria += [s for s in it["sentences"]
                             if "acceptance" in (s.get("section") or "").lower()]
        elif b["kind"] == "code":
            left.append(f'<pre class="np-code">{_np_esc(b["text"])}</pre>')
    every = semcov.ticket_sentences(blocks)
    criteria = criteria or every
    untested = sum(1 for s in criteria if kind(s["id"])[0] == "miss")

    groups, rejected = [], []
    for s in every:
        row = cov.get(s["id"]) or {}
        k, label = kind(s["id"])
        rejected += [(r, s) for r in row.get("review") or [] if r.get("verdict") == "reject"]
        if k == "na":
            continue
        tests = "".join(
            f'<details class="np-test"><summary>{_np_icon("chevron_right", "chev")}'
            f'<span class="np-kind">UNIT</span>'
            f'<span class="np-testname">{_np_esc(names.get(t["id"]) or t["id"])}</span>'
            f'<code class="np-ref">{_np_esc(t["id"].rsplit("/", 1)[-1])}</code></summary>'
            f'<div class="np-testbody"><span>{_np_esc(t.get("why"))}</span>'
            + (f'<pre class="np-code">{_np_esc(t["line"])}</pre>' if t.get("line") else "")
            + "</div></details>"
            for t in row.get("tests") or [] if isinstance(t, dict) and t.get("id"))
        gap = row.get("gap")
        groups.append(
            f'<div class="np-group" data-np-group="{s["id"]}"><div class="np-grouphead">'
            f'<span class="np-pill cov-{k}">{_np_esc(label)}</span>'
            f'<span>{_np_esc(s["text"])}</span></div>{tests}'
            + (f'<div class="np-gap"><b>Gap:</b> {_np_esc(gap)}</div>' if gap else "")
            + "</div>")
    rej = "".join(
        f'<li><code>{_np_esc(r["id"].rsplit("/", 1)[-1])}</code> '
        f'{_np_esc(names.get(r["id"]) or "")}<br><span class="np-muted">'
        f'{_np_esc(r.get("why"))}</span></li>' for r, _ in rejected)
    legend = "".join(f'<span class="np-pill cov-{k}">{label}</span>'
                     for k, label in (("full", "Tested"), ("part", "Partly tested"),
                                      ("miss", "Not tested"), ("na", "Not for this ticket")))
    num = ticket.get("number")
    ticket_head = (f'<div class="np-cardhead"><span><a href="{_np_esc(ticket.get("url"))}">'
                   f'Issue #{_np_esc(num)}</a></span><span class="np-muted np-selhint">'
                   "Click a sentence to see its tests</span></div>")
    body = ('<div class="np-two">'
            f'<div class="np-card np-ticket">{ticket_head}<div class="np-ticketbody">'
            f'{"".join(left)}</div></div>'
            '<div class="np-card np-groups"><div class="np-cardhead"><b>Tests per sentence'
            f'</b></div>{"".join(groups)}'
            + (f'<details class="np-rejected"><summary>{_np_icon("chevron_right", "chev")}'
               f"Matched on words, rejected by AI <b>{len(rejected)}</b></summary>"
               f"<ul>{rej}</ul></details>" if rejected else "")
            + "</div></div>")
    plain = _np_json(out_dir / "test-mapping.json") or {}
    body = _np_provenance(out_dir, plain) + body + _np_changed_tests(changed) + _np_score(spec)
    return (_np_section("asked", "Asked vs tested",
                        "The ticket, and the tests that check each sentence of it.", body,
                        f'<div class="np-legend">{legend}</div>'), untested, len(criteria))


def _np_changed_tests(tests: list[dict]) -> str:
    rows = [t for t in tests if t.get("status") in ("added", "modified", "deleted")]
    if not rows:
        return ""
    word = {"added": "new", "modified": "changed", "deleted": "removed"}
    out = "".join(
        f'<li><span class="np-status-{t["status"]}">{word[t["status"]]}</span>'
        f'<span>{_np_esc(t.get("name"))}'
        + ("".join(f' <span class="np-muted">· via helper <code>{_np_esc(h.get("name"))}'
                   "</code></span>" for h in t.get("viaHelper") or []))
        + f'</span><code class="np-ref">:{_np_esc(t.get("line"))}</code></li>'
        for t in rows)
    n = {k: sum(1 for t in rows if t["status"] == k) for k in word}
    return ('<div class="np-card"><div class="np-cardhead"><b>Tests this branch added or '
            f'changed</b><span class="np-muted">{n["added"]} new · {n["modified"]} changed · '
            f'{n["deleted"]} removed</span></div><ul class="np-list">{out}</ul></div>')


def _np_score(spec: dict) -> str:
    v = spec.get("verdict") or {}
    if v.get("score") is None:
        return ""
    bullets = "".join(f"<li>{b}</li>" for b in (v.get("bullets") or [])[:2])
    return (f'<div class="np-card np-scorecard"><div class="np-score"><b>{_np_esc(v["score"])}'
            '</b><span>of 10</span></div><div><div class="np-label">Test score</div>'
            + (f'<ul class="np-plainlist">{bullets}</ul>' if bullets else "") + "</div></div>")


# --------------------------------------------------------------------------- decisions, fixes

def _np_refs(item: dict, root: Path) -> str:
    snippets = [s for s in item.get("snippets") or [] if isinstance(s, dict) and s.get("ref")]
    if snippets:
        return "".join(snippet_html(s["ref"], s.get("caption"), root) for s in snippets)
    refs = item.get("refs") or []
    return ('<div class="np-refs">' + " · ".join(f"<code>{_np_esc(r)}</code>" for r in refs)
            + "</div>") if refs else ""


def _np_confidence(c) -> str:
    try:
        pct = round(float(c) * 100)
    except (TypeError, ValueError):
        return ""
    tone = "low" if pct < 70 else "mid"
    return (f'<span class="np-conf"><span class="np-confbar"><span class="{tone}" '
            f'style="width:{pct}%"></span></span>{pct}% sure</span>')


def _np_unrecorded(spec: dict) -> str:
    """The note for a branch with no `review-points.md`: its piles are empty because
    nothing was written down, which must not read as a review that found nothing."""
    points = spec.get("_reviewPoints") or {}
    if not points.get("missing"):
        return ""
    return (f'<p class="np-note warn">No review was recorded for this branch: no '
            f'<code>{_np_esc(points.get("path") or "review-points.md")}</code> says what was '
            "reviewed, fixed or declined. Run <code>/record-review</code> in the conversation "
            "that wrote the code, then build the page again.</p>")


def _np_decisions(spec: dict, root: Path) -> tuple[str, int]:
    assumed = sorted((a for a in spec.get("assumptions") or [] if isinstance(a, dict)),
                     key=lambda a: float(a.get("confidence") or 1))
    ignored = [f for f in spec.get("findings") or [] if isinstance(f, dict)]
    n = 0

    def card(item, first, body, tail):
        nonlocal n
        n += 1
        return (f'<details class="np-item"{" open" if first else ""}><summary>'
                f'<span class="np-num-sq">{n}</span><span class="np-itemtitle">'
                f'{item.get("title") or ""}</span>{tail}{_np_icon("chevron_right", "chev")}'
                f'</summary><div class="np-itembody">{body}{_np_refs(item, root)}</div></details>')
    a_html = "".join(card(
        a, i == 0,
        (f'<p><b>Other option:</b> {a.get("alternative")}</p>' if a.get("alternative") else "")
        + (f'<p class="np-why">{a.get("why")}</p>' if a.get("why") else ""),
        _np_confidence(a.get("confidence"))) for i, a in enumerate(assumed))
    f_html = "".join(card(
        f, False,
        (f'<p>{f.get("observation") or f.get("body") or ""}</p>')
        + (f'<p class="np-why"><b>Not fixed because:</b> {f.get("why")}</p>'
           if f.get("why") else ""),
        f'<span class="np-sev">{_np_esc(f.get("severity"))}</span>' if f.get("severity")
        else "") for f in ignored)
    total = len(assumed) + len(ignored)
    if _np_unrecorded(spec):
        body = _np_unrecorded(spec)
    elif not total:
        body = '<p class="np-empty">Nothing is waiting for you.</p>'
    else:
        body = ((f'<h3 class="np-h3">Choices where the ticket was not clear '
                 f'<span class="np-muted">{len(assumed)} · least sure first</span></h3>'
                 f'<div class="np-items">{a_html}</div>' if assumed else "")
                + (f'<h3 class="np-h3">Review points the agent did not fix '
                   f'<span class="np-muted">{len(ignored)}</span></h3>'
                   f'<div class="np-items">{f_html}</div>' if ignored else ""))
    # Hidden until the served page's probe says it can post (review.py's PR_PUSH_JS).
    publish = push_pr_button(spec)
    return (_np_section("decide", f'Your decisions <span class="np-muted">{total}</span>',
                        "The agent could not settle these alone. Agree, or ask for a change "
                        "on the PR.", body + push_pr_dialog(spec),
                        f'<div class="np-publish">{publish}</div>' if publish else ""), total)


def _np_fixed(spec: dict, root: Path) -> tuple[str, int]:
    fixes = [f for f in spec.get("autofixes") or [] if isinstance(f, dict)]
    points = spec.get("_reviewPoints") or {}
    items = "".join(
        f'<details class="np-item"><summary><span class="np-itemtitle">{f.get("title") or ""}'
        "</span>"
        + (f'<span class="np-sev">{_np_esc(f.get("severity"))}</span>'
           if f.get("severity") else "")
        + f'{_np_icon("chevron_right", "chev")}</summary><div class="np-itembody">'
        + (f'<p>{f.get("observation") or f.get("body") or ""}</p>')
        + (f'<p><b>Fix:</b> {f.get("fix")}</p>' if f.get("fix") else "")
        + (f.get("_fixDiffs") or _np_refs(f, root))
        + "</div></details>" for f in fixes)
    other = points.get("fixOther")
    if other:
        items += (f'<details class="np-item warn"><summary>{_np_icon("warning")}'
                  '<span class="np-itemtitle">Other changes in the fix commits</span>'
                  f'{_np_icon("chevron_right", "chev")}</summary>'
                  f'<div class="np-itembody">{other}</div></details>')
    warn = "".join(f'<p class="np-note warn">{w}</p>' for w in points.get("fixWarnings") or [])
    body = (_np_unrecorded(spec) or (f'<div class="np-items">{items}</div>{warn}'
                                     if fixes or other
                                     else '<p class="np-empty">The review fixed nothing.</p>'))
    return (_np_section("fixed", f'Fixed in review <span class="np-muted">{len(fixes)}</span>',
                        "The review found these, and the agent fixed them. You need to do "
                        "nothing here.", body), len(fixes))


# --------------------------------------------------------------------------- cost, footer

def _np_minutes(secs) -> str:
    if not secs:
        return ""
    secs = float(secs)
    return f"{round(secs)} s" if secs < 60 else f"{round(secs / 60)} min"


def _np_cost(ledger: dict | None) -> tuple[str, str]:
    comp = (ledger or {}).get("components") or {}
    rows = [r for r in comp.get("rows") or [] if isinstance(r, dict)]
    if not rows:
        return _np_section("cost", "Cost", "", '<p class="np-empty">The cost was not '
                           "measured for this build.</p>"), ""
    top = max((r.get("usd") or 0) for r in rows) or 1
    body = ""
    for r in rows:
        models = sorted({m for e in r.get("entries") or [] for m in (e.get("models") or {})})
        usd = r.get("usd")
        body += (f'<tr><td>{_np_esc(str(r.get("label") or r.get("key")).capitalize())}</td>'
                 f'<td class="np-muted">{_np_esc(", ".join(models))}</td>'
                 f'<td class="np-num">{_np_minutes(r.get("busySeconds") or r.get("modelSeconds"))}</td>'
                 f'<td class="np-num">{"$%.2f" % usd if usd is not None else "—"}</td>'
                 f'<td class="np-barcell"><span class="np-bar"><span class="np-bar-c" '
                 f'style="width:{round(100 * (usd or 0) / top)}%"></span></span></td></tr>')
    total = comp.get("usd") or 0
    busy = _np_minutes(comp.get("busySeconds"))
    body += (f'<tr class="np-total"><td>Total</td><td></td><td class="np-num">{busy}</td>'
             f'<td class="np-num">${total:.2f}</td><td></td></tr>')
    tabs = ((ledger or {}).get("tabs") or {}).get("tabs") or {}
    per = "".join(f'<li><span>{_np_esc(NP_VIEW_LABELS.get(t, t).capitalize())}</span>'
                  f'<span class="np-num">${(v.get("cost") or 0):.2f}</span></li>'
                  for t, v in tabs.items() if v.get("measured") and (v.get("cost") or 0) > 0)
    resid = ((ledger or {}).get("tabs") or {}).get("residual") or {}
    if resid.get("measured") and resid.get("cost"):
        per += (f'<li><span>The page run itself</span><span class="np-num">'
                f'${resid["cost"]:.2f}</span></li>')
    side = (f'<div class="np-card"><div class="np-cardhead"><b>This page, per part</b></div>'
            f'<ul class="np-list np-costlist">{per}</ul></div>' if per else "")
    html_ = _np_section(
        "cost", f'Cost <span class="np-muted">${total:.2f}{" · " + busy if busy else ""}</span>',
        "Model tokens to write, review and fix the change, and to build this page.",
        f'<div class="np-two"><div class="np-card np-scroll"><table class="np-table np-costtable">'
        "<thead><tr><th>Step</th><th>Model</th><th class=\"np-num\">Time</th>"
        f'<th class="np-num">Cost</th><th></th></tr></thead>{body}</table></div>{side}</div>')
    return html_, f"${total:.2f}"


def _np_footer(root: Path, base_st: dict | None, out_dir: Path, out_path: Path,
               spec: dict) -> str:
    start = (base_st or {}).get("diffBase") or (base_st or {}).get("mergeBase")
    log = _np_git(root, "log", "--format=%h%x09%s", f"{start}..HEAD") if start else ""
    commits = "".join(f"<li><code>{_np_esc(h)}</code> {_np_esc(s)}</li>"
                      for h, _, s in (ln.partition("\t") for ln in log.splitlines()))
    warns = "".join(f'<li class="np-warn">{_np_esc(w)}</li>'
                    for w in (_np_json(out_dir / "review-commits.json") or {}).get("warnings")
                    or [])
    pr = spec.get("pr") or {}
    rebuild = f"/human-review {pr['number']}" if pr.get("number") else "/human-review"
    return ('<footer class="np-foot"><details><summary>'
            f'{_np_icon("chevron_right", "chev")}Commits and build details</summary>'
            f'<ul class="np-plainlist">{commits}{warns}'
            f"<li>Rebuild in Claude Code: <code>{_np_esc(rebuild)}</code></li></ul></details>"
            '<div class="np-footrow"><span>Built by <a href="https://github.com/victorrentea/'
            'human-review">human-review</a></span>'
            f'<code class="np-path">{_np_esc(out_path)}</code>'
            '<button type="button" class="np-btn np-small copycmd" data-say="Copied the path '
            f'of this page" data-copy="{_np_esc(out_path)}">{_np_icon("content_copy")}Copy '
            "path</button></div></footer>")


# --------------------------------------------------------------------------- the page

def new_page_html(*, spec: dict, root: Path, out_dir: Path, out_path: Path,
                  base_st: dict | None, ledger: dict | None, old_doc: str,
                  emitted: list[dict], mode_html: str, rerun_html: str,
                  head: str, scripts: str) -> str:
    """The whole document. `head` is the old page's `<head>` contents (styles, the theme
    and paint scripts), `scripts` the old scripts the views and the actions need."""
    ticket = _np_json(out_dir / "ticket-body.json") or {}
    asked, untested, n_criteria = _np_asked(out_dir, spec)
    decide, n_decide = _np_decisions(spec, root)
    fixed, n_fixed = _np_fixed(spec, root)
    cost, cost_label = _np_cost(ledger)

    cards = []
    if n_decide:
        cards.append(("decide", n_decide, "Decisions wait for you",
                      "Choices where the ticket was not clear, and review points not fixed.",
                      "act"))
    if untested:
        cards.append(("asked", untested, f'Criteri{"on" if untested == 1 else "a"} not tested',
                      f"Of {n_criteria} acceptance criteria. Check {'it' if untested == 1 else 'them'} by hand.",
                      "miss"))
    if n_fixed:
        cards.append(("fixed", n_fixed, "Fixed in review",
                      "No action needed. Read them to check the fixes.", "full"))
    summary = spec.get("summary") or ""
    changed = _np_section(
        "changed", "What changed", "",
        (f'<div class="np-summary">{summary}</div>' if summary else "")
        + _np_demo(out_dir) + _np_files(root, spec, base_st) + _np_next(cards))

    views = []
    view_panels = ""
    for tab in emitted:
        tid = tab.get("id")
        if tid in NP_NATIVE or tid in NP_DROPPED:
            continue
        panel = _np_sections(old_doc, tid)
        if not panel:
            continue
        label = NP_VIEW_LABELS.get(tid) or tab.get("label") or tid
        views.append((tid, label))
        view_panels += (f'<section class="np-panel np-view" id="np-{tid}" data-np-panel="{tid}" '
                        f'role="tabpanel" aria-labelledby="np-tab-{tid}">{panel}</section>')

    def badge(n, cls):
        return f'<span class="np-count {cls}">{n}</span>' if n else ""
    core = [("changed", "What changed", ""),
            ("asked", "Asked vs tested", badge(untested, "miss")) if asked else None,
            ("decide", "Your decisions", badge(n_decide, "act")),
            ("fixed", "Fixed in review", badge(n_fixed, "quiet")),
            ("cost", "Cost", f'<span class="np-count quiet">{cost_label}</span>' if cost_label
             else "")]
    core = [c for c in core if c]

    band = ('<div class="np-band">' + _np_topbar(spec, mode_html)
            + '<div class="np-hero">' + _np_meta(spec, root, base_st, ticket)
            + f'<h1 class="np-h1">{_np_esc(_np_title(spec))}</h1>'
            + _np_status(out_dir, base_st) + "</div></div>")
    panels = changed + asked + decide + fixed + cost + view_panels
    return (f'<!doctype html>\n<html lang="en"><head>{head}</head>\n'
            f'<body class="np"><div class="np-root">{band}{_np_tabbar(core, views)}'
            f'{rerun_html}<main class="np-main">{panels}</main>'
            f"{_np_footer(root, base_st, out_dir, out_path, spec)}</div>\n{scripts}\n"
            "</body></html>\n")
