# Iteration 04b – Row-Boundary Overflow

**Status:** Complete (partial - see Notes)

## Objective

Fix a second gap found via the `*_cells.png` contact sheet: in
`325573509_D3241J`, handwriting bleeds *vertically* across row lines and
even past the table's own outer border, unlike Iteration 04a's horizontal
(column) issue.

## Approach

`cells.py` now computes each block's row boundaries adaptively instead of
using the raw printed line position directly:

- The 9 internal boundaries are pulled to the nearest (almost) blank row
  found within a small search window (`_find_row_gap`), so a stroke that
  bleeds a few pixels past a line still ends up entirely inside one cell.
  Falls back to the line's own position if no blank row exists nearby.
- The outer top/bottom boundaries are pushed outward while ink continues
  past them (reusing `geometry.extend_for_ink`, made public - the same
  technique Iteration 03b uses for the whole table's bounds), so an
  ascender/descender that pokes past the table's own border is still
  captured.
- Both searches start a few pixels past the printed line's own position
  (`OUTER_EDGE_BLUR_MARGIN`) rather than immediately adjacent to it: at this
  image size, a printed line's blur bleeds into a couple of rows on either
  side, which otherwise reads as "hit a real border" and stops the search
  immediately, before it ever reaches genuine overflow further out.
- What counts as "blank" (`ROW_GAP_MIN_INK`) is calibrated from the actual
  dataset (measured across all 29 scans) rather than guessed, because scan
  noise varies enough between scans that a low, seemingly-safe threshold
  produced false positives on some scans while a real gap on the worst
  scan reads about the same as noise on others.

See [`cells.py`](../cells.py).

## What Was Dropped: Automatic Overflow Flagging

The plan for this iteration also included flagging cells where the
boundary search couldn't find a genuine gap, so they could be listed for
manual review instead of guessing. This was implemented, then removed
after validation showed it doesn't work: three different signals were
tried (absolute ink threshold, ink relative to that row's own peak content,
per-cell ink-density outlier detection), and none reliably separated
`325573509`'s genuinely unsegmentable connected cursive from ordinary scan
noise on other, visually clean scans. Depending on calibration the flag
either fired on ~25% of all cells across the dataset or none at all, with
no usable middle ground - the thin connecting strokes in the one
problem case read numerically the same as background noise elsewhere.

A false "all clear" would be worse than no signal at all. Catching cases
like this is left to the existing contact-sheet visual review (the
`*_cells.png` overlay + `contact_sheet.py`), which is how this issue and
Iteration 04a's were both actually found.

## Validation

Re-ran against all 29 scans: 29/29 succeeded, no regressions in the
`*_cells.png` contact sheet review. `325573509`'s row 20 box now extends
several pixels further down (into where a dangling stroke below the
table's printed border previously went uncaptured), though the exam's
fundamentally connected cursive style still can't be cleanly separated
per-question - see Notes.

## Tests

`tests/test_cells.py` adds: a boundary shifting to a genuine nearby gap
when ink bleeds slightly past a line, a graceful fallback to the line's own
position when no gap exists nearby (no crash), and outer-edge extension
capturing ink that overflows above the table's own border. Existing tests'
synthetic ink strokes were widened (`STROKE_WIDTH = 30`) - a thinner
synthetic stroke reads numerically close to the calibrated noise floor and
isn't representative of real handwriting ink density at this image size.

## Notes

`325573509` remains only partially fixed. Its handwriting is written as
one continuous connected script per block, with no blank row anywhere near
several internal boundaries even after this fix - there is no correct
automatic row-by-row split for that exam. This is consistent with the
project overview's acceptance that some manual intervention is fine; this
scan should be flagged for manual answer entry rather than solved
geometrically.
