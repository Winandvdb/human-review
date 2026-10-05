"""The "Adopt this tab" prompts: one per tab, and every path they name exists."""
from pathlib import Path

import pytest

from hrbuild.shared.adopt import ADOPT, adopt_html, adopt_prompt
from hrbuild.shared.layout import LAYOUT_TABS
from hrbuild.tabs.cost import COST_TAB_ID

SKILL = Path(__file__).resolve().parent.parent


def test_every_tab_the_build_knows_has_a_prompt():
    assert set(LAYOUT_TABS) | {"review", COST_TAB_ID} <= set(ADOPT)


@pytest.mark.parametrize("tid", sorted(ADOPT))
def test_every_file_a_prompt_points_at_is_in_the_skill(tid):
    for start in ADOPT[tid][1].split(", "):
        if not start.startswith("http"):
            assert (SKILL / start).exists(), start


def test_a_tab_without_a_prompt_gets_no_button():
    assert adopt_prompt("nope", "Nope") is None
    assert adopt_html("nope", "Nope") == ""


def test_the_button_copies_the_prompt_escaped():
    out = adopt_html("api", "API")
    assert 'class="adopt copycmd"' in out
    assert "the API tab of its review page" in out
