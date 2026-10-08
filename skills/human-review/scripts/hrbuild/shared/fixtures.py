"""Which DB fixture each E2E test starts from, and the colour each fixture wears.

A fixture is a named set of demo rows the review environment restores *on top of* the
seed: a ``<name>.sql`` in a folder called ``fixtures`` (petclinic keeps them in
``petclinic-backend/src/main/resources/db/fixtures``, next to the seed they build on,
and its reset sidecar draws one Demo-tab button per file). The colours are the
project's to choose, in a ``fixture-colors.json`` beside those files::

    {"green": "#2fa84f"}

Beside the SQL and not in ``.human-review/``: whoever adds ``blue.sql`` is standing in
that folder, and the reset sidecar only ever reads ``*.sql`` from it, so the map rides
along harmlessly. A fixture the map does not name takes the next free colour of
``FIXTURE_PALETTE`` by its order in the folder, and the seed is always ``FIXTURE_SEED`` grey.

Per test the answer is read off the test's own code, never guessed from its name:

1. an explicit fixture — a ``@fixture:<name>`` tag (Cucumber, or Playwright's
   ``{tag: ...}``), or a call that loads one: ``__reset/<name>``,
   ``loadFixture('<name>')``, ``resetTo('<name>')``, ``fixture('<name>')``;
2. otherwise the seed, when the code the test runs leans on seeded rows by name —
   ``seed``/``seeded``/``SEEDED_…``/``R__seed`` outside comments (petclinic's
   owner-search Background asserts "the DB seeded by Flyway"; add-visit's DSL reads
   ``SEEDED_OWNER_WITH_PET``);
3. otherwise nothing: a test that makes its own rows works on any data, and a dot for it
   would be a guess.

"The code the test runs" is, for a Cucumber scenario, the feature's tags and the step
definitions its Background and its own steps match; for a Playwright test, its body, the
file's hooks and helpers, and the local modules it imports (DSLs, page objects) — not
``support/``, which every test imports and which says nothing about any one of them.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

FIXTURE_SEED = "#8b929c"
# Seven, readable on the dark and the light theme alike, and far enough apart in hue that
# two dots side by side never read as one colour.
FIXTURE_PALETTE = ("#2fa84f", "#3b82f6", "#e5a50a", "#d9485f", "#9b59d0", "#14a3a3", "#e8772e")
FIXTURE_COLORS_FILE = "fixture-colors.json"

_FX_NAME = re.compile(r"[a-z0-9][a-z0-9-]*")
_FX_COLOUR = re.compile(r"#[0-9a-fA-F]{3,8}|[a-zA-Z]{3,20}|(?:rgb|hsl)a?\([0-9\s.,%]+\)")
_FX_SEEDWORD = re.compile(r"(?<![A-Za-z])(?:R__)?seed(?:ed|s)?(?![A-Za-z])", re.I)
_FX_SPEC = re.compile(r"\.(?:spec|test|e2e)\.[cm]?[jt]sx?$")


def _fx_ls(root: Path) -> list[str]:
    r = subprocess.run(["git", "-C", str(root), "ls-files"], capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.strip():
        return r.stdout.splitlines()
    return [str(p.relative_to(root)) for p in root.rglob("*")
            if p.is_file() and "node_modules" not in p.parts and ".git" not in p.parts]


def fixture_dirs(files: list[str]) -> list[str]:
    return sorted({str(Path(f).parent) for f in files
                   if Path(f).parent.name == "fixtures" and f.endswith(".sql")})


def fixture_colors(root: Path, files: list[str] | None = None) -> dict:
    """``{"seed": grey, "colors": {name: colour}}`` for every fixture in the project.

    Configured colours first; the rest take the palette in folder order, skipping any
    colour the configuration already spent, so a fallback never repeats a chosen one."""
    files = _fx_ls(root) if files is None else files
    names, chosen = [], {}
    for d in fixture_dirs(files):
        for f in sorted(files):
            p = Path(f)
            if str(p.parent) == d and p.suffix == ".sql" and _FX_NAME.fullmatch(p.stem):
                if p.stem not in names:
                    names.append(p.stem)
        try:
            cfg = json.loads((root / d / FIXTURE_COLORS_FILE).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            cfg = {}
        for k, v in (cfg.items() if isinstance(cfg, dict) else ()):
            if isinstance(v, str) and _FX_COLOUR.fullmatch(v.strip()):
                chosen[str(k)] = v.strip()
    seed = chosen.pop("seed", None) or chosen.pop("default", None) or FIXTURE_SEED
    free = [c for c in FIXTURE_PALETTE if c.lower() not in {v.lower() for v in chosen.values()}]
    free = free or list(FIXTURE_PALETTE)
    colors, i = {}, 0
    for n in names:
        if n in chosen:
            colors[n] = chosen[n]
        else:
            colors[n] = free[i % len(free)]
            i += 1
    for n, c in chosen.items():
        colors.setdefault(n, c)
    return {"seed": seed, "colors": colors, "palette": free}


def demo_fixtures(root: Path | None, files: list[str] | None = None) -> list[tuple[str, str]]:
    """``[("", seed colour), (name, colour), …]``: the seed (Default) first, then every
    ``<name>.sql`` the project's fixtures folders hold, in folder order — the Demo tab's
    "DB Fixture:" row. Read off the files at build time, never off the running app: the
    row is on screen with the app down, and an instance started from an older image must
    not shrink the list (8 Oct 2026: :7655 listed only Default while green.sql was there).
    A name only ``fixture-colors.json`` mentions has no SQL to load and is not listed."""
    if root is None:
        return [("", FIXTURE_SEED)]
    root = Path(root)
    files = _fx_ls(root) if files is None else files
    reg = fixture_colors(root, files)
    on_disk = {Path(f).stem for f in files
               if Path(f).parent.name == "fixtures" and f.endswith(".sql")}
    return [("", reg["seed"])] + [(n, c) for n, c in reg["colors"].items() if n in on_disk]


def _fx_strip_comments(src: str) -> str:
    """Comments out, strings kept: a comment is the author musing, a string is what runs."""
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c in "'\"`":
            j = i + 1
            while j < n and src[j] != c:
                j += 2 if src[j] == "\\" else 1
            out.append(src[i:j + 1]); i = j + 1
        elif src.startswith("//", i):
            j = src.find("\n", i); i = n if j < 0 else j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2); i = n if j < 0 else j + 2
        else:
            out.append(c); i += 1
    return "".join(out)


def _fx_explicit(text: str, known: set[str]) -> set[str]:
    found = set()
    for m in re.finditer(r"@fixture[:=-]([a-z0-9][a-z0-9-]*)", text):
        found.add(m.group(1))
    for m in re.finditer(r"__reset/([a-z0-9][a-z0-9-]*)", text):
        found.add(m.group(1))
    for m in re.finditer(r"\b(?:loadFixture|resetTo|useFixture|fixture)\(\s*['\"`]"
                         r"([a-z0-9][a-z0-9-]*)['\"`]", text):
        found.add(m.group(1))
    out = set()
    for f in found:
        if f in ("seed", "default"):
            out.add("seed")
        elif f in known:
            out.add(f)
    return out


def _fx_verdict(tags: str, code: str, known: set[str]) -> str | None:
    hits = _fx_explicit(tags + "\n" + code, known)
    if len(hits) == 1:
        return hits.pop()
    if len(hits) > 1:
        return None                          # two fixtures named: not ours to pick
    if re.search(r"(?<![\w-])@seed(?![\w-])", tags) or _FX_SEEDWORD.search(code):
        return "seed"
    return None


# --- Cucumber ----------------------------------------------------------------------------

_FX_STEPDEF = re.compile(r"\b(?:Given|When|Then|And|But|defineStep)\(\s*(['\"`])((?:\\.|(?!\1).)*)\1")


def _fx_expr_to_regex(expr: str) -> re.Pattern | None:
    out, i = [], 0
    while i < len(expr):
        c = expr[i]
        if c == "{":
            j = expr.find("}", i)
            kind = expr[i + 1:j] if j > 0 else ""
            out.append({"word": r"\S+", "string": r"(?:\"[^\"]*\"|'[^']*')",
                        "int": r"-?\d+", "float": r"-?[\d.]+"}.get(kind, r".*"))
            i = j + 1 if j > 0 else len(expr)
        else:
            out.append(re.escape(c)); i += 1
    try:
        return re.compile("^" + "".join(out) + "$")
    except re.error:
        return None


def _fx_step_defs(root: Path, files: list[str]) -> list[tuple[re.Pattern, str]]:
    defs = []
    for f in files:
        if not re.search(r"\.[cm]?[jt]s$", f) or "node_modules" in f:
            continue
        try:
            src = (root / f).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if "@cucumber/cucumber" not in src:
            continue
        code = _fx_strip_comments(src)
        ms = list(_FX_STEPDEF.finditer(code))
        for k, m in enumerate(ms):
            rx = _fx_expr_to_regex(m.group(2).replace("\\'", "'").replace('\\"', '"'))
            if rx is not None:
                end = ms[k + 1].start() if k + 1 < len(ms) else len(code)
                defs.append((rx, code[m.start():end]))
    return defs


_FX_KW = re.compile(r"^\s*(?:Given|When|Then|And|But|\*)\s+(.*)$")
_FX_BLOCK = re.compile(r"^\s*(Feature|Background|Scenario Outline|Scenario Template|Scenario|"
                    r"Example|Rule|Examples|Scenarios):")


def _fx_feature_tests(rel: str, src: str, defs, known: set[str]) -> dict[str, str]:
    lines = src.splitlines()
    feature_tags, pending, background = "", "", []
    scenarios = []                              # (line, tags, steps)
    cur = None
    for no, line in enumerate(lines, 1):
        s = line.strip()
        if s.startswith("@"):
            pending += " " + s
            continue
        m = _FX_BLOCK.match(line)
        if m:
            kind = m.group(1)
            if kind == "Feature":
                feature_tags, cur = pending, None
            elif kind == "Background":
                cur = background
            elif kind.startswith("Scenario") or kind == "Example":
                cur = []
                scenarios.append((no, pending, cur))
            else:
                cur = None if kind in ("Examples", "Scenarios") else cur
            pending = ""
            continue
        k = _FX_KW.match(line)
        if k and cur is not None:
            cur.append(re.sub(r"<[^>]+>", "X", k.group(1).strip()))
    out = {}
    for no, tags, steps in scenarios:
        code = []
        for step in background + steps:
            for rx, body in defs:
                if rx.match(step):
                    code.append(body)
                    break
        v = _fx_verdict(feature_tags + " " + tags, "\n".join(code), known)
        if v:
            out[f"{rel}:{no}"] = v
    return out


# --- Playwright --------------------------------------------------------------------------

_FX_TEST = re.compile(r"^\s*test(?:\.(?:only|fixme|slow))?\(\s*['\"`]", re.M)


def _fx_block_end(code: str, start: int) -> int:
    """End of the `(...)` call opened at the first `(` from `start`."""
    i = code.find("(", start)
    depth = 0
    while 0 <= i < len(code):
        c = code[i]
        if c in "'\"`":
            j = i + 1
            while j < len(code) and code[j] != c:
                j += 2 if code[j] == "\\" else 1
            i = j
        elif c in "({[":
            depth += 1
        elif c in ")}]":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return len(code)


def _fx_local_imports(root: Path, rel: str, code: str) -> str:
    here = (root / rel).parent
    texts = []
    for m in re.finditer(r"""from\s+['"](\.{1,2}/[^'"]+)['"]""", code):
        spec = m.group(1)
        if "/support/" in spec + "/" or spec.startswith("./support"):
            continue
        for ext in ("", ".ts", ".js", ".tsx", ".mjs", "/index.ts", "/index.js"):
            p = (here / (spec + ext)).resolve()
            if p.is_file():
                try:
                    texts.append(_fx_strip_comments(p.read_text(encoding="utf-8")))
                except (OSError, UnicodeDecodeError):
                    pass
                break
    return "\n".join(texts)


def _fx_spec_tests(root: Path, rel: str, src: str, known: set[str]) -> dict[str, str]:
    if "@playwright/test" not in src and "trace-fixture" not in src:
        return {}
    code = _fx_strip_comments(src)
    # The comment-stripped text keeps every newline, so offsets map back to source lines
    # through the original — count them in `src` by matching the same test openers there.
    src_lines = [src[:m.start()].count("\n") + 1 + (m.group(0)[:1] == "\n")
                 for m in _FX_TEST.finditer(src)]
    spans = [(m.start(), _fx_block_end(code, m.start())) for m in _FX_TEST.finditer(code)]
    if len(spans) != len(src_lines):
        return {}
    shared, last = [], 0
    for a, b in spans:
        shared.append(code[last:a]); last = b
    shared.append(code[last:])
    shared_text = "".join(shared) + "\n" + _fx_local_imports(root, rel, code)
    out = {}
    for (a, b), line in zip(spans, src_lines):
        body = code[a:b]
        tags = " ".join(re.findall(r"@[\w:=-]+", body))
        v = _fx_verdict(tags, body + "\n" + shared_text, known)
        if v:
            out[f"{rel}:{line}"] = v
    return out


def fixtures_by_test(root: Path, files: list[str] | None = None) -> dict[str, str]:
    """``{"<repo-relative file>:<line>": fixture}`` — ``"seed"`` or a fixture's name —
    for every E2E test whose starting data can be read off its code. Absent = unknown."""
    root = Path(root)
    files = _fx_ls(root) if files is None else files
    known = set(fixture_colors(root, files)["colors"])
    out: dict[str, str] = {}
    features = [f for f in files if f.endswith(".feature") and "node_modules" not in f]
    defs = _fx_step_defs(root, files) if features else []
    for f in features:
        try:
            out.update(_fx_feature_tests(f, (root / f).read_text(encoding="utf-8"), defs, known))
        except (OSError, UnicodeDecodeError):
            pass
    for f in files:
        if _FX_SPEC.search(f) and "node_modules" not in f:
            try:
                out.update(_fx_spec_tests(root, f, (root / f).read_text(encoding="utf-8"), known))
            except (OSError, UnicodeDecodeError):
                pass
    return out


def fixture_registry(root: Path) -> dict:
    files = _fx_ls(Path(root))
    reg = fixture_colors(Path(root), files)
    reg["tests"] = fixtures_by_test(Path(root), files)
    return reg


def render_fixture_registry(root: Path) -> str:
    """The ``hr-fixtures`` JSON block FIXTURES_JS reads, or "" when the project has no
    fixtures and no test leans on the seed — then neither tab draws a dot."""
    reg = fixture_registry(root)
    if not reg["colors"] and not reg["tests"]:
        return ""
    return ('<script type="application/json" id="hr-fixtures">'
            + json.dumps(reg).replace("</", "<\\/") + "</script>")


if __name__ == "__main__":
    import sys
    print(json.dumps(fixture_registry(Path(sys.argv[1] if len(sys.argv) > 1 else ".")), indent=1))
