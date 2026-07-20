import argparse
from pathlib import Path

from config import TEMPLATE_PATH
from geometry import read_image
from template import build_printed_template
from utils import save_image


def main():

    parser = argparse.ArgumentParser(
        description="Build the printed-content template from a set of normalized answer tables."
    )

    parser.add_argument("tables", nargs="+", help="Normalized answer-table images (answer_table.png)")
    parser.add_argument("-o", "--output", default=str(TEMPLATE_PATH), help="Output template path")

    args = parser.parse_args()

    images = [read_image(Path(path)) for path in args.tables]
    template = build_printed_template(images)
    save_image(Path(args.output), template)
    print(f"Wrote {args.output} from {len(images)} tables")


if __name__ == "__main__":
    main()
