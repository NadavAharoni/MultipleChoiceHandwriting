# Iteration 04a – Full-Width Answer Cells

**Status:** Complete

## Objective

Fix a cell-segmentation gap found during manual review: a few students
wrote their answer next to the printed number instead of in the blank
handwriting sub-column reserved for it, so the cropped cell was blank.

Found by reviewing the `*_cells.png` contact sheet. Affected at least
`324974302_D3241J` and `325573509_D3241J`; roughly 2-3 of 29 scans.

## Root Cause

Iteration 04 split each cell at the printed answer/number divider and kept
only the handwriting sub-column, assuming the student's ink was always
there. It sometimes isn't.

## Fix

`segment_answer_cells` now crops the **whole cell** (left edge to right
edge, both sub-columns) instead of stopping at the divider. This matches
the pipeline described in `Handwritten_Answer_Recognition_Architecture.md`
(`Extract answer cells → Remove printed grid → ...`), where a later stage
is expected to strip printed content from the raw cell — splitting off the
number sub-column in Iteration 04 was premature. The divider's x-position
is still detected and kept on `AnswerCell.divider` as metadata, for that
future printed-number-masking stage.

The right edge of a block is still sometimes missing (03b allows the outer
number-column border to be cropped). When absent, the cell now falls back
to either the table's own right edge (outer/right block) or a small margin
before the other block's left edge (left block), instead of failing.

See [`cells.py`](../cells.py).

## Validation

Re-ran against all 29 scans: 29/29 succeeded. Both flagged exams now show
their handwriting fully inside the boxed cell in the debug overlay.
Reviewed the full `*_cells.png` contact sheet again; no regressions in the
other 27 scans.

## Tests

Added to `tests/test_cells.py`:

- A cell now spans past the divider to (near) the block's outer edge.
- A direct regression test placing ink only in the number sub-column and
  asserting it is captured.
- The missing-outer-edge fallback now also asserts the cell still reaches
  well past the divider.
