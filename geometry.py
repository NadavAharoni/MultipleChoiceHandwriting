from pathlib import Path
import cv2
import numpy as np

from config import (
    HORIZONTAL_KERNEL_DIVISOR,
    MIN_LINE_KERNEL_LENGTH,
    SAVE_DEBUG_IMAGES,
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


def process_image(image_path, output_dir, intermediate_dir):
    """Produce the threshold and line-extraction diagnostics for one scan.

    Table localisation and normalisation deliberately remain later stages; this
    iteration only exposes the grid signal those stages will use.
    """
    image_path = Path(image_path)
    image = read_image(image_path)
    threshold = threshold_image(image)
    horizontal, vertical = extract_grid_lines(threshold)
    grid = cv2.bitwise_or(horizontal, vertical)

    stem = image_path.stem
    if SAVE_DEBUG_IMAGES:
        save_image(intermediate_dir / f"{stem}_threshold.png", threshold)
        save_image(intermediate_dir / f"{stem}_horizontal.png", horizontal)
        save_image(intermediate_dir / f"{stem}_vertical.png", vertical)
        save_image(intermediate_dir / f"{stem}_grid.png", grid)

    # Keep the original scan available to the following pipeline iterations.
    save_image(output_dir / f"{stem}.png", image)
