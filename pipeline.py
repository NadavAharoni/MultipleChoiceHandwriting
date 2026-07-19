import argparse
from pathlib import Path

from config import OUTPUT_DIR, INTERMEDIATE_DIR
from utils import ensure_dir
from geometry import process_image


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
