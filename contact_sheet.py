import argparse
from pathlib import Path

from config import CONTACT_SHEET_COLUMNS, CONTACT_SHEET_THUMB_WIDTH
from utils import build_contact_sheet, save_image


def main():

    parser = argparse.ArgumentParser(
        description="Tile many debug images into one contact sheet for quick review."
    )

    parser.add_argument("images", nargs="+", help="Input images")
    parser.add_argument("-o", "--output", default="contact_sheet.png", help="Output image path")
    parser.add_argument("--columns", type=int, default=CONTACT_SHEET_COLUMNS)
    parser.add_argument("--thumb-width", type=int, default=CONTACT_SHEET_THUMB_WIDTH)

    args = parser.parse_args()

    paths = sorted(Path(image) for image in args.images)
    sheet = build_contact_sheet(paths, columns=args.columns, thumb_width=args.thumb_width)
    save_image(Path(args.output), sheet)
    print(f"Wrote {args.output} ({len(paths)} images)")


if __name__ == "__main__":
    main()
