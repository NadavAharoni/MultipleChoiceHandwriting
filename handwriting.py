from dataclasses import dataclass

import cv2
import numpy as np

from cells import AnswerCell
from config import (
    HANDWRITING_COLUMN_PAD_PX,
    HANDWRITING_CONNECTIVITY,
    HANDWRITING_MULTI_ROW_FLAG_RATIO,
    HANDWRITING_ROW_PAD_PX,
    TABLE_HEIGHT,
    TABLE_ROW_COUNT,
)
from geometry import threshold_image

NOMINAL_ROW_HEIGHT = TABLE_HEIGHT / (TABLE_ROW_COUNT - 1)


@dataclass(frozen=True)
class Handwriting:
    """A cell's handwriting, isolated from the printed form around it.

    ``image`` is white with black ink, cropped tightly to the handwriting
    that was attributed to this question - which may extend beyond the
    cell's own tight bounds when a stroke was found to belong here despite
    poking past the boundary (see `extract_cell_handwriting`).
    """

    question: int
    image: np.ndarray
    spans_multiple_rows: bool


def _padded_region(cell: AnswerCell, shape: tuple[int, int]) -> tuple[int, int, int, int]:
    height, width = shape
    top = max(0, cell.top - HANDWRITING_ROW_PAD_PX)
    bottom = min(height, cell.bottom + HANDWRITING_ROW_PAD_PX)
    left = max(0, cell.left - HANDWRITING_COLUMN_PAD_PX)
    right = min(width, cell.right + HANDWRITING_COLUMN_PAD_PX)
    return top, left, bottom, right


def extract_cell_handwriting(
    table_image: np.ndarray, template: np.ndarray, cell: AnswerCell
) -> Handwriting:
    """Isolate one cell's handwriting, reattaching strokes cropped at its edge.

    A cell's tight bounds (from `cells.segment_answer_cells`) are only a
    starting point: a stroke can legitimately extend past them. This looks
    for connected ink components in a padded region around the cell,
    keeping only those whose centroid falls inside the cell's own tight
    bounds - a component centred in a neighboring cell is left for that
    cell's own search to find instead, so nothing is claimed twice.
    """
    threshold = threshold_image(table_image)
    handwriting_ink = cv2.bitwise_and(threshold, cv2.bitwise_not(template))

    top, left, bottom, right = _padded_region(cell, threshold.shape)
    region = handwriting_ink[top:bottom, left:right]
    component_count, labels = cv2.connectedComponents(region, connectivity=HANDWRITING_CONNECTIVITY)

    kept_mask = np.zeros_like(region)
    kept_bounds = None
    spans_multiple_rows = False

    for label in range(1, component_count):
        rows, columns = np.nonzero(labels == label)
        centroid_y, centroid_x = rows.mean() + top, columns.mean() + left
        if not (cell.top <= centroid_y < cell.bottom and cell.left <= centroid_x < cell.right):
            continue

        kept_mask[labels == label] = 255
        bounds = (rows.min(), columns.min(), rows.max(), columns.max())
        kept_bounds = bounds if kept_bounds is None else (
            min(kept_bounds[0], bounds[0]),
            min(kept_bounds[1], bounds[1]),
            max(kept_bounds[2], bounds[2]),
            max(kept_bounds[3], bounds[3]),
        )
        if bounds[2] - bounds[0] > NOMINAL_ROW_HEIGHT * HANDWRITING_MULTI_ROW_FLAG_RATIO:
            spans_multiple_rows = True

    # A blank cell has no components to bound; fall back to its own tight
    # area rather than producing a zero-sized image.
    tight_bounds = (cell.top - top, cell.left - left, cell.bottom - top - 1, cell.right - left - 1)
    if kept_bounds is None:
        kept_bounds = tight_bounds
    else:
        kept_bounds = (
            min(kept_bounds[0], tight_bounds[0]),
            min(kept_bounds[1], tight_bounds[1]),
            max(kept_bounds[2], tight_bounds[2]),
            max(kept_bounds[3], tight_bounds[3]),
        )

    y0, x0, y1, x1 = kept_bounds
    canvas = np.full((y1 - y0 + 1, x1 - x0 + 1), 255, dtype=np.uint8)
    canvas[kept_mask[y0 : y1 + 1, x0 : x1 + 1] > 0] = 0

    return Handwriting(question=cell.question, image=canvas, spans_multiple_rows=spans_multiple_rows)


def extract_handwriting(table_image: np.ndarray, template: np.ndarray, cells: list[AnswerCell]) -> list[Handwriting]:
    """Extract handwriting for every cell in a normalized answer table."""
    return [extract_cell_handwriting(table_image, template, cell) for cell in cells]
