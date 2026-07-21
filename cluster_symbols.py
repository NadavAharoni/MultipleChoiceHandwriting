import argparse
import csv
from pathlib import Path

import cv2
import numpy as np

from clustering import build_cluster_gallery, cluster_symbols, extract_symbol
from config import CLUSTER_COUNT, INTERMEDIATE_DIR, OUTPUT_DIR
from utils import ensure_dir, save_image


def _read_grayscale(path: Path) -> np.ndarray:
    data = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise RuntimeError(f"Cannot read image: {path}")
    return image


def main():

    parser = argparse.ArgumentParser(
        description="Cluster every cell's handwriting by shape, for later labeling."
    )

    parser.add_argument(
        "handwriting_dir",
        nargs="?",
        default=str(OUTPUT_DIR / "handwriting"),
        help="Directory of <exam>/q<NN>.png handwriting outputs",
    )
    parser.add_argument("-k", type=int, default=CLUSTER_COUNT, help="Number of shape clusters")
    parser.add_argument(
        "-o", "--output", default=str(OUTPUT_DIR / "clusters.csv"), help="Output CSV mapping path"
    )
    parser.add_argument(
        "--gallery", default=str(INTERMEDIATE_DIR / "cluster_gallery.png"), help="Output gallery image path"
    )

    args = parser.parse_args()

    paths = sorted(Path(args.handwriting_dir).glob("*/q*.png"))
    if not paths:
        print(f"No handwriting images found under {args.handwriting_dir}")
        return

    names, canvases, blank = [], [], []
    for path in paths:
        name = f"{path.parent.name}/{path.stem}"
        canvas = extract_symbol(_read_grayscale(path))
        if canvas is None:
            blank.append(name)
        else:
            names.append(name)
            canvases.append(canvas)

    print(f"{len(names)} symbols, {len(blank)} blank cells, clustering with k={args.k}")
    result = cluster_symbols(canvases, k=args.k)

    ensure_dir(Path(args.output).parent)
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["exam", "question", "cluster", "distance", "letter"])
        for name, cluster, distance in zip(names, result.labels, result.distances):
            exam, question = name.split("/")
            writer.writerow([exam, question, cluster, f"{distance:.3f}", ""])
        for name in blank:
            exam, question = name.split("/")
            writer.writerow([exam, question, "", "", ""])
    print(f"Wrote {args.output} ({len(names) + len(blank)} rows, 'letter' column left for labeling)")

    gallery = build_cluster_gallery(names, canvases, result)
    save_image(Path(args.gallery), gallery)
    print(f"Wrote {args.gallery}")


if __name__ == "__main__":
    main()
