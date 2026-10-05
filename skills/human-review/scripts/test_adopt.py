"""The "Prompt to get this" buttons: one per piece, inside the card it is about."""
import html
import re
from pathlib import Path

import pytest

from hrbuild.shared.adopt import (PIECES, PLACES, _close, adopt_html, adopt_prompt,
                                  place_prompts)
from hrbuild.shared.layout import LAYOUT_TABS
from hrbuild.tabs.cost import COST_TAB_ID

SCRIPTS = Path(__file__).resolve().parent
SKILL = SCRIPTS.parent


def _prompts(out):
    return [html.unescape(p) for p in re.findall(r'data-copy="([^"]*)"', out)]


def test_every_tab_the_build_knows_has_a_place_for_its_buttons():
    assert set(LAYOUT_TABS) | {"review", COST_TAB_ID} <= set(PLACES)


@pytest.mark.parametrize("piece", sorted(PIECES))
def test_every_file_a_prompt_points_at_is_in_the_skill(piece):
    for start in PIECES[piece][1].split(", "):
        if not start.startswith("http"):
            assert (SKILL / start).exists(), start


@pytest.mark.parametrize("anchor", sorted({a for p in PLACES.values() for _, _, a, _ in p}))
def test_every_class_a_button_anchors_on_is_still_emitted_somewhere(anchor):
    """The producers do not know about the button, so a renamed class would silently move
    it to the foot of the panel. This is where that rename shows up."""
    cls = re.search(r'(class|id)="([\w-]+)', anchor).group(2)
    sources = [p.read_text(encoding="utf-8") for p in SCRIPTS.rglob("*.py")
               if not p.name.startswith("test_")]
    assert any(f'"{cls}' in s or f' {cls}"' in s or f"'{cls}" in s for s in sources), cls


def test_a_piece_without_a_prompt_gets_no_button():
    assert adopt_prompt("nope") is None
    assert adopt_html("nope") == ""
    assert place_prompts("nope", "<p>x</p>") == "<p>x</p>"


def test_the_button_says_prompt_to_get_this_and_copies_the_prompt_escaped():
    out = adopt_html("api")
    assert 'class="adopt copycmd"' in out and "\U0001F916 Prompt to get this</button>" in out
    assert "Adopt" not in out
    assert _prompts(out)[0].startswith("Get the REST contract")


def _card(title, src, inner=""):
    return (f'<div class="diagram"><div class="head"><b>{title}</b>'
            f'<span>{src}</span></div><div class="svgbox"><svg></svg></div>{inner}</div>')


def test_each_data_card_gets_its_own_button_inside_its_border_with_its_own_prompt():
    body = (_card("Domain Model", "DomainModel.puml")
            + _card("DB", "DB.puml", '<p class="sub dgm-unseen">Also changed</p>')
            + _card("Conceptual Model", "ConceptualModel.drawio.png"))
    out = place_prompts("data", body)
    cards = out.split('<div class="diagram">')[1:]
    assert len(cards) == 3
    for card in cards:
        assert card.count("Prompt to get this") == 1
        assert card.rstrip().endswith("</button></div></div>"), "the button closes the card"
    first = [p.split(" into this repository")[0] for p in _prompts(out)]
    assert first == [
        "Get the domain-model class diagram generated from your domain classes by Java "
        "reflection, committed as PlantUML and diffed base against branch",
        "Get the ERD generated from your DB migration scripts, committed as PlantUML and "
        "diffed base against branch, with the schema changes it cannot draw listed under it",
        "Get the hand-drawn draw.io Conceptual Model diagram, checked against the code by a "
        "test and diffed base against branch"]


def test_a_diagram_inside_a_test_pair_is_part_of_the_pair_not_a_piece_of_its_own():
    body = '<div class="diagram dgm-bare"><div class="head"></div></div>'
    assert place_prompts("packages", body) == body


def test_the_demo_button_sits_under_the_transcript_in_a_column_of_its_own():
    body = ('<div class="vidwrap"><div class="vidcol"><video></video></div>'
            '<ol class="transcript"><li>cue</li></ol></div>')
    out = place_prompts("behaviour", body)
    assert re.search(r'<div class="adoptcol"><ol class="transcript">.*?</ol>'
                     r'<div class="adoptline adopt-after">.*?</div></div></div>$', out)


def test_each_review_round_gets_a_button_at_its_own_end():
    body = ('<p class="pileround">Round I</p><h2 id="assumed">A</h2><ol class="findings"></ol>'
            '<p class="pileround">Round II</p><h2 id="first">B</h2><ol class="findings"></ol>'
            '<p class="pileround">Round III</p><h2 id="fixed">C</h2><ol class="findings"></ol>'
            '<details class="fixother"></details>')
    out = place_prompts("review", body)
    rounds = out.split('<p class="pileround">')[1:]
    assert [r.count("Prompt to get this") for r in rounds] == [1, 1, 1]
    assert all(r.endswith("</button></div>") for r in rounds)


def test_the_tests_button_floats_over_the_panes_and_adds_no_height():
    body = ('<div class="reqmap"><div class="rm-body"><div class="rm-text"></div>'
            '<div class="rm-side"><aside class="rm-code"><div>x</div></aside></div>'
            '</div></div>')
    out = place_prompts("requirements", body)
    assert '</aside></div><div class="adoptline adopt-float">' in out


def test_a_script_inside_a_card_cannot_close_it_early():
    body = ('<div class="dsa"><script>var s = "</div><div>";</script>'
            '<div class="dsa-row"></div></div><p>after</p>')
    out = place_prompts("dsaudit", body)
    assert out.endswith('</button></div></div><p>after</p>')
    assert _close(body, 0) == (len(body) - len("</div><p>after</p>"),
                               len(body) - len("<p>after</p>"))


def test_a_tab_whose_anchor_moved_still_offers_its_button_at_the_end():
    out = place_prompts("complexity", "<p>renamed markup</p>")
    assert out.startswith("<p>renamed markup</p>") and out.count("Prompt to get this") == 1
