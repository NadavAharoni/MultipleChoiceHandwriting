from dataclasses import dataclass

import cv2
import numpy as np
from sklearn.cluster import KMeans

from config import CLUSTER_CANVAS_SIZE, CLUSTER_COUNT, CLUSTER_MIN_COMPONENT_AREA


def extract_symbol(
    image: np.ndarray,
    min_area: int = CLUSTER_MIN_COMPONENT_AREA,
    canvas_size: int = CLUSTER_CANVAS_SIZE,
) -> np.ndarray | None:
    """Reduce a handwriting image to a fixed-size, centred shape descriptor.

    A handwriting output (`handwriting.py`) can still contain a small
    leftover printed-number fragment alongside the real ink - an accepted
    limitation there, since removing it risks reopening Iteration 04a's
    bug. Excluding components below ``min_area`` here keeps only
    substantial strokes, since real handwriting is consistently much
    larger than what survives. Returns ``None`` for a blank cell (no
    component reaches ``min_area``), which the caller should treat as "no
    answer detected" rather than a shape to cluster.
    """
    ink = (image < 128).astype(np.uint8) * 255
    component_count, _, stats, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    big = [stats[i] for i in range(1, component_count) if stats[i][4] >= min_area]
    if not big:
        return None

    x0 = min(box[0] for box in big)
    y0 = min(box[1] for box in big)
    x1 = max(box[0] + box[2] for box in big)
    y1 = max(box[1] + box[3] for box in big)
    crop = ink[y0:y1, x0:x1]

    height, width = crop.shape
    scale = (canvas_size - 4) / max(height, width)
    resized = cv2.resize(crop, (max(1, round(width * scale)), max(1, round(height * scale))))

    canvas = np.zeros((canvas_size, canvas_size), dtype=np.uint8)
    resized_height, resized_width = resized.shape
    offset_y = (canvas_size - resized_height) // 2
    offset_x = (canvas_size - resized_width) // 2
    canvas[offset_y : offset_y + resized_height, offset_x : offset_x + resized_width] = resized
    return canvas


@dataclass(frozen=True)
class ClusterResult:
    """Shape-based clusters over a set of symbols, with a per-item confidence signal.

    ``distances`` is each symbol's distance to its own cluster's centroid -
    lower means more typical of its cluster, higher means more likely to be
    misclustered or an unusual handwriting style, worth reviewing first
    (see docs/06_symbol_clustering.md).
    """

    labels: np.ndarray
    distances: np.ndarray


def cluster_symbols(canvases: list[np.ndarray], k: int = CLUSTER_COUNT, random_state: int = 0) -> ClusterResult:
    """Cluster symbol canvases by shape.

    Not intended to recover exactly the 5 possible letters: the same
    letter written in different handwriting styles can land in different
    clusters, and a multi-symbol answer (e.g. a comma-separated pair) has
    its own distinct shape. Labeling what each cluster actually represents
    is a separate, later step.
    """
    if len(canvases) < k:
        raise ValueError(f"Need at least k={k} symbols to form that many clusters, got {len(canvases)}")

    features = np.array([canvas.flatten() / 255.0 for canvas in canvases])
    kmeans = KMeans(n_clusters=k, random_state=random_state, n_init=10).fit(features)
    assigned_centroids = kmeans.cluster_centers_[kmeans.labels_]
    distances = np.linalg.norm(features - assigned_centroids, axis=1)
    return ClusterResult(labels=kmeans.labels_, distances=distances)


def build_cluster_gallery(
    names: list[str], canvases: list[np.ndarray], result: ClusterResult, columns: int = 24
) -> np.ndarray:
    """Tile symbols into one image, grouped by cluster and sorted by distance.

    Within each cluster's row, the most typical symbols (lowest distance to
    centroid) come first and the least typical - the ones worth reviewing
    first - come last, instead of being buried in cluster order.
    """
    label_height = 12
    cell_size = canvases[0].shape[0] + label_height

    rows = []
    for cluster in range(result.labels.max() + 1):
        members = np.flatnonzero(result.labels == cluster)
        members = members[np.argsort(result.distances[members])]

        tiles = []
        for i in members[:columns]:
            tile = np.zeros((cell_size, canvases[i].shape[1]), dtype=np.uint8)
            tile[: canvases[i].shape[0]] = canvases[i]
            label = names[i].rsplit("/", 1)[-1].removesuffix(".png")
            cv2.putText(tile, label, (1, cell_size - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.25, 255, 1, cv2.LINE_AA)
            tiles.append(tile)
        while len(tiles) < columns:
            tiles.append(np.zeros((cell_size, canvases[0].shape[1]), dtype=np.uint8))
        rows.append(np.hstack(tiles))

    separator = np.full((4, rows[0].shape[1]), 96, dtype=np.uint8)
    interleaved = [row for pair in zip(rows, [separator] * len(rows)) for row in pair]
    return np.vstack(interleaved[:-1])
