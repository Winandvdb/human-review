"""The "Prompt to get this" buttons: one per piece — inside the card it is about, or at the
right end of the tab's title row when the piece is the whole tab."""
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


@pytest.mark.parametrize("anchor", sorted({a for p in PLACES.values() for _, _, a, _ in p
                                            if a}))
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
        assert card.rstrip().endswith("</button></div></div>") or card.rstrip().endswith(
            "</button></div></div></div>"), "the button closes the card"
    # A card that ends on a caption line gives that line the pill, not a row under it.
    assert '<div class="adoptfoot"><p class="sub dgm-unseen">Also changed</p>' \
           '<div class="adoptline adopt-title">' in cards[1]
    assert "adoptfoot" not in cards[0] + cards[2]
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


def test_the_tests_button_shares_the_filter_cell_on_the_title_row():
    """The panes fill the window, so the button used to float over their corner; now it
    sits on the title row, after the UI/API/unit filter, in the cell over the card."""
    body = ('<div class="reqmap"><div class="rm-body"><h2 class="tabtitle rm-head">Issue</h2>'
            '<div class="rm-text"></div><p class="rm-cats"><label class="rm-catf">UI</label>'
            '</p><div class="rm-side"><aside class="rm-code"><div>x</div></aside></div>'
            '</div></div>')
    out = place_prompts("requirements", body)
    assert re.search(r'<div class="adopthead"><p class="rm-cats">.*?</p>'
                     r'<div class="adoptline adopt-title">.*?</button></div></div>'
                     r'<div class="rm-side">', out)
    assert out.count("Prompt to get this") == 1


def test_the_cost_button_sits_in_the_header_row_beside_its_last_label():
    """Cost opens on its table, not a title: the header row is its first row, and the
    button goes in that row's last cell, before `cost`, on a zero-size anchor."""
    body = ('<table class="costtab costledger costfour"><thead><tr><th scope="col">component'
            '</th><th scope="col">cost</th></tr></thead><tbody><tr><th>x</th></tr></tbody>'
            '</table>')
    out = place_prompts("cost", body)
    assert re.search(r'<th scope="col">component</th><th scope="col">'
                     r'<div class="adoptline adopt-th">.*?</button></div>cost</th>', out)
    assert out.count("Prompt to get this") == 1


def test_a_script_inside_a_card_cannot_close_it_early():
    body = ('<div class="diagram"><script>var s = "</div><div>";</script>'
            '<div class="head"><b>Domain Model</b></div></div><p>after</p>')
    out = place_prompts("data", body)
    assert out.endswith('</button></div></div><p>after</p>')
    assert _close(body, 0) == (len(body) - len("</div><p>after</p>"),
                               len(body) - len("<p>after</p>"))


def test_a_tab_whose_anchor_moved_still_offers_its_button_at_the_end():
    out = place_prompts("requirements", "<p>renamed markup</p>")
    assert out.startswith("<p>renamed markup</p>") and out.count("Prompt to get this") == 1


#: The tabs whose prompt is about the whole tab, not one card of it (5 Oct 2026, Victor),
#: each with the first row its button joins: the tab's title wherever it has one.
WHOLE_TAB = {"sequence": '<h2 class="tabtitle" id="sequences">Sequence diagrams</h2>',
             "city": '<h2 class="tabtitle" id="codecity">Impact on code size</h2>',
             "complexity": '<h2 class="tabtitle cx-title"><a href="#">Cognitive</a> per</h2>',
             "logging": '<h2 class="tabtitle" id="logging-added">Uses of logging</h2>',
             "owners": '<h2 class="tabtitle cow-title">Needs approval by</h2>',
             "api": '<div class="apiverdict red"><span class="dot"></span>Breaking</div>',
             "dsaudit": '<h2 class="tabtitle">UX design system</h2>'}


@pytest.mark.parametrize("tid", sorted(WHOLE_TAB))
def test_a_whole_tab_prompt_sits_at_the_right_end_of_the_tabs_title_row(tid):
    """If the tab holds one consistent piece of knowledge, one generation, its prompt goes on
    the right side of that tab's title (Victor, 5 Oct 2026): the first row and the button
    become one flex row, outside every card — never the first card, never the last."""
    first = WHOLE_TAB[tid]
    rest = ('<p class="tabsub">from where</p>'
            '<div class="dsa"><details>Book A Visit</details></div>'
            '<div class="cx-group"><div class="cx-list">JOBS</div></div>'
            '<div class="cow"><div class="cow-row">approval</div></div>'
            '<script>var s = "</div>";</script>')
    out = place_prompts(tid, '<p class="paneltag">X</p>' + first + rest)
    assert out.count("Prompt to get this") == 1
    head = re.escape('<p class="paneltag">X</p><div class="adopthead">' + first)
    assert re.match(head + r'<div class="adoptline adopt-title">.*?</button></div></div>'
                    + re.escape(rest) + "$", out, re.S)
    assert all(how == "title" for _, how, _, _ in PLACES[tid])


def test_only_the_first_title_takes_the_button():
    body = ('<h2 class="tabtitle">One</h2><p>x</p><h2 class="tabtitle">Two</h2>')
    out = place_prompts("logging", body)
    assert out.startswith('<div class="adopthead"><h2 class="tabtitle">One</h2>')
    assert out.count("Prompt to get this") == 1


def test_a_whole_tab_without_its_title_row_still_closes_the_panel_with_its_button():
    out = place_prompts("city", '<a class="city"><img></a>')
    assert out.startswith('<a class="city"><img></a><div class="adoptline adopt-end">')


def test_every_tab_is_either_per_card_or_whole_tab_or_one_of_the_agreed_exceptions():
    per_card = {"data", "packages", "review"}
    # The Tests filter row, the Cost header row, the Demo's transcript column.
    agreed = {"requirements": "title", "cost": "th", "behaviour": "col"}
    assert set(PLACES) == per_card | set(WHOLE_TAB) | set(agreed)
    for tid, how in agreed.items():
        assert [h for _, h, _, _ in PLACES[tid]] == [how]


def test_a_header_cell_marked_data_adopt_takes_the_button_instead_of_the_last():
    """The cost tab's `time` column stands left of `cost`: the pill, hung before `cost`,
    covered `time` and its hover. The cell that asks for it gets it."""
    body = ('<table class="costtab costledger costfour"><thead><tr><th scope="col">component'
            '</th><th scope="col" data-adopt>time</th><th scope="col">cost</th></tr></thead>'
            '<tbody><tr><th>x</th></tr></tbody></table>')
    out = place_prompts("cost", body)
    assert re.search(r'<th scope="col" data-adopt><div class="adoptline adopt-th">.*?</button>'
                     r'</div>time</th><th scope="col">cost</th>', out)


def test_tab_title_pills_say_page_and_smaller_areas_keep_the_short_label():
    """Victor, 7 Oct 2026: a pill on a whole tab's title row reads "…this page"; the ones
    on a diagram card or a part of a screen stay "…this"."""
    tab = place_prompts("city", '<h2 class="tabtitle">City</h2><p>x</p>')
    assert "Prompt to get this page</button>" in tab
    api = place_prompts("api", '<div class="apiverdict ok">v</div>')
    assert "Prompt to get this page</button>" in api
    card = place_prompts("data", _card("Domain Model", "DomainModel.puml",
                                       '<p class="sub dgm-unseen">Also changed</p>'))
    assert "adopt-title" in card and "Prompt to get this</button>" in card
    assert "this page" not in card
    cost = place_prompts("review", '<h2 id="assumed">A</h2><p class="pileround">r</p>')
    assert "Prompt to get this</button>" in cost and "this page" not in cost
