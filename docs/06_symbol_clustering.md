# Iteration 06 – Symbol Clustering

**Status:** Complete (clustering only - labeling/classification is the next step)

## Objective

Per the architecture doc (`... → Cluster similar symbols per student → Identify clusters using classifier + confidence → ...`), group each cell's handwriting by shape so that later, a human (or a classifier) only has to label a handful of clusters rather than every one of the ~580 individual cells.

## Why not split into symbols first, or use a CNN?

Two directions were considered and set aside before this one:

- **Splitting each cell into individual letters/commas first.** Investigated directly: many letters are written as 2+ genuinely disconnected strokes (e.g. a vertical line plus a separate curve), which a connected-component gap threshold can't distinguish from "letter, comma, letter" - confirmed by looking at a whole-table component overlay. Whole-cell clustering sidesteps this: most cells are a single answer anyway, and multi-symbol cells naturally form their own cluster(s) rather than needing to be decomposed first.
- **A small CNN.** No labeled training data exists (that's the point of this project), and ~580 samples across a handful of classes is too little to train one from scratch without a new heavy dependency. See the discussion prior to this iteration; clustering fits the data size and the "same student writes consistently" structure the architecture doc already assumes.

## Two bugs found via this diagnostic, fixed in `handwriting.py`

Clustering directly on Iteration 05's output didn't work at all initially (KMeans produced one cluster holding >75% of all cells, visually incoherent). Tracing why surfaced two real problems in the shipped 05 output, not just a clustering-side issue:

1. **`kept_bounds` was unioned with the cell's full tight area even when real content was found**, not just in the blank-cell fallback case - so every output was padded out to the full ~480px cell width regardless of how little of it was actual ink. Fixed: the union with the tight area now only happens when nothing was kept.
2. **Leftover grid-line fragments were larger than assumed.** A residual divider/border sliver can be a substantial, elongated component (e.g. 4px wide × 53px tall, area ~177) - not the tiny few-pixel speck a generic small-noise filter assumes. Fixed with a shape+position check (`_is_line_remnant`): a component is discarded only if it's thin, tall, *and* centred on that scan's own exact known divider/edge position (`cells.py` already tracks this per scan) - not a blanket mask, so a real stroke that happens to cross the divider (Iteration 04a) survives, since it's wider than a line sliver.

A leftover printed-number fragment (05's already-documented, accepted limitation) can still remain. Rather than chase it in `handwriting.py` - which would risk reopening 04a again - clustering handles it with a minimum component area (`CLUSTER_MIN_COMPONENT_AREA = 150`, calibrated against the real dataset: noise fragments topped out well under that, real strokes well above it).

## Approach

- `clustering.extract_symbol`: keep only components above the area threshold, crop to their union, resize into a fixed 40×40 canvas, centred. Returns `None` for a blank cell (no answer detected).
- `clustering.cluster_symbols`: flatten each canvas to a feature vector, KMeans with `k` clusters (default 6 - intentionally more than 5, since the same letter in different handwriting styles, or a multi-symbol answer, land in their own clusters rather than being forced into exactly 5 "letter" groups).
- Each symbol's distance to its own cluster's centroid is returned as a confidence signal: low distance = typical of its cluster, high = worth a second look.
- `clustering.build_cluster_gallery` and the `cluster_symbols.py` CLI tile every cluster as a row, **sorted by that distance** - so within a row, the atypical members needing review land at the end instead of being buried among typical ones.

## Validation

Ran `cluster_symbols.py` against all 580 real cells (559 symbols + 21 blank). The resulting gallery is visually coherent - a `|C`-shaped letter cluster, a hook-shaped letter cluster, a multi-symbol-answer cluster, etc. - a sharp contrast to the incoherent single dominant cluster before the two bugs above were fixed.

Spot-checked against a concrete human judgment call: three cells manually identified as ג that ended up in a cluster otherwise dominated by a different letter. Two of the three ranked in the bottom 5 of 30 by distance-to-centroid (i.e. the confidence signal would have flagged them); the third ranked mid-pack and would not have been flagged. The signal is real but not complete - consistent with everything else in this pipeline that flags for review rather than claiming to resolve automatically.

## Output

- `output/clusters.csv` - one row per cell: exam, question, cluster, distance, and an empty `letter` column for the next (manual) labeling step.
- `intermediate/cluster_gallery.png` - visual review of every cluster, sorted by confidence.

Kept as a standalone script (`cluster_symbols.py`), not wired into `pipeline.py`'s automatic run: `k` is a tunable exploratory parameter and the output is a review artifact pending manual labeling, not a finished pipeline stage like table detection or cell segmentation.

## Tests

`tests/test_clustering.py`: `extract_symbol` ignores small noise and keeps real strokes, returns `None` for a blank cell, and spans multiple components for a multi-symbol answer; `cluster_symbols` separates two visually distinct synthetic shape groups, gives a shape outlier a higher distance than its group's typical members, and raises when there are fewer symbols than `k`.

## Notes / Next Step

Clustering only groups by shape - it doesn't know which letter a cluster represents. The next step is labeling: fill in `clusters.csv`'s `letter` column per cluster (not per cell), then reassemble each question's answer from its cell's label, handling multi-symbol cells as multiple letters. Cells whose distance is an outlier within their cluster should be surfaced for a second look rather than trusted at face value.
