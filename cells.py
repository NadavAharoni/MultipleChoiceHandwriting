from dataclasses import dataclass

import cv2
import numpy as np

from config import CELL_GAP_MARGIN, CELL_INSET, QUESTIONS_PER_BLOCK, TABLE_ROW_COUNT
from geometry import run_centers, threshold_image


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
        left, divider = lines[0], lines[1]
        right = lines[2] if len(lines) >= 3 else fallback_right
        for index in range(QUESTIONS_PER_BLOCK):
            top, bottom = rows[index], rows[index + 1]
            cell_left = int(round(left)) + CELL_INSET
            cell_top = top + CELL_INSET
            cell_right = int(round(right)) - CELL_INSET
            cell_bottom = bottom - CELL_INSET
            cells.append(
                AnswerCell(
                    question=first_question + index,
                    left=cell_left,
                    top=cell_top,
                    right=cell_right,
                    bottom=cell_bottom,
                    divider=int(round(divider)),
                    image=table_image[cell_top:cell_bottom, cell_left:cell_right],
                )
            )

    return sorted(cells, key=lambda cell: cell.question)
