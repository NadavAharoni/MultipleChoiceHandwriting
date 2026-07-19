from pathlib import Path
import cv2
import numpy as np

from config import (
    HORIZONTAL_KERNEL_DIVISOR,
    MIN_LINE_KERNEL_LENGTH,
    SAVE_DEBUG_IMAGES,
    TABLE_HEIGHT,
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


def _run_centers(values: np.ndarray) -> list[float]:
    """Return the centres of contiguous true runs in a one-dimensional mask."""
    padded = np.pad(values.astype(np.int8), (1, 1))
    starts = np.flatnonzero(np.diff(padded) == 1)
    ends = np.flatnonzero(np.diff(padded) == -1)
    return [float((start + end - 1) / 2) for start, end in zip(starts, ends)]


def _nearest_row(rows: list[float], target: float, tolerance: float) -> float | None:
    candidates = [row for row in rows if abs(row - target) <= tolerance]
    return min(candidates, key=lambda row: abs(row - target), default=None)


def find_table_bounds(horizontal: np.ndarray, vertical: np.ndarray) -> tuple[int, int, int, int]:
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
    if len(vertical_columns) >= 2:
        left = min(left, int(round(min(vertical_columns))))
        right = max(right, int(round(max(vertical_columns))))
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
    bounds = find_table_bounds(horizontal, vertical)
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
