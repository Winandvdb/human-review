"""The folder behind a box: a Java package's directory, a Maven module's.

The Structure tab draws the code's shape — `packages.puml`'s boxes are packages, the
module graph's are Maven modules — and a reader looking at `..mcp` wants to see what is
in it. So every such box carries the folder it stands for, relative to the checkout
(`data-folder`), and a link to that folder on github.com at the reviewed commit. Served,
`FOLDERS_JS` turns the click into "reveal it in the VS Code window that has this
checkout" (`serve-review.py`'s `/__reveal_folder__`); off disk the link is all there is.

Nothing here knows petclinic. The package root is not configured: a box's stereotype is an
ArchUnit package pattern (`..rest.dto`), and the root is whichever package every pattern
in the diagram sits under — read off the tracked sources of the module the `.puml` lives
in. A module is the directory of the tracked `pom.xml` whose own `artifactId` is the box's
name. A box neither explains gets no link, rather than a guessed one.
"""
from __future__ import annotations

import functools
import html
import re
import subprocess
import urllib.parse
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path, PurePosixPath

from .snippets import github_blob_base

#: A component declaration, in the spellings PlantUML accepts: `[Label]`, `[Label] as a`,
#: `component "Label" as a`, `component a as "Label"`, `component Name`, and the same with
#: rectangle/node/package/folder/frame. A bare word without a keyword is not one — that is
#: a `skinparam` or an arrow's first half.
_DECL = re.compile(
    r'^\s*(?:(?:component|rectangle|node|package|folder|frame|artifact)\s+)?'
    r'(?:\[(?P<b>[^\]]+)\]|"(?P<q>[^"]+)"|(?P<w>[\w.\-]+))'
    r'(?:\s+as\s+(?:"(?P<aq>[^"]+)"|\[(?P<ab>[^\]]+)\]|(?P<aw>[\w.\-]+)))?'
    r'(?P<rest>.*)$')
_KEYWORD = re.compile(r'^\s*(?:component|rectangle|node|package|folder|frame|artifact)\s')
_STEREO = re.compile(r'<<\s*([^>]+?)\s*>>')
#: PlantUML's own markup for one box: `<g class="entity" data-qualified-name="…">`, a rect
#: and the name. Nested groups or an `<a>` already inside mean somebody else links it.
_ENTITY = re.compile(r'(<g class="entity"[^>]*?data-qualified-name="(?P<q>[^"]*)"[^>]*)>'
                     r'(?P<inner>.*?)</g>', re.S)
_SOURCE_DIR = re.compile(r'^(?P<src>(?:.*/)?src/main/(?:java|kotlin))/(?P<pkg>.+)$')


def _ls_files(root: Path, *spec: str) -> list[str]:
    out = subprocess.run(["git", "-C", str(root), "ls-files", "--", *spec],
                         capture_output=True, text=True)
    return out.stdout.splitlines() if out.returncode == 0 else []


def puml_boxes(text: str) -> list[dict]:
    """`{name, label, stereotype}` for each box a `.puml` declares. `name` is what
    PlantUML writes as `data-qualified-name` (the alias, or the label without one)."""
    boxes = []
    for line in text.splitlines():
        m = _DECL.match(line)
        if not m or not (m["b"] or m["q"] or _KEYWORD.match(line)):
            continue
        first = m["b"] or m["q"] or m["w"]
        alias = m["aq"] or m["ab"] or m["aw"]
        # `component a as "Label"`: the quoted side is the label, whichever side it is on.
        label, name = first, alias or first
        if alias and m["aq"] and not m["q"]:
            label, name = alias, first
        st = _STEREO.search(m["rest"] or "")
        boxes.append({"name": name.strip(), "label": label.strip(),
                      "stereotype": st[1].strip() if st else None})
    return boxes


def _module_dir(rel: str, root: Path) -> str:
    """The build module a diagram belongs to: its nearest ancestor with a build file."""
    for parent in PurePosixPath(rel).parents:
        d = root / parent
        if any((d / f).is_file() for f in ("pom.xml", "build.gradle", "build.gradle.kts")):
            return "" if str(parent) == "." else str(parent)
    return ""


@functools.lru_cache(maxsize=None)
def _packages(root: Path, module: str) -> dict[str, list[str]]:
    """Dotted package → the directories (repo-relative) that hold it, from tracked sources."""
    found: dict[str, list[str]] = {}
    for path in _ls_files(root, module or "."):
        if not path.endswith((".java", ".kt")):
            continue
        m = _SOURCE_DIR.match(str(PurePosixPath(path).parent))
        if not m:
            continue
        parts = m["pkg"].split("/")
        for i in range(1, len(parts) + 1):
            dotted = ".".join(parts[:i])
            where = f'{m["src"]}/{"/".join(parts[:i])}'
            if where not in found.setdefault(dotted, []):
                found[dotted].append(where)
    return found


def _pattern(stereotype: str) -> tuple[str, bool] | None:
    """An ArchUnit package identifier as `(package, relative)`: `..rest.dto` is any
    package ending in `rest.dto`, `com.acme.rest` that package exactly. A trailing `..`
    (and its subpackages) names the same top folder. Wildcards and alternations name
    no one folder, so they get none."""
    s = stereotype.strip()
    if not s or re.search(r"[*()\[\]|\s]", s):
        return None
    relative = s.startswith("..")
    s = s.strip(".")
    return (s, relative) if s and ".." not in s else None


def package_folders(rel: str, root: Path) -> dict[str, str]:
    """Box name → the folder of the package its stereotype names, for one `.puml`."""
    src = root / rel
    if not src.is_file():
        return {}
    wanted = {}
    for box in puml_boxes(src.read_text(encoding="utf-8", errors="replace")):
        p = box["stereotype"] and _pattern(box["stereotype"])
        if p:
            wanted[box["name"]] = p
    if not wanted:
        return {}
    pkgs = _packages(root, _module_dir(rel, root))
    # For each box, every package its pattern could mean, keyed by the root it implies.
    options: dict[str, dict[str, str]] = {}
    for name, (pkg, relative) in wanted.items():
        hits = {}
        for dotted, dirs in pkgs.items():
            if dotted == pkg:
                hits[""] = dirs[0]
            elif relative and dotted.endswith("." + pkg):
                hits[dotted[: -len(pkg) - 1]] = dirs[0]
        options[name] = hits
    # The root package is the one most boxes agree on — `victor.training.petclinic` for
    # all nine of petclinic's — the shallowest on a tie. A box that does not fit it still
    # gets its folder when its own pattern has exactly one answer.
    votes = Counter(base for hits in options.values() for base in hits)
    common = min(votes, key=lambda b: (-votes[b], b.count("."), b)) if votes else None
    out = {}
    for name, hits in options.items():
        if common in hits:
            out[name] = hits[common]
        elif len(hits) == 1:
            out[name] = next(iter(hits.values()))
    return out


def _artifact_id(pom: Path) -> str | None:
    """The project's own `artifactId`, not its parent's."""
    try:
        tree = ET.parse(pom)
    except (ET.ParseError, OSError):
        return None
    for child in tree.getroot():
        if child.tag.rsplit("}", 1)[-1] == "artifactId":
            return (child.text or "").strip() or None
    return None


@functools.lru_cache(maxsize=None)
def maven_modules(root: Path) -> dict[str, str]:
    """`artifactId` → the module's directory, for every tracked `pom.xml`. All of them
    rather than one reactor's `<modules>`: a repository of sibling modules has no
    aggregator to read, and a reactor's modules are tracked poms like any other."""
    out = {}
    for pom in _ls_files(root, "pom.xml", "*/pom.xml"):
        if "/node_modules/" in f"/{pom}" or pom.startswith(".human-review/"):
            continue
        aid = _artifact_id(root / pom)
        folder = str(PurePosixPath(pom).parent)
        if aid and aid not in out:
            out[aid] = "." if folder == "." else folder
    return out


@functools.lru_cache(maxsize=None)
def _tree_base(root: Path) -> str | None:
    """`https://github.com/<owner>/<repo>/tree/<HEAD>` — the folder as the reviewed commit
    has it — or None without a github.com remote."""
    repo = github_blob_base(root)
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    return f"{repo}/tree/{head}" if repo and head else None


def folder_targets(rel: str, root: Path) -> dict[str, tuple[str, str]]:
    """Box name → `(label, repo-relative folder)` for every box in `rel` that is a package
    or a Maven module of this checkout."""
    src = root / rel
    if not src.is_file():
        return {}
    boxes = puml_boxes(src.read_text(encoding="utf-8", errors="replace"))
    pkgs = package_folders(rel, root)
    modules = maven_modules(root)
    by_dir = {PurePosixPath(d).name: d for d in modules.values() if d != "."}
    out = {}
    for box in boxes:
        folder = (pkgs.get(box["name"]) or modules.get(box["label"])
                  or modules.get(box["name"]) or by_dir.get(box["label"]))
        if folder:
            out.setdefault(box["name"], (box["label"], folder))
    return out


def link_folders(markup: str, rel: str, root: Path) -> str:
    """Every box in `markup` (inlined SVGs of `rel`) that is a package or a module carries
    `data-folder` / `data-folder-name`, and its shapes are wrapped in a link to the folder
    on github.com when the checkout has a remote there. Boxes already linked are left be."""
    targets = folder_targets(rel, root) if rel else {}
    if not targets:
        return markup
    tree = _tree_base(root)

    def one(m: re.Match) -> str:
        hit = targets.get(html.unescape(m["q"]))
        if not hit or "<a " in m["inner"] or "<g" in m["inner"] or "data-folder=" in m[1]:
            return m.group(0)
        label, folder = hit
        attrs = (f' data-folder="{html.escape(folder, quote=True)}"'
                 f' data-folder-name="{html.escape(label, quote=True)}"')
        inner = m["inner"]
        if tree:
            href = tree if folder == "." else f"{tree}/{urllib.parse.quote(folder)}"
            tip = html.escape(f"Open {label} on GitHub", quote=True)
            inner = f'<a href="{html.escape(href, quote=True)}" data-tip="{tip}">{inner}</a>'
        return f"{m[1]}{attrs}>{inner}</g>"

    return _ENTITY.sub(one, markup)
