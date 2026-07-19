from pathlib import Path

import cv2
import numpy as np

from utils import save_image


def largest_contour(contours):

    if len(contours) == 0:
        return None

    return max(contours, key=cv2.contourArea)


def process_image(image_path, output_dir, intermediate_dir):

    image = cv2.imread(str(image_path))

    if image is None:
        raise Exception("Cannot read image")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    thresh = cv2.adaptiveThreshold(
        blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31,
        15,
    )

    contours, _ = cv2.findContours(
        thresh,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    drawing = image.copy()

    if contours:

        biggest = largest_contour(contours)

        cv2.drawContours(
            drawing,
            [biggest],
            -1,
            (0, 255, 0),
            5,
        )

    stem = image_path.stem

    save_image(
        intermediate_dir / f"{stem}_threshold.png",
        thresh,
    )

    save_image(
        intermediate_dir / f"{stem}_contours.png",
        drawing,
    )

    save_image(
        output_dir / f"{stem}.png",
        image,
    )
    