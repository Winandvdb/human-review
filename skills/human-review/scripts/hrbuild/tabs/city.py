"""The Code City tab."""
from __future__ import annotations


#: What the Code City shot is above, said as a heading rather than as a caption. Fixed in
#: the build and not asked of every content file, for the same reason the zip offer in the
#: footer is: it is a fact about what this picture always shows, not about this branch. A
#: `title` on the block overrides it for a page that means something else by the picture.
CITY_HEADING = "Impact on code size, complexity, coupling, \u2026"


#: The tab's id, as `shared/layout.py` and `run-steps.STEPS` spell it.
CITY_TAB = "city"


def declare_city_run_tests(root, out_dir, skill_dir) -> dict | None:
    """The Code City tab's ⏳: run the tests, then rebuild the city with their coverage.

    The Tests tab's own press (`tabs/tests.py:declare_run_tests_rerun`) with the city's
    producer appended — not a second runner. The city is coloured by what those suites
    measured (line coverage, and what the end-to-end tests alone reach), so a press that
    re-ran them and left the city alone would leave its colours a run behind the Tests tab
    beside it. Its ⚙️ stays `--steps city`: the coverage already on disk, nothing run."""
    from .tests import declare_run_tests_rerun
    return declare_run_tests_rerun(
        root, out_dir, skill_dir, tab=CITY_TAB, then=(CITY_TAB,),
        label="Re-run the tests, then rebuild the Code City with their coverage",
        tip="Re-run the tests, then rebuild the city with their coverage. Free, takes "
            "minutes, needs the app running.")
