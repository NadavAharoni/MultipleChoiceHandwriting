from pathlib import Path

# Output directories
OUTPUT_DIR = Path("output")
INTERMEDIATE_DIR = Path("intermediate")

# Standard page size after normalization
PAGE_WIDTH = 2480
PAGE_HEIGHT = 3508

# Debug images
SAVE_DEBUG_IMAGES = True

# Geometry parameters.  The kernels scale with the scan so the same settings
# work for images produced at different scanner resolutions.
HORIZONTAL_KERNEL_DIVISOR = 50
VERTICAL_KERNEL_DIVISOR = 50
MIN_LINE_KERNEL_LENGTH = 25

# Normalized answer-table image produced by the table-detection stage.
TABLE_WIDTH = 1200
TABLE_HEIGHT = 600
TABLE_ROW_COUNT = 11
TABLE_ASPECT_RATIO = 2.08

# Answer-cell segmentation.  Each answer table is split into two blocks of
# ten questions; the right block (larger x) holds questions 1-10, the left
# block holds questions 11-20.
QUESTIONS_PER_BLOCK = 10
# Shrink each detected cell inward by this many pixels so the crop excludes
# the printed grid line itself.
CELL_INSET = 2
# Fallback gap kept between the left block's right edge and the right
# block's left edge when the left block's own outer border is not detected.
CELL_GAP_MARGIN = 15

# How far (in pixels) to search near a printed row line for a genuinely
# blank row, so handwriting that bleeds slightly across the line still ends
# up entirely on one side. Also used to grow the table's outer top/bottom
# edge for the same reason. About a third of the ~60px normalized row
# height - far enough to catch typical overflow without eating into most of
# the neighboring cell.
ROW_GAP_SEARCH_PX = 22
# The printed outer top/bottom table border's own blur bleeds into this many
# adjacent rows at this image size; the outward ink-overflow search starts
# past that halo so it isn't mistaken for hitting a real border immediately.
OUTER_EDGE_BLUR_MARGIN = 4
# A row is considered blank if it has at most this much ink, once the
# printed grid lines crossing it have been masked out. Calibrated from the
# real dataset: scan noise alone can read up to ~13 in a genuinely blank
# row, while real handwriting reads much higher (30+).
ROW_GAP_MIN_INK = 15

# Contact sheet defaults, used to tile many debug images for quick review.
CONTACT_SHEET_COLUMNS = 6
CONTACT_SHEET_THUMB_WIDTH = 320

# Printed-content template: every scan shares the same printed form, so a
# pixel that is ink in nearly every scan is the printed grid/numbers, not
# handwriting (which varies scan to scan). Calibrated against the real
# dataset (see docs/05_handwriting_extraction.md): a pixel's own position
# jitters a little between scans even after normalization, so ink is first
# dilated to tolerate that before the frequency vote.
TEMPLATE_DILATE_PX = 3
TEMPLATE_FREQUENCY_THRESHOLD = 0.75
TEMPLATE_PATH = INTERMEDIATE_DIR / "printed_template.png"

# Handwriting extraction: how far a cell's search region extends beyond its
# own tight bounds to find connected ink components that belong to it but
# were cropped at the boundary (see cells.py's CELL_INSET / row-boundary
# logic). Kept deliberately small: cells.py's own row boundaries are already
# adjusted toward genuine ink gaps (see docs/04b_row_boundary_overflow.md),
# so this is a secondary safety margin, not the primary defense against
# clipping. A larger margin was tried and rejected - removing the grid line
# removes the natural barrier that kept adjacent rows' ink apart, so bigger
# padding let ordinary bold handwriting in adjacent rows merge into one
# component far more often than it caught genuine overflow.
HANDWRITING_ROW_PAD_PX = 8
HANDWRITING_COLUMN_PAD_PX = 8
# 4-connectivity (not 8) for the same reason: diagonal-only touches are the
# easiest way for two unrelated rows' ink to falsely merge.
HANDWRITING_CONNECTIVITY = 4
# A kept component taller than this multiple of the nominal row height is
# flagged as spanning multiple rows - a sign it may not belong entirely to
# this question.
HANDWRITING_MULTI_ROW_FLAG_RATIO = 1.3

