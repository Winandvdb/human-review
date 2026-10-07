"""The `N↑` before the branch name: commits added after the reviewed one, no band, no bullet."""
import html
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hrbuild.shared.masthead import ref_badges
from hrbuild.tabs.review import commits_after_review


def _git(repo, *a):
    return subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                          check=True, capture_output=True, text=True).stdout.strip()


def _repo(tmp_path, after):
    _git(tmp_path, "init", "-q")
    (tmp_path / "a.txt").write_text("0")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "reviewed")
    review = _git(tmp_path, "rev-parse", "HEAD")
    for i in range(after):
        (tmp_path / "a.txt").write_text(str(i + 1))
        _git(tmp_path, "commit", "-qam", f"later {i}")
    out = tmp_path / ".human-review"
    out.mkdir()
    (out / "aftermath.json").write_text(json.dumps({"review": review}))
    return out, review


def test_commits_after_the_review_are_listed_newest_first(tmp_path):
    out, review = _repo(tmp_path, 2)
    got = commits_after_review(out, tmp_path)
    assert got["review"] == review[:8]
    assert [c["subject"] for c in got["commits"]] == ["later 1", "later 0"]


def test_nothing_after_the_review_means_no_marker(tmp_path):
    out, _ = _repo(tmp_path, 0)
    assert commits_after_review(out, tmp_path) is None
    assert "drift-ahead" not in ref_badges({"pr": {"branch": "b", "base": "main"}})


def test_the_marker_sits_right_before_the_head_ref_with_a_listing_tip():
    after = {"review": "abc12345", "commits": [{"short": "d1", "when": "06 Oct 11:20", "subject": "S"}]}
    out = ref_badges({"pr": {"branch": "test-pr", "base": "main"}, "_afterReview": after})
    assert 'class="drift drift-ahead"' in out and "1\u2191</span>" in out
    tip = html.unescape(re.search(r'data-tip-html="([^"]*)"', out).group(1))
    assert "1 commit added to this PR after the review (at abc12345):" in tip
    assert '<li><code>d1</code> S <span class="tipwhen">06 Oct 11:20</span></li>' in tip
    assert out.index("drift-ahead") < out.index("test-pr")
