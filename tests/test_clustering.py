import numpy as np
import pytest

from clustering import cluster_symbols, extract_symbol

HEIGHT, WIDTH = 60, 400


def _blank_image():
    return np.full((HEIGHT, WIDTH), 255, dtype=np.uint8)


def test_extract_symbol_ignores_small_noise_keeps_real_stroke():
    image = _blank_image()
    image[10:40, 20:40] = 0  # a real stroke, well above the area threshold
    image[5:8, 300:303] = 0  # a tiny noise speck, well below it

    canvas = extract_symbol(image, min_area=150)
    assert canvas is not None
    assert canvas.shape == (40, 40)
    # The noise speck sits far to the right; if it leaked into the crop,
    # the stroke wouldn't fill most of the canvas after centring/scaling.
    assert np.count_nonzero(canvas) > (40 * 40) * 0.15


def test_extract_symbol_returns_none_for_a_blank_cell():
    image = _blank_image()
    image[5:8, 300:303] = 0  # only noise, nothing above the area threshold

    assert extract_symbol(image, min_area=150) is None


def test_extract_symbol_spans_multiple_components_for_a_multi_symbol_answer():
    image = _blank_image()
    image[10:40, 20:45] = 0  # first letter
    image[15:25, 60:70] = 0  # comma
    image[10:40, 90:115] = 0  # second letter

    canvas = extract_symbol(image, min_area=50)
    assert canvas is not None
    # A multi-symbol answer is much wider than tall once captured whole.
    ys, xs = np.nonzero(canvas)
    assert (xs.max() - xs.min()) > (ys.max() - ys.min())


def _synthetic_canvas(kind, rng):
    canvas = np.zeros((40, 40), dtype=np.uint8)
    jitter = rng.integers(-1, 2, size=2)
    if kind == "square":
        y, x = 10 + jitter[0], 10 + jitter[1]
        canvas[y : y + 15, x : x + 15] = 255
    else:  # diagonal line
        for i in range(30):
            y, x = 5 + i + jitter[0], 5 + i + jitter[1]
            if 0 <= y < 40 and 0 <= x < 40:
                canvas[y, x] = 255
    return canvas


def test_cluster_symbols_separates_two_distinct_shapes():
    rng = np.random.default_rng(0)
    canvases = [_synthetic_canvas("square", rng) for _ in range(15)]
    canvases += [_synthetic_canvas("line", rng) for _ in range(15)]

    result = cluster_symbols(canvases, k=2)
    squares, lines = result.labels[:15], result.labels[15:]
    # Each true group should be assigned overwhelmingly to one cluster label.
    assert max(np.bincount(squares, minlength=2)) >= 14
    assert max(np.bincount(lines, minlength=2)) >= 14


def test_cluster_symbols_gives_an_outlier_higher_distance():
    rng = np.random.default_rng(1)
    canvases = [_synthetic_canvas("square", rng) for _ in range(19)]
    outlier = np.zeros((40, 40), dtype=np.uint8)
    outlier[2:6, 2:38] = 255  # a thin bar, unlike the rest of the group
    canvases.append(outlier)

    result = cluster_symbols(canvases, k=1)
    assert result.distances[-1] > np.median(result.distances[:-1])


def test_cluster_symbols_raises_when_too_few_symbols_for_k():
    canvases = [np.zeros((40, 40), dtype=np.uint8) for _ in range(3)]
    with pytest.raises(ValueError):
        cluster_symbols(canvases, k=5)
