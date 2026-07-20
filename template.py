import cv2
import numpy as np

from config import TEMPLATE_DILATE_PX, TEMPLATE_FREQUENCY_THRESHOLD
from geometry import threshold_image


def build_printed_template(
    table_images: list[np.ndarray],
    dilate_px: int = TEMPLATE_DILATE_PX,
    frequency_threshold: float = TEMPLATE_FREQUENCY_THRESHOLD,
) -> np.ndarray:
    """Find the ink that is printed on every form, not handwritten.

    Every scan shares the same printed table, so a pixel that is ink in
    nearly every scan is a grid line or a printed number; handwriting
    varies scan to scan and never reaches that frequency at a fixed pixel.
    A normalized table's exact pixel position jitters a little between
    scans even after warping, so each scan's ink is dilated slightly before
    the frequency vote - otherwise a printed line that lands one pixel
    apart in two scans would count as absent from both.
    """
    if not table_images:
        raise ValueError("Need at least one table image to build a template")

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilate_px * 2 + 1, dilate_px * 2 + 1))
    accumulator = None
    for image in table_images:
        ink = threshold_image(image)
        dilated = cv2.dilate(ink, kernel)
        mask = (dilated > 0).astype(np.float32)
        accumulator = mask if accumulator is None else accumulator + mask

    frequency = accumulator / len(table_images)
    return np.where(frequency >= frequency_threshold, 255, 0).astype(np.uint8)
