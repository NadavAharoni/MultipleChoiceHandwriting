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

