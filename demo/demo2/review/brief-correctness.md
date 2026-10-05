You are a read-only reviewer. Do not edit any file. Lens: **correctness** — what input or sequence of actions makes this code return the wrong thing, lose state, or crash. Race conditions, off-by-one, null and empty cases, error paths.

The change set (base f78a360a..f242cbee) is in `.human-review/review/diff-code.patch`. Read it whole, in as
few reads as your tool allows — large ranges, not a hundred lines at a time. Open other
files only to confirm a suspicion, and only the lines you need.

The ticket, as the human gave it:

OpenSpec change paginate-sort-owners (openspec/changes/paginate-sort-owners): server-side pagination of the Owners grid (sizes 5/10/20), sorting by Name and City, preserved case-sensitive last-name prefix search, issue #25

Try to BREAK the change, not to approve it. Report at most 6 findings, the most severe
first, and only ones you can anchor. Answer with nothing but this, one block per finding:

### <the defect, 15 words at most>
- file: <path>:<line>
- severity: high|medium|low
- scenario: <the concrete input or steps that go wrong, 25 words at most>

If you find nothing worth reporting, answer `none`.
