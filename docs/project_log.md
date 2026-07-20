# Project Log — Token Cost by Activity

## Purpose

This project is partly an experiment in whether asking an LLM to *write code*
that solves the problem is cheaper (in tokens) than asking the LLM to *solve
the problem directly* (e.g. reading each scanned image itself). See the
motivation in [`01_project_overview.md`](01_project_overview.md).

This log tracks an approximate token cost per unit of work, split by
category, so the two approaches can be compared later.

## Methodology (read before trusting the numbers)

There is no tool available in this session that reports the exact token
count of a message, an image, or a tool result. The Claude Code CLI's
`/cost` command shows the authoritative cumulative total for the whole
session, but not a per-message or per-category breakdown.

Every number below is therefore a **rough order-of-magnitude estimate**,
built from:

- Output text: ~4 characters per token.
- An image `Read`: a rough tier by rendered size —
  small crop (~1 answer cell): ~250 tokens;
  normalized table / debug overlay (~1200×600): ~800 tokens;
  full scanned page or contact sheet (~2000×1500+): ~1600 tokens.

These are estimates, not measurements. Treat the totals as directional
(useful for comparing categories against each other), not precise.

## Categories

- **code** — writing/editing Python, running scripts/tests, reading source files.
- **image** — the model reading/inspecting an image (scans, debug overlays, crops).
- **discussion** — planning, explanations, and this kind of meta-conversation.

## Log

| # | Task | Category | Est. tokens | Notes |
|---|------|----------|-------------:|-------|
| 1 | Read `01_project_overview.md` + all `docs/*.md`, `config.py`, `geometry.py`, `pipeline.py`, `utils.py`, `pipeline.sh` | code | ~9,000 | Orienting on the existing codebase before iteration 04. |
| 2 | Viewed one `answer_table.png`, one `table_detection.png`, one `grid.png` | image | ~4,800 | Understanding the two-block, 20-cell layout. |
| 3 | Iterative Bash experiments to find a robust column-detection method (3 rounds, incl. running against all 29 real outputs) | code | ~4,500 | Textual numeric output only, no images. |
| 4 | Wrote `cells.py`, updated `geometry.py`/`pipeline.py`/`config.py`/`utils.py`, wrote `contact_sheet.py` | code | ~4,000 | |
| 5 | Wrote `tests/test_cells.py` (8 cases) + ran pytest | code | ~2,200 | |
| 6 | Ran full pipeline against all 29 real scans (table detection + cell segmentation) | code | ~1,200 | Text console output only. |
| 7 | Viewed 1 cell-debug overlay + 2 individual cell crops | image | ~1,300 | Spot-checking one exam. |
| 8 | Viewed 3 more cell-debug overlays (edge cases: cropped number column, narrower table) | image | ~2,400 | |
| 9 | Built and viewed the 29-exam contact sheet | image | ~1,600 | One image call instead of opening 29 files individually — the token-saving payoff of the contact-sheet idea from the overview doc. |
| 10 | Wrote `docs/04_answer_cell_segmentation.md`, updated `01_project_overview.md`, `requirements-dev.txt`, committed | code | ~1,800 | |
| 11 | Discussion: token-reporting request, CLAUDE.md edit, revert, this log's creation | discussion | ~1,800 | |
| 12 | Re-added the CLAUDE.md logging instruction | discussion | ~250 | |

**Running totals:** code ≈ 22,700 · image ≈ 10,100 · discussion ≈ 2,050

## Early takeaway

For iteration 04, the code side dominates — most tokens went into writing
and iterating on the column-detection algorithm and its tests, not into
viewing images. Image inspection was used sparingly and deliberately (a
handful of representative samples plus one contact sheet), rather than the
model looking at every one of the 29 scans individually. That gap is
exactly the effect the project overview's cost theory predicts, though with
only one iteration logged this isn't yet a solid trend.

## Maintenance

Entries above were reconstructed retrospectively for iteration 04 (rough
estimates, not live measurements). Going forward, new entries will be added
per task as work happens. This file is not yet wired into a standing
CLAUDE.md rule — ask if you'd like it automated.
