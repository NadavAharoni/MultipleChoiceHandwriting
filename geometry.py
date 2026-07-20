from pathlib import Path
import cv2
import numpy as np

from config import (
    HORIZONTAL_KERNEL_DIVISOR,
    MIN_LINE_KERNEL_LENGTH,
    SAVE_DEBUG_IMAGES,
    TABLE_HEIGHT,
    TABLE_ASPECT_RATIO,
    TABLE_ROW_COUNT,
    TABLE_WIDTH,
    VERTICAL_KERNEL_DIVISOR,
)
from utils import save_image


def read_image(image_path: Path) -> np.ndarray:
    """Read an image without assuming its filename is ASCII-only."""
    data = np.fromfile(str(image_path), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"Cannot read image: {image_path}")
    return image


def threshold_image(image: np.ndarray) -> np.ndarray:
    """Return a binary image whose foreground contains ink and grid lines."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    return cv2.adaptiveThreshold(
        blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31,
        15,
    )


def extract_grid_lines(threshold: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Extract long horizontal and vertical structures from a binary image."""
    height, width = threshold.shape
    horizontal_length = max(MIN_LINE_KERNEL_LENGTH, width // HORIZONTAL_KERNEL_DIVISOR)
    vertical_length = max(MIN_LINE_KERNEL_LENGTH, height // VERTICAL_KERNEL_DIVISOR)

    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_length, 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, vertical_length))

    horizontal = cv2.morphologyEx(threshold, cv2.MORPH_OPEN, horizontal_kernel)
    vertical = cv2.morphologyEx(threshold, cv2.MORPH_OPEN, vertical_kernel)
    return horizontal, vertical


def _run_centers(values: np.ndarray, bridge_gap: int = 3) -> list[float]:
    """Return the centres of contiguous true runs in a one-dimensional mask.

    A grid line that is slightly rotated or thinned by morphology can dip
    below the ink threshold for a pixel or two, splitting one line into two
    candidates.  Short gaps like that are bridged first so each real grid
    line yields a single, correctly centred run.
    """
    padded = np.pad(values.astype(np.int8), (1, 1))
    starts = np.flatnonzero(np.diff(padded) == 1)
    ends = np.flatnonzero(np.diff(padded) == -1)
    bridged = values.copy()
    for previous_end, next_start in zip(ends[:-1], starts[1:]):
        if next_start - previous_end <= bridge_gap:
            bridged[previous_end:next_start] = True

    padded = np.pad(bridged.astype(np.int8), (1, 1))
    starts = np.flatnonzero(np.diff(padded) == 1)
    ends = np.flatnonzero(np.diff(padded) == -1)
    return [float((start + end - 1) / 2) for start, end in zip(starts, ends)]


def _nearest_row(rows: list[float], target: float, tolerance: float) -> float | None:
    candidates = [row for row in rows if abs(row - target) <= tolerance]
    return min(candidates, key=lambda row: abs(row - target), default=None)


def _select_table_columns(
    horizontal_left: int,
    horizontal_right: int,
    vertical_columns: list[float],
    table_height: int,
) -> tuple[int, int]:
    """Choose table edges that match the known form's grid and aspect ratio."""
    candidates = sorted({horizontal_left, horizontal_right, *(round(column) for column in vertical_columns)})
    selections = []
    for index, left in enumerate(candidates):
        for right in candidates[index + 1 :]:
            ratio = (right - left) / table_height
            if not 1.7 <= ratio <= 2.5:
                continue
            support = sum(left - 3 <= column <= right + 3 for column in vertical_columns)
            # The actual form has six strong vertical grid lines.  Prefer a
            # candidate enclosing those lines, then its expected aspect ratio.
            score = support * 10 - abs(ratio - TABLE_ASPECT_RATIO)
            selections.append((score, left, right))

    if selections:
        _, left, right = max(selections)
        return int(left), int(right)

    # Retain a useful fallback for badly occluded scans, rather than silently
    # selecting a page border simply because it is the outermost vertical line.
    expected_width = round(table_height * TABLE_ASPECT_RATIO)
    return horizontal_left, min(horizontal_right, horizontal_left + expected_width)


def _extend_for_ink(
    threshold: np.ndarray,
    axis: int,
    span: tuple[int, int],
    edge: int,
    direction: int,
    max_extend: int,
    ink_ceiling: int,
    min_ink: int = 5,
) -> int:
    """Push a table edge outward while handwriting ink continues past it.

    Students do not confine their handwriting to the printed grid line, so
    the strict line-based edge can clip a stroke that overruns it.  This
    walks outward one pixel at a time and stops as soon as it meets either
    blank page (no more ink) or something with a printed-line's worth of
    ink (a real border or unrelated rule), so only genuine handwriting
    overflow gets included.
    """
    lo, hi = span
    limit = threshold.shape[axis]
    extended = edge
    for offset in range(1, max_extend + 1):
        probe = edge + offset * direction
        if probe < 0 or probe >= limit:
            break
        line = threshold[probe, lo:hi] if axis == 0 else threshold[lo:hi, probe]
        count = np.count_nonzero(line)
        if count >= ink_ceiling or count < min_ink:
            break
        extended = probe
    return extended


def find_table_bounds(
    threshold: np.ndarray, horizontal: np.ndarray, vertical: np.ndarray
) -> tuple[int, int, int, int]:
    """Find the table using its eleven nearly equally spaced horizontal lines."""
    height, width = horizontal.shape
    row_ink = np.count_nonzero(horizontal, axis=1)
    # A table row spans both answer blocks, whereas ordinary printed text does
    # not survive horizontal morphology over this much of the page.
    candidate_rows = _run_centers(row_ink >= max(120, width // 10))

    best_rows: list[float] | None = None
    best_score = -1
    for start_index, first in enumerate(candidate_rows):
        for second in candidate_rows[start_index + 1 :]:
            spacing = second - first
            if not 15 <= spacing <= max(100, height // 12):
                continue

            matched = []
            for index in range(TABLE_ROW_COUNT):
                row = _nearest_row(candidate_rows, first + index * spacing, spacing * 0.28)
                if row is not None:
                    matched.append(row)

            # The line support breaks ties between similarly regular form rows.
            support = sum(row_ink[round(row)] for row in matched)
            score = len(matched) * 1_000_000 + support
            if len(matched) >= TABLE_ROW_COUNT - 1 and score > best_score:
                best_rows = matched
                best_score = score

    if best_rows is None:
        raise RuntimeError("Could not find the regular 11-row answer table")

    top = int(round(min(best_rows)))
    bottom = int(round(max(best_rows)))
    line_bands = horizontal[max(0, top - 3) : min(height, bottom + 4)]
    column_ink = np.count_nonzero(line_bands, axis=0)
    candidate_columns = np.flatnonzero(column_ink >= max(2, len(best_rows) // 3))
    if candidate_columns.size == 0:
        raise RuntimeError("Could not find the answer table columns")

    # The median row endpoints reject isolated horizontal artefacts near the
    # table while retaining the full width of both answer blocks.
    row_endpoints = []
    for row in best_rows:
        points = np.flatnonzero(horizontal[round(row)])
        if points.size:
            row_endpoints.append((int(points.min()), int(points.max())))
    if len(row_endpoints) < TABLE_ROW_COUNT - 1:
        raise RuntimeError("The detected table has too few complete row lines")

    left = int(np.median([start for start, _ in row_endpoints]))
    right = int(np.median([end for _, end in row_endpoints]))

    # Horizontal lines can end just before a handwritten or coloured outer
    # border.  A vertical line extending through most rows is a more reliable
    # source for the true left and right edges.
    column_ink = np.count_nonzero(vertical[top : bottom + 1], axis=0)
    vertical_columns = _run_centers(column_ink >= (bottom - top + 1) * 0.5)
    left, right = _select_table_columns(left, right, vertical_columns, bottom - top + 1)

    # If the selected left edge is a full answer-cell width before the first
    # detected vertical grid line, it is the left number-column boundary, not
    # the table edge.  Shift the fixed-width crop left to retain the handwritten
    # cell; sacrificing a little of the far-right question-number margin is
    # preferable to clipping handwriting.
    in_table_columns = [column for column in vertical_columns if left <= column <= right]
    if in_table_columns:
        missing_answer_width = int(round(min(in_table_columns))) - left
        unused_right_margin = right - int(np.median([end for _, end in row_endpoints]))
        if missing_answer_width > (bottom - top) * 0.3 and unused_right_margin > missing_answer_width:
            left -= missing_answer_width
            right -= missing_answer_width

    # Grow top, bottom, and left to include handwriting that overruns the
    # printed grid line.  The right edge is left alone: it borders the
    # printed question numbers, and cropping into those is acceptable, but
    # growing it risks pulling in unrelated page content.
    row_height = (bottom - top) / (TABLE_ROW_COUNT - 1)
    line_ceiling = max(120, (right - left) // 2)
    top = _extend_for_ink(threshold, 0, (left, right), top, -1, round(row_height), line_ceiling)
    bottom = _extend_for_ink(threshold, 0, (left, right), bottom, 1, round(row_height), line_ceiling)
    left = _extend_for_ink(threshold, 1, (top, bottom), left, -1, round(row_height), line_ceiling)

    margin = 3
    return (
        max(0, left - margin),
        max(0, top - margin),
        min(width - 1, right + margin),
        min(height - 1, bottom + margin),
    )


def estimate_skew_angle(threshold: np.ndarray) -> float:
    """Estimate small page rotation from long near-horizontal printed lines."""
    height, width = threshold.shape
    lines = cv2.HoughLinesP(
        threshold,
        1,
        np.pi / 360,
        threshold=80,
        minLineLength=max(100, width // 6),
        maxLineGap=25,
    )
    if lines is None:
        return 0.0
    angles = []
    for x1, y1, x2, y2 in lines[:, 0]:
        angle = float(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
        if abs(angle) <= 8:
            angles.append(angle)
    return float(np.median(angles)) if angles else 0.0


def rotate_image(image: np.ndarray, angle: float) -> tuple[np.ndarray, np.ndarray]:
    """Deskew an image, retaining a transform from original to deskewed pixels."""
    height, width = image.shape[:2]
    center = (width / 2, height / 2)
    # OpenCV's image coordinates have y pointing down, so the measured line
    # angle is applied directly to make it horizontal.
    transform = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(image, transform, (width, height), borderValue=(255, 255, 255)), transform


def normalize_table(image: np.ndarray, bounds: tuple[int, int, int, int]) -> tuple[np.ndarray, np.ndarray]:
    """Warp a detected table rectangle into the fixed downstream coordinate system."""
    left, top, right, bottom = bounds
    source = np.float32([[left, top], [right, top], [right, bottom], [left, bottom]])
    destination = np.float32(
        [[0, 0], [TABLE_WIDTH - 1, 0], [TABLE_WIDTH - 1, TABLE_HEIGHT - 1], [0, TABLE_HEIGHT - 1]]
    )
    transform = cv2.getPerspectiveTransform(source, destination)
    return cv2.warpPerspective(image, transform, (TABLE_WIDTH, TABLE_HEIGHT)), source


def process_image(image_path, output_dir, intermediate_dir):
    """Locate, deskew, and normalize the answer table from one scanned page."""
    image_path = Path(image_path)
    image = read_image(image_path)
    initial_threshold = threshold_image(image)
    angle = estimate_skew_angle(initial_threshold)
    deskewed, rotation = rotate_image(image, angle)
    threshold = threshold_image(deskewed)
    horizontal, vertical = extract_grid_lines(threshold)
    grid = cv2.bitwise_or(horizontal, vertical)
    bounds = find_table_bounds(threshold, horizontal, vertical)
    answer_table, table_corners = normalize_table(deskewed, bounds)

    stem = image_path.stem
    if SAVE_DEBUG_IMAGES:
        save_image(intermediate_dir / f"{stem}_threshold.png", threshold)
        save_image(intermediate_dir / f"{stem}_horizontal.png", horizontal)
        save_image(intermediate_dir / f"{stem}_vertical.png", vertical)
        save_image(intermediate_dir / f"{stem}_grid.png", grid)
        overlay = image.copy()
        inverse_rotation = cv2.invertAffineTransform(rotation)
        original_corners = cv2.transform(table_corners[None, :, :], inverse_rotation)[0].astype(np.int32)
        cv2.polylines(overlay, [original_corners], True, (0, 255, 0), 5)
        save_image(intermediate_dir / f"{stem}_table_detection.png", overlay)

    save_image(output_dir / f"{stem}_answer_table.png", answer_table)
