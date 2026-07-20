from dataclasses import dataclass

import cv2
import numpy as np

from config import (
    CELL_GAP_MARGIN,
    CELL_INSET,
    OUTER_EDGE_BLUR_MARGIN,
    QUESTIONS_PER_BLOCK,
    ROW_GAP_MIN_INK,
    ROW_GAP_SEARCH_PX,
    TABLE_ROW_COUNT,
)
from geometry import extend_for_ink, run_centers, threshold_image


@dataclass(frozen=True)
class AnswerCell:
    """One answer cell cropped from a normalized answer table.

    The crop spans the whole cell - both the handwriting sub-column and the
    printed-number sub-column - because a few students write their answer
    next to the printed number rather than in the blank space reserved for
    it.  ``divider`` records the detected boundary between the two
    sub-columns, for a future stage that wants to mask out the printed
    number; it is informational only and is not used to bound the crop.
    """

    question: int
    left: int
    top: int
    right: int
    bottom: int
    divider: int
    image: np.ndarray


def _find_row_lines(threshold: np.ndarray) -> list[int]:
    """Find the table's eleven horizontal row lines (ten answer rows)."""
    height, width = threshold.shape
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(25, width // 20), 1))
    horizontal = cv2.morphologyEx(threshold, cv2.MORPH_OPEN, kernel)
    row_ink = np.count_nonzero(horizontal, axis=1)
    rows = run_centers(row_ink >= max(120, width // 10))
    if len(rows) != TABLE_ROW_COUNT:
        raise RuntimeError(
            f"Expected {TABLE_ROW_COUNT} row lines in the normalized table, found {len(rows)}"
        )
    return [int(round(row)) for row in rows]


def _cluster(values: list[float], tolerance: float) -> list[list[float]]:
    ordered = sorted(values)
    clusters = [[ordered[0]]]
    for value in ordered[1:]:
        if value - clusters[-1][-1] <= tolerance:
            clusters[-1].append(value)
        else:
            clusters.append([value])
    return clusters


def _find_block_lines(threshold: np.ndarray, rows: list[int]) -> tuple[list[float], list[float]]:
    """Find each block's vertical grid lines: left edge, divider, [right edge].

    A grid border is detected per row band rather than over the table's full
    height: requiring it to be visible in nearly every row is unambiguous,
    whereas requiring unbroken ink across the whole normalized image is
    fragile after the perspective warp softens the printed lines.  A false
    line formed by handwriting ink lining up across a few rows is rejected
    because, unlike a printed border, it will not be present in almost every
    row band.  The outer right edge is sometimes absent (Iteration 03b
    allows the table crop to clip the printed-number margin), so each block
    may yield two or three lines.
    """
    width = threshold.shape[1]
    row_count = len(rows) - 1
    band_height = (rows[-1] - rows[0]) / row_count
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(10, int(band_height * 0.6))))

    positions: list[float] = []
    for top, bottom in zip(rows[:-1], rows[1:]):
        band = threshold[top + 2 : bottom - 2, :]
        vertical = cv2.morphologyEx(band, cv2.MORPH_OPEN, kernel)
        column_ink = np.count_nonzero(vertical, axis=0)
        positions.extend(run_centers(column_ink >= band.shape[0] * 0.5))

    clusters = _cluster(positions, tolerance=10)
    lines = sorted(float(np.mean(cluster)) for cluster in clusters if len(cluster) >= row_count - 1)

    midpoint = width / 2
    left_block = [line for line in lines if line < midpoint]
    right_block = [line for line in lines if line >= midpoint]
    if len(left_block) < 2 or len(right_block) < 2:
        raise RuntimeError("Could not find both answer-table blocks in the normalized table")

    return left_block, right_block


def _masked_row_ink(threshold: np.ndarray, y: int, left: int, right: int, divider: int) -> int:
    """Ink count in row ``y`` across a block, ignoring its vertical grid lines."""
    row = threshold[y, left:right].copy()
    for line_x in (0, divider - left, right - left - 1):
        lo, hi = max(0, line_x - 3), min(row.shape[0], line_x + 4)
        row[lo:hi] = 0
    return int(np.count_nonzero(row))


def _find_row_gap(threshold: np.ndarray, y_center: int, left: int, right: int, divider: int) -> int:
    """Find the nearest (almost) blank row to ``y_center``, searching outward.

    ``y_center`` itself is a printed row line, so it is never blank; this
    looks just above and below it for the natural whitespace between one
    row's handwriting and the next, so a stroke that bleeds slightly across
    the line still ends up entirely inside one cell. Falls back to the
    printed line's own position if no blank row is found nearby (handwriting
    genuinely continuous across rows, with no gap to find - the cut still
    has to go somewhere, and the line's own position is the least-bad
    choice).
    """
    for offset in range(ROW_GAP_SEARCH_PX + 1):
        for y in {y_center - offset, y_center + offset}:
            if _masked_row_ink(threshold, y, left, right, divider) <= ROW_GAP_MIN_INK:
                return y
    return y_center


def _find_row_boundaries(
    threshold: np.ndarray, rows: list[int], left: int, right: int, divider: int
) -> list[int]:
    """Return the 11 y-positions bounding a block's ten answer rows.

    The outer top/bottom boundaries are pushed outward while ink continues
    past them, the same technique Iteration 03b uses to grow the whole
    table's bounds. The nine internal boundaries are instead pulled to the
    nearest blank row via `_find_row_gap`, since both of their neighbors are
    cells we also need to keep intact.
    """
    ink_ceiling = max(40, (right - left) // 2)
    # The printed line's own blur bleeds into a few adjacent rows, which
    # would otherwise immediately look like "a real border" and stop the
    # walk before it ever reaches genuine overflow further out. Starting a
    # bit past that known halo avoids mistaking the line for its own
    # stopping condition.
    height = threshold.shape[0]
    top_start = max(0, rows[0] - OUTER_EDGE_BLUR_MARGIN)
    bottom_start = min(height - 1, rows[-1] + OUTER_EDGE_BLUR_MARGIN)
    top = extend_for_ink(
        threshold, 0, (left, right), top_start, -1,
        ROW_GAP_SEARCH_PX - OUTER_EDGE_BLUR_MARGIN, ink_ceiling, ROW_GAP_MIN_INK,
    )
    bottom = extend_for_ink(
        threshold, 0, (left, right), bottom_start, 1,
        ROW_GAP_SEARCH_PX - OUTER_EDGE_BLUR_MARGIN, ink_ceiling, ROW_GAP_MIN_INK,
    )

    boundaries = [top]
    boundaries.extend(_find_row_gap(threshold, y, left, right, divider) for y in rows[1:-1])
    boundaries.append(bottom)
    return boundaries


def segment_answer_cells(table_image: np.ndarray) -> list[AnswerCell]:
    """Split a normalized answer-table image into its 20 answer cells.

    The right block (larger x) holds questions 1-10 and the left block holds
    questions 11-20, matching the printed form's layout.
    """
    threshold = threshold_image(table_image)
    width = threshold.shape[1]
    rows = _find_row_lines(threshold)
    left_lines, right_lines = _find_block_lines(threshold, rows)

    blocks = [
        (left_lines, right_lines[0] - CELL_GAP_MARGIN, QUESTIONS_PER_BLOCK + 1),
        (right_lines, width, 1),
    ]

    cells = []
    for lines, fallback_right, first_question in blocks:
        left, divider = int(round(lines[0])), int(round(lines[1]))
        right = int(round(lines[2])) if len(lines) >= 3 else int(round(fallback_right))
        boundaries = _find_row_boundaries(threshold, rows, left, right, divider)

        for index in range(QUESTIONS_PER_BLOCK):
            # Row boundaries are already precisely positioned - either the
            # first blank row found near a printed line, or the point where
            # ink stopped past the table's outer edge - so, unlike the
            # column edges below, they need no further inward correction.
            cell_top, cell_bottom = boundaries[index], boundaries[index + 1]
            cell_left = left + CELL_INSET
            cell_right = right - CELL_INSET
            cells.append(
                AnswerCell(
                    question=first_question + index,
                    left=cell_left,
                    top=cell_top,
                    right=cell_right,
                    bottom=cell_bottom,
                    divider=divider,
                    image=table_image[cell_top:cell_bottom, cell_left:cell_right],
                )
            )

    return sorted(cells, key=lambda cell: cell.question)
