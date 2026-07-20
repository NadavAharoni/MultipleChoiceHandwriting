import numpy as np
import pytest

from cells import segment_answer_cells

WIDTH, HEIGHT = 1200, 600
ROW_COUNT = 11
LEFT_EDGE, LEFT_DIVIDER, LEFT_RIGHT = 10, 210, 490
RIGHT_EDGE, RIGHT_DIVIDER, RIGHT_RIGHT = 690, 835, 1190
# Wide enough that blur+threshold reads it well above the noise floor (a
# thinner stroke can end up numerically indistinguishable from scan noise,
# see docs/04b_row_boundary_overflow.md), narrow enough to never look like a
# horizontal grid line.
STROKE_WIDTH = 30


def _draw_block(image, left, divider, right, rows, skip_right_edge=False):
    verticals = [left, divider] if skip_right_edge else [left, divider, right]
    for x in verticals:
        image[rows[0] : rows[-1] + 1, x] = 0
    for y in rows:
        image[y, left : right + 1] = 0


def _blank_table():
    return np.full((HEIGHT, WIDTH, 3), 255, dtype=np.uint8)


def _rows(top=3, bottom=596):
    return [round(top + index * (bottom - top) / (ROW_COUNT - 1)) for index in range(ROW_COUNT)]


def make_table(rows=None, skip_right_edge=False, noise_stroke=None):
    image = _blank_table()
    rows = rows if rows is not None else _rows()
    _draw_block(image, LEFT_EDGE, LEFT_DIVIDER, LEFT_RIGHT, rows, skip_right_edge)
    _draw_block(image, RIGHT_EDGE, RIGHT_DIVIDER, RIGHT_RIGHT, rows, skip_right_edge)
    if noise_stroke is not None:
        x, row_span = noise_stroke
        for row_index in row_span:
            top, bottom = rows[row_index], rows[row_index + 1]
            image[top + 5 : bottom - 5, x] = 0
    return image


def _draw_stroke(image, y0, y1, x_start):
    image[y0:y1, x_start : x_start + STROKE_WIDTH] = 0


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


def test_cell_spans_the_whole_block_not_just_the_handwriting_sub_column():
    # Some students write next to the printed number instead of in the
    # blank space reserved for it, so the crop must include both
    # sub-columns rather than stopping at the divider.
    cells = segment_answer_cells(make_table())
    question_1 = next(cell for cell in cells if cell.question == 1)
    assert RIGHT_EDGE < question_1.left < RIGHT_DIVIDER < question_1.right <= RIGHT_RIGHT
    assert question_1.divider == pytest.approx(RIGHT_DIVIDER, abs=2)


def test_cell_image_matches_its_bounds():
    cells = segment_answer_cells(make_table())
    cell = cells[0]
    assert cell.image.shape[:2] == (cell.bottom - cell.top, cell.right - cell.left)


def test_succeeds_when_the_outer_right_edge_is_cropped_off():
    # 03b deliberately allows the outer number-column border to be missing;
    # only the left edge and the answer/number divider are required. The
    # cell must still extend out to (near) the table's own edge rather than
    # stopping at the divider.
    cells = segment_answer_cells(make_table(skip_right_edge=True))
    assert [cell.question for cell in cells] == list(range(1, 21))
    question_1 = next(cell for cell in cells if cell.question == 1)
    assert question_1.right > RIGHT_DIVIDER + 50


def test_ignores_a_handwriting_stroke_that_mimics_a_vertical_line():
    # A stroke lining up across most (but not all) rows must not be mistaken
    # for a printed grid line.
    clean = segment_answer_cells(make_table())
    noisy = segment_answer_cells(make_table(noise_stroke=(300, range(8))))
    assert [(c.left, c.right) for c in clean] == [(c.left, c.right) for c in noisy]


def test_captures_ink_written_next_to_the_printed_number_instead_of_in_the_cell():
    # Regression test for real scans where a student wrote her answer next
    # to the printed number rather than in the blank handwriting cell.
    image = make_table()
    rows = _rows()
    ink_x = RIGHT_DIVIDER + 10  # inside the number sub-column
    _draw_stroke(image, rows[0] + 5, rows[1] - 5, ink_x)

    cells = segment_answer_cells(image)
    question_1 = next(cell for cell in cells if cell.question == 1)
    assert np.count_nonzero(question_1.image < 128) > 0


def test_row_boundary_shifts_to_the_true_gap_when_ink_bleeds_across_the_line():
    # A tall letter's tail bleeds a few pixels past the printed row line,
    # but a real blank gap still exists a little further down. The cut
    # should land in that gap, not exactly on the line, so nothing is lost.
    image = make_table()
    rows = _rows()
    y0 = rows[1]
    bleed_bottom = y0 + 6  # last inked row is bleed_bottom - 1
    _draw_stroke(image, y0 - 15, bleed_bottom, RIGHT_EDGE + 15)

    cells = segment_answer_cells(image)
    question_1 = next(c for c in cells if c.question == 1)
    assert question_1.bottom >= bleed_bottom


def test_falls_back_to_the_printed_line_when_no_gap_exists_nearby():
    # Regression test for a real scan where one student's connected cursive
    # left no blank row anywhere near a boundary, in either direction, for
    # as far as the search looks. There is no correct geometric cut in that
    # case; landing on the printed line itself is the least-bad choice, and
    # segmentation must still complete rather than raise.
    image = make_table()
    rows = _rows()
    y0 = rows[5]
    _draw_stroke(image, y0 - 22, y0 + 23, RIGHT_EDGE + 15)

    cells = segment_answer_cells(image)
    question_5 = next(c for c in cells if c.question == 5)
    question_6 = next(c for c in cells if c.question == 6)
    assert question_5.bottom == y0
    assert question_6.top == y0


def test_extends_top_edge_when_ink_overflows_above_the_table():
    # Mirrors Iteration 03b's outer-bounds fix, one level down: a stroke's
    # ascender pokes above the table's own printed top border.
    rows = _rows(top=30)
    image = make_table(rows=rows)
    overflow_top = rows[0] - 10
    _draw_stroke(image, overflow_top, rows[0], RIGHT_EDGE + 15)

    cells = segment_answer_cells(image)
    question_1 = next(c for c in cells if c.question == 1)
    assert question_1.top <= overflow_top


def test_raises_when_a_row_line_is_missing():
    image = make_table()
    rows = _rows()
    # Erase the middle row line entirely.
    image[rows[5] - 1 : rows[5] + 2, :] = 255
    with pytest.raises(RuntimeError):
        segment_answer_cells(image)
