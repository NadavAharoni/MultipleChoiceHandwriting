# Iteration 05 – Handwriting Extraction

**Status:** Complete

## Objective

Per the architecture doc's pipeline (`... → Extract answer cells → Remove
printed grid → Threshold & clean handwriting → ...`), isolate each cell's
handwritten ink from the printed form around it, producing a clean image
per question ready for symbol splitting and recognition.

This also addresses a limitation raised after Iteration 04b: a cell's tight
bounding box is only a starting point, not guaranteed to contain the whole
answer. A stroke that pokes past it should still be attributed to the
right question wherever possible.

## Approach

### Printed-content template ([`template.py`](../template.py))

Every scan shares the same printed form, so a pixel that is ink in nearly
every scan is a grid line or a printed number - handwriting varies scan to
scan and essentially never reaches that frequency at a fixed pixel. This
sidesteps needing to know what a grid line or a digit glyph looks like at
all; it's discovered directly from the corpus:

- Threshold every processed table, dilate each by a few pixels (a
  normalized table's exact pixel position still jitters a little between
  scans even after warping - measured directly against the dataset), and
  accumulate.
- A pixel present in at least 75% of scans is called printed. Visually
  confirmed against the dataset: this cleanly separates crisp, fully-formed
  grid lines and numbers from the faint "ghost" that handwriting leaves
  behind, even in the areas most students happen to write in.
- Because it's frequency-based rather than a fixed region, it also solves
  Iteration 04a's number-column problem for free: a student's ink in that
  sub-column varies in position across scans, so it never reaches the
  template's frequency, and it survives.
- `build_template.py` runs this once, over every `answer_table.png`;
  `pipeline.py` does the same internally before processing any cell.

### Attributing ink to a cell ([`handwriting.py`](../handwriting.py))

- Subtract the (dilated) template from a cell's thresholded ink to get
  candidate handwriting.
- Find connected components in a small padded region around the cell's
  tight bounds (from `cells.segment_answer_cells`), not just within the
  tight bounds themselves - otherwise a component that legitimately
  belongs to this cell but pokes past its edge would be cut at exactly the
  boundary being worked around.
- Keep a component only if its centroid falls inside the cell's own tight
  bounds. A component centred in a neighboring cell is left for that
  cell's own search to claim instead, so nothing is attributed twice.
- The output image is cropped to the union of all kept components (which
  may extend past the tight bounds) and the tight bounds themselves (so a
  blank cell still produces a sensibly sized white image, not a zero-size
  one).

### Padding and connectivity were miscalibrated on the first pass

An initial version used generous padding (18px) and 8-connectivity,
expecting to mostly need it for genuine overflow. Running against all 29
scans instead produced 70/580 cells flagged as spanning multiple rows -
almost entirely on scans already known to be clean. Removing a row's grid
line removes the barrier that kept adjacent rows' ink from ever touching;
with generous padding and diagonal connectivity, two unrelated rows'
ordinary bold handwriting merged into one component far more often than a
genuine overflow was caught.

Cut padding to 8px and switched to 4-connectivity: cells.py's own row
boundaries are already adjusted toward genuine ink gaps (Iteration 04b), so
this padding only needs to be a secondary safety margin, not the primary
defense against clipping. Re-running against all 29 scans dropped this to
1/580 flagged cells - and that one is in `325573509_D3241J`, the scan
already known (04b) to be genuinely unsegmentable in places.

## Debug Output

- `output/handwriting/<stem>/q<NN>.png` - each question's isolated
  handwriting.
- `intermediate/printed_template.png` - the learned printed-content mask.
- `intermediate/<stem>_cells.png` - now also outlines a cell in orange
  instead of red when its handwriting spans multiple rows.

## Validation

Ran the full pipeline against all 29 scans: 29/29 succeeded. Reviewed the
`*_cells.png` contact sheet (no regressions) and a sample of
`output/handwriting/*/q*.png` across three scans - grid and printed
numbers are removed while handwriting stays fully legible, matching the
result manually verified in `docs/04b_row_boundary_overflow.md`'s "dropped
feature" discussion but now working because it uses shape/topology
(connected components) rather than an ink-density threshold.

## Tests

`tests/test_template.py`: the template correctly recovers printed content
shared across synthetic scans while excluding per-scan-varying handwriting.

`tests/test_handwriting.py`: printed ink removed while handwriting is kept;
a component overflowing a cell's tight bounds by less than the padding is
fully reattached; a component centred in the neighboring cell is not
claimed; a component taller than the row-height threshold is flagged;
a blank cell returns a correctly-sized blank image.

## Notes

- The template doesn't fully remove the printed number on a handful of
  scans whose crop geometry deviates more than usual from the corpus
  norm (the same few scans already flagged elsewhere for unusual table
  bounds). The leftover glyph is visually distinct from handwritten Hebrew
  letters, so it's left as a known, minor limitation rather than chased
  further via a per-scan-specific mask - a targeted digit mask depending on
  the scan's own `divider`/right-edge would reopen exactly the
  region-exclusion bug fixed in Iteration 04a.
- `spans_multiple_rows` is intentionally conservative after the
  recalibration above; it exists to flag cells worth a manual look, not to
  guarantee catching every imperfect split.
