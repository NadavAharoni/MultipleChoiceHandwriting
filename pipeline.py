import argparse
from pathlib import Path

import cv2

from cells import segment_answer_cells
from config import INTERMEDIATE_DIR, OUTPUT_DIR, SAVE_DEBUG_IMAGES
from geometry import locate_answer_table
from utils import ensure_dir, save_image


def _save_cell_debug_overlay(stem, answer_table, cells, intermediate_dir):
    overlay = answer_table.copy()
    for cell in cells:
        cv2.rectangle(overlay, (cell.left, cell.top), (cell.right, cell.bottom), (0, 0, 255), 2)
        cv2.line(overlay, (cell.divider, cell.top), (cell.divider, cell.bottom), (0, 200, 255), 1)
        cv2.putText(
            overlay,
            str(cell.question),
            (cell.left + 4, cell.top + 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2,
        )
    save_image(intermediate_dir / f"{stem}_cells.png", overlay)


def process_image(image_path, output_dir, intermediate_dir):
    """Locate the answer table on one scan and segment its answer cells."""
    stem, answer_table = locate_answer_table(image_path, output_dir, intermediate_dir)

    cells = segment_answer_cells(answer_table)

    cells_dir = output_dir / "cells" / stem
    for cell in cells:
        save_image(cells_dir / f"q{cell.question:02d}.png", cell.image)

    if SAVE_DEBUG_IMAGES:
        _save_cell_debug_overlay(stem, answer_table, cells, intermediate_dir)

    return cells


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "images",
        nargs="+",
        help="Input images"
    )

    args = parser.parse_args()

    ensure_dir(OUTPUT_DIR)
    ensure_dir(INTERMEDIATE_DIR)

    ok = 0
    failed = 0

    for filename in args.images:

        try:
            print(f"Processing {filename}")

            process_image(
                Path(filename),
                OUTPUT_DIR,
                INTERMEDIATE_DIR
            )

            ok += 1

        except Exception as ex:

            print(f"FAILED: {filename}")
            print(ex)

            failed += 1

    print()
    print("===================================")
    print(f"Successful : {ok}")
    print(f"Failed     : {failed}")


if __name__ == "__main__":
    main()
