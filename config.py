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

# Contact sheet defaults, used to tile many debug images for quick review.
CONTACT_SHEET_COLUMNS = 6
CONTACT_SHEET_THUMB_WIDTH = 320

