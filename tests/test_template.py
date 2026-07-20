import numpy as np
import pytest

from template import build_printed_template

HEIGHT, WIDTH = 200, 200


def _make_table(seed):
    rng = np.random.default_rng(seed)
    image = np.full((HEIGHT, WIDTH, 3), 255, dtype=np.uint8)
    # Printed content: identical on every "scan".
    image[100:102, 10:190] = 0
    image[10:190, 50:52] = 0
    # Handwriting: a blob at a different position on every "scan".
    x, y = rng.integers(60, 140), rng.integers(60, 140)
    image[y : y + 15, x : x + 15] = 0
    return image


def test_isolates_shared_printed_content_from_varying_handwriting():
    images = [_make_table(seed) for seed in range(15)]
    template = build_printed_template(images)

    assert template[101, 100] == 255  # part of the shared horizontal line
    assert template[100, 51] == 255  # part of the shared vertical line
    assert template[5, 5] == 0  # never touched by the lines or any blob


def test_raises_on_empty_input():
    with pytest.raises(ValueError):
        build_printed_template([])
