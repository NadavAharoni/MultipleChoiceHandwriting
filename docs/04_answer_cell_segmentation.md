# Iteration 04 – Answer Cell Segmentation

**Status:** Complete

## Objective

Split each normalized `answer_table.png` into its 20 individual handwritten
answer cells, ready for handwriting recognition.

## Approach

The normalized table image still contains the printed grid lines, so this
stage locates them directly rather than assuming fixed pixel coordinates:

- The eleven horizontal row lines are found the same way as in the table
  detection stage (long-run morphology + `run_centers`).
- Each block's left edge and answer/number divider are found by detecting
  vertical borders **per row band** (ten independent ~59px-tall strips)
  and keeping only the x-positions supported by nearly every row.
  Requiring near-full support across all ten rows — rather than one
  unbroken vertical run spanning the whole table — turned out to be the key
  reliability fix: after the perspective warp, printed borders are no longer
  perfectly continuous, while a stray handwriting stroke that happens to
  line up vertically only ever does so in a handful of rows.
- The outer right edge of the number column is not required: several scans
  crop it during table detection (acceptable per Iteration 03b), and it
  is not needed to bound the handwriting cell anyway.
- The right block (larger x) holds questions 1-10, the left block holds
  questions 11-20, matching the printed form.

See [`cells.py`](../cells.py).

## Debug Output

- `intermediate/<stem>_cells.png` — the normalized table with each detected
  cell boxed and labelled with its question number.
- `output/cells/<stem>/q<NN>.png` — the cropped handwriting cell for each
  question.
- `contact_sheet.py` tiles any set of debug images (e.g. all `*_cells.png`)
  into one image for quick human review, per the project overview's
  suggestion.

## Validation

Ran against the complete dataset (29 scans):

- Total scans processed: 29
- Successful: 29
- Failed: 0

Every scan produced all 20 labelled cells, correctly ordered (1-10 on the
right block top-to-bottom, 11-20 on the left block top-to-bottom). Visual
review via the cells contact sheet did not show any clipped handwriting.

## Tests

`tests/test_cells.py` exercises the segmentation logic against synthetic
tables (no dependency on the real scans), covering: normal segmentation,
question numbering/ordering, a missing outer number-column edge, a
handwriting stroke that mimics a vertical grid line, and a missing row line
raising an error.

## Notes

Cell boundaries are the printed grid lines with a small fixed inward inset;
there is no ink-based overflow extension at the cell level (unlike the
table-level bounds in Iteration 03b). None of the 29 scans showed clipped
handwriting in review, so this was not added. If future recognition work
finds clipped strokes at cell edges, revisit with the same overflow-into-ink
technique used for the outer table bounds.
