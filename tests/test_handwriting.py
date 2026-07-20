import numpy as np

from cells import AnswerCell
from handwriting import NOMINAL_ROW_HEIGHT, extract_cell_handwriting

HEIGHT, WIDTH = 300, 300


def _blank_image():
    return np.full((HEIGHT, WIDTH, 3), 255, dtype=np.uint8)


def _blank_template():
    return np.zeros((HEIGHT, WIDTH), dtype=np.uint8)


def _cell(question, top, left, bottom, right):
    return AnswerCell(
        question=question,
        left=left,
        top=top,
        right=right,
        bottom=bottom,
        divider=(left + right) // 2,
        image=np.zeros((1, 1, 3), dtype=np.uint8),
    )


def test_removes_printed_ink_keeps_handwriting():
    image = _blank_image()
    template = _blank_template()

    # Printed content: a horizontal line, marked in the template.
    image[100:103, 20:280] = 0
    template[95:108, 20:280] = 255

    # Handwriting: a blob elsewhere in the cell, not in the template.
    image[130:150, 100:120] = 0

    cell = _cell(1, top=90, left=20, bottom=170, right=280)
    result = extract_cell_handwriting(image, template, cell)

    ink = np.count_nonzero(result.image < 128)
    assert 0 < ink < 600  # roughly the handwriting blob (400px), not the whole line too


def test_reattaches_component_that_overflows_the_cell():
    image = _blank_image()
    template = _blank_template()
    cell = _cell(1, top=100, left=20, bottom=160, right=280)
    # A stroke mostly inside the cell, whose tail pokes past cell.bottom by
    # less than the padding, so the whole thing should survive unclipped.
    image[145:168, 100:120] = 0  # 23 rows tall, last 7 of them past bottom=160

    result = extract_cell_handwriting(image, template, cell)
    # A shape assertion alone would pass even if the tail were clipped,
    # since the canvas is always at least as tall as the cell's own tight
    # bounds (60px here) - checking the actual ink count catches that.
    assert np.count_nonzero(result.image < 128) >= 23 * 20 - 40


def test_does_not_claim_a_component_centred_in_the_neighbor():
    image = _blank_image()
    template = _blank_template()
    cell = _cell(1, top=100, left=20, bottom=160, right=280)
    # A stroke whose centroid falls below this cell's own bounds.
    image[165:176, 100:120] = 0

    result = extract_cell_handwriting(image, template, cell)
    assert np.count_nonzero(result.image < 128) == 0


def test_flags_a_component_taller_than_the_row_height_threshold():
    image = _blank_image()
    template = _blank_template()
    cell = _cell(1, top=50, left=20, bottom=170, right=280)
    tall_height = int(NOMINAL_ROW_HEIGHT * 1.5)
    image[90 : 90 + tall_height, 100:120] = 0

    result = extract_cell_handwriting(image, template, cell)
    assert result.spans_multiple_rows


def test_blank_cell_returns_image_matching_tight_bounds():
    image = _blank_image()
    template = _blank_template()
    cell = _cell(1, top=100, left=20, bottom=160, right=280)

    result = extract_cell_handwriting(image, template, cell)
    assert result.image.shape == (60, 260)
    assert np.all(result.image == 255)
