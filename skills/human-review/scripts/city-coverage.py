#!/usr/bin/env python3
"""The Code City's two coverage colours, out of the coverage the test step already measured.

`testcov.py` runs every suite once with a per-test hook — JUnit under JaCoCo, Karma under
Istanbul, the browser suites with Chromium's V8 coverage and a JaCoCo dump of the backend
they drove — and writes `assets/test-coverage.json`: per test, every line of production
code it ran (`tests[].hits`), and per file, every line some probe could see run
(`executableAll`). That is a whole-project line coverage already, measured, sitting on
disk. The city used to have none: its own coverage pass (code-city's `generate.sh` step
[3]) needs a JaCoCo report and was switched off, with the four colours it fed left in the
dropdown marked unavailable, on the same page whose Tests tab had just run every suite.

This turns one into the other — nothing is run:

  line        lines run by ANY test (unit, API, end-to-end; every suite merged)
              / lines some probe can see run
  acceptance  lines run by the end-to-end tests alone / the same denominator. "End-to-end"
              is exactly what the Tests tab calls UI or API (`tabs/tests.py:_cov_cat`): a
              browser-driven test (Playwright, the Cucumber scenarios run through
              Chromium), a backend Cucumber feature, a JVM test that goes through the HTTP
              layer (MockMvc, TestRestTemplate, RestAssured, WebTestClient). Karma specs and
              plain JUnit are unit tests and count only towards `line`.

A file no probe can see (`executableAll` does not name it) is left out, so the city draws
it "not measured", never 0%. Acceptance is left out everywhere when no end-to-end test was
measured at all — "the browser suite never reached this" and "the browser suite did not
run" are different claims, and only the first is a finding.

Writes the JSON `code-city/generate.sh --coverage` reads (format: code-city's
`coverage_input.py`), with `commit` saying which HEAD the run measured.

Usage:
  city-coverage.py [--in .human-review/assets/test-coverage.json]
                   [--out .human-review/assets/codecity-coverage.json] [--root REPO]

Exit 0 with the file written; 3 when there is nothing to convert (no coverage file, or one
written before `executableAll` existed) — the city is then built without coverage.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

DEFAULT_IN = Path(".human-review/assets/test-coverage.json")
DEFAULT_OUT = Path(".human-review/assets/codecity-coverage.json")
#: The Tests tab's categories that are not "one isolated component".
ACCEPTANCE = {"e2e", "api"}


def log(msg: str) -> None:
    print(f"[city-coverage] {msg}", file=sys.stderr, flush=True)


def category(test: dict, root: Path) -> str:
    """UI (`e2e`), API or unit — the Tests tab's own answer, never a second copy of it."""
    from hrbuild.tabs.tests import _cov_cat
    # A test testcov could not place at a file (`file: null`) is classified on its suite
    # and source alone, which is all `_cov_cat` needs for every kind but a JVM API test.
    return _cov_cat({**test, "file": test.get("file") or ""}, root)


def convert(doc: dict, root: Path) -> dict | None:
    """code-city's coverage JSON out of a `test-coverage.json`, or None with nothing in it."""
    executable = {f: set(v) for f, v in (doc.get("executableAll") or {}).items() if v}
    if not executable:
        return None
    ran: dict[str, set[int]] = {}
    e2e: dict[str, set[int]] = {}
    measured_e2e = False
    for t in doc.get("tests") or []:
        accept = category(t, root) in ACCEPTANCE
        measured_e2e = measured_e2e or accept
        for f, lines in (t.get("hits") or {}).items():
            if f not in executable:
                continue
            ran.setdefault(f, set()).update(lines)
            if accept:
                e2e.setdefault(f, set()).update(lines)
    files = {}
    for f in sorted(executable):
        total = len(executable[f])
        entry = {"line": {"covered": len(ran.get(f, set()) & executable[f]), "total": total}}
        if measured_e2e:
            entry["acceptance"] = {"covered": len(e2e.get(f, set()) & executable[f]),
                                   "total": total}
        files[f] = entry
    return {"source": "human-review testcov.py (assets/test-coverage.json)",
            "commit": doc.get("head", ""), "acceptance": measured_e2e, "files": files}


def summary(out: dict) -> str:
    def pct(key):
        c = sum(e[key]["covered"] for e in out["files"].values() if key in e)
        t = sum(e[key]["total"] for e in out["files"].values() if key in e)
        return f"{100.0 * c / t:.1f}%" if t else "not measured"
    return (f"{len(out['files'])} file(s): line coverage {pct('line')}, "
            f"acceptance {pct('acceptance')}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="src", default=str(DEFAULT_IN))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--root", help="the repository the paths are relative to "
                                   "(default: git toplevel of the working directory)")
    args = ap.parse_args(argv)
    root = Path(args.root or subprocess.run(["git", "rev-parse", "--show-toplevel"],
                                            capture_output=True, text=True).stdout.strip()
                or ".")
    src = Path(args.src)
    try:
        doc = json.loads(src.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        log(f"no coverage at {src} — the city is built without it")
        return 3
    out = convert(doc, root)
    if out is None:
        log(f"{src} has no executableAll (written by an older testcov.py) — re-run the tests "
            "(⏳), or `testcov.py --reuse` to re-read the last run")
        return 3
    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=0, separators=(",", ":")) + "\n", encoding="utf-8")
    log(f"{summary(out)} -> {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
