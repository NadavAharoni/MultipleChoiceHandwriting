import numpy as np
import pytest

from cells import segment_answer_cells

WIDTH, HEIGHT = 1200, 600
ROW_COUNT = 11
LEFT_EDGE, LEFT_DIVIDER, LEFT_RIGHT = 10, 210, 490
RIGHT_EDGE, RIGHT_DIVIDER, RIGHT_RIGHT = 690, 835, 1190


def _draw_block(image, left, divider, right, rows, skip_right_edge=False):
    verticals = [left, divider] if skip_right_edge else [left, divider, right]
    for x in verticals:
        image[rows[0] : rows[-1] + 1, x] = 0
    for y in rows:
        image[y, left : right + 1] = 0


def _blank_table():
    return np.full((HEIGHT, WIDTH, 3), 255, dtype=np.uint8)


def _rows():
    return [round(3 + index * (596 - 3) / (ROW_COUNT - 1)) for index in range(ROW_COUNT)]


def make_table(skip_right_edge=False, noise_stroke=None):
    image = _blank_table()
    rows = _rows()
    _draw_block(image, LEFT_EDGE, LEFT_DIVIDER, LEFT_RIGHT, rows, skip_right_edge)
    _draw_block(image, RIGHT_EDGE, RIGHT_DIVIDER, RIGHT_RIGHT, rows, skip_right_edge)
    if noise_stroke is not None:
        x, row_span = noise_stroke
        for row_index in row_span:
            top, bottom = rows[row_index], rows[row_index + 1]
            image[top + 5 : bottom - 5, x] = 0
    return image


def test_segments_into_20_cells_with_expected_question_numbers():
    cells = segment_answer_cells(make_table())
    assert [cell.question for cell in cells] == list(range(1, 21))


def test_right_block_rows_are_questions_1_to_10_top_to_bottom():
    cells = segment_answer_cells(make_table())
    right_block = [cell for cell in cells if cell.question <= 10]
    right_block.sort(key=lambda cell: cell.top)
    assert [cell.question for cell in right_block] == list(range(1, 11))


def test_left_block_rows_are_questions_11_to_20_top_to_bottom():
    cells = segment_answer_cells(make_table())
    left_block = [cell for cell in cells if cell.question > 10]
    left_block.sort(key=lambda cell: cell.top)
    assert [cell.question for cell in left_block] == list(range(11, 21))


def test_cell_bounds_are_between_divider_and_left_edge():
    cells = segment_answer_cells(make_table())
    question_1 = next(cell for cell in cells if cell.question == 1)
    assert RIGHT_EDGE < question_1.left < question_1.right < RIGHT_DIVIDER


def test_cell_image_matches_its_bounds():
    cells = segment_answer_cells(make_table())
    cell = cells[0]
    assert cell.image.shape[:2] == (cell.bottom - cell.top, cell.right - cell.left)


def test_succeeds_when_the_outer_right_edge_is_cropped_off():
    # 03b deliberately allows the outer number-column border to be missing;
    # only the left edge and the answer/number divider are required.
    cells = segment_answer_cells(make_table(skip_right_edge=True))
    assert [cell.question for cell in cells] == list(range(1, 21))


def test_ignores_a_handwriting_stroke_that_mimics_a_vertical_line():
    # A stroke lining up across most (but not all) rows must not be mistaken
    # for a printed grid line.
    clean = segment_answer_cells(make_table())
    noisy = segment_answer_cells(make_table(noise_stroke=(300, range(8))))
    assert [(c.left, c.right) for c in clean] == [(c.left, c.right) for c in noisy]


def test_raises_when_a_row_line_is_missing():
    image = make_table()
    rows = _rows()
    # Erase the middle row line entirely.
    image[rows[5] - 1 : rows[5] + 2, :] = 255
    with pytest.raises(RuntimeError):
        segment_answer_cells(image)
