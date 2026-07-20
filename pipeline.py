import argparse
from pathlib import Path

import cv2

from cells import segment_answer_cells
from config import INTERMEDIATE_DIR, OUTPUT_DIR, SAVE_DEBUG_IMAGES, TEMPLATE_PATH
from geometry import locate_answer_table
from handwriting import extract_handwriting
from template import build_printed_template
from utils import ensure_dir, save_image


def _save_cell_debug_overlay(stem, answer_table, cells, handwriting, intermediate_dir):
    overlay = answer_table.copy()
    flagged = {item.question for item in handwriting if item.spans_multiple_rows}
    for cell in cells:
        color = (0, 140, 255) if cell.question in flagged else (0, 0, 255)
        cv2.rectangle(overlay, (cell.left, cell.top), (cell.right, cell.bottom), color, 2)
        cv2.line(overlay, (cell.divider, cell.top), (cell.divider, cell.bottom), (0, 200, 255), 1)
        cv2.putText(
            overlay,
            str(cell.question),
            (cell.left + 4, cell.top + 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
        )
    save_image(intermediate_dir / f"{stem}_cells.png", overlay)


def locate_tables(image_paths, output_dir, intermediate_dir):
    """Stage 1: locate and normalize the answer table on every scan.

    Runs first, and separately from cell segmentation, because building the
    printed-content template needs every table before any cell can be
    processed.
    """
    tables = {}
    failures = []
    for image_path in image_paths:
        print(f"Locating table: {image_path}")
        try:
            stem, answer_table = locate_answer_table(Path(image_path), output_dir, intermediate_dir)
            tables[stem] = answer_table
        except Exception as ex:
            print(f"FAILED: {image_path}")
            print(ex)
            failures.append(str(image_path))
    return tables, failures


def process_tables(tables, template, output_dir, intermediate_dir):
    """Stage 2: segment answer cells and extract handwriting for each table."""
    ok = 0
    failures = []
    for stem, answer_table in tables.items():
        print(f"Extracting handwriting: {stem}")
        try:
            cells = segment_answer_cells(answer_table)
            handwriting = extract_handwriting(answer_table, template, cells)

            cells_dir = output_dir / "cells" / stem
            for cell in cells:
                save_image(cells_dir / f"q{cell.question:02d}.png", cell.image)

            handwriting_dir = output_dir / "handwriting" / stem
            for item in handwriting:
                save_image(handwriting_dir / f"q{item.question:02d}.png", item.image)

            if SAVE_DEBUG_IMAGES:
                _save_cell_debug_overlay(stem, answer_table, cells, handwriting, intermediate_dir)

            flagged = sorted(item.question for item in handwriting if item.spans_multiple_rows)
            if flagged:
                print(f"  review questions {flagged}: handwriting spans multiple rows")

            ok += 1
        except Exception as ex:
            print(f"FAILED: {stem}")
            print(ex)
            failures.append(stem)
    return ok, failures


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

    tables, table_failures = locate_tables(args.images, OUTPUT_DIR, INTERMEDIATE_DIR)

    ok, cell_failures = 0, []
    if tables:
        print(f"Building printed-content template from {len(tables)} table(s)")
        template = build_printed_template(list(tables.values()))
        save_image(TEMPLATE_PATH, template)

        ok, cell_failures = process_tables(tables, template, OUTPUT_DIR, INTERMEDIATE_DIR)

    print()
    print("===================================")
    print(f"Successful : {ok}")
    print(f"Failed     : {len(table_failures) + len(cell_failures)}")
    for name in table_failures + cell_failures:
        print(f"  {name}")


if __name__ == "__main__":
    main()
