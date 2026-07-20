from pathlib import Path
import cv2
import numpy as np

def ensure_dir(path: Path):
    path.mkdir(parents=True,exist_ok=True)

def save_image(path: Path,image):
    ensure_dir(path.parent)
    ok,buf=cv2.imencode(path.suffix,image)
    if not ok:
        raise RuntimeError(f'Failed encoding {path}')
    buf.tofile(str(path))

def read_image(path: Path):
    data = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f'Cannot read image: {path}')
    return image

def image_name(path: Path):
    return path.stem

def build_contact_sheet(paths, columns: int, thumb_width: int):
    """Tile many images into one grid, labelled with their filenames.

    Lets a human review every debug image from a full run at a glance
    instead of opening each file individually.
    """
    paths = list(paths)
    if not paths:
        raise ValueError("No images to tile into a contact sheet")

    label_height = 24
    thumbnails = []
    for path in paths:
        image = read_image(path)
        scale = thumb_width / image.shape[1]
        thumb_height = max(1, round(image.shape[0] * scale))
        thumb = cv2.resize(image, (thumb_width, thumb_height))
        cell = np.full((thumb_height + label_height, thumb_width, 3), 255, dtype=np.uint8)
        cell[:thumb_height] = thumb
        cv2.putText(
            cell,
            Path(path).stem[:40],
            (2, thumb_height + 17),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 0, 0),
            1,
            cv2.LINE_AA,
        )
        thumbnails.append(cell)

    cell_height = max(thumb.shape[0] for thumb in thumbnails)
    rows = -(-len(thumbnails) // columns)  # ceil division
    sheet = np.full((rows * cell_height, columns * thumb_width, 3), 220, dtype=np.uint8)
    for index, thumb in enumerate(thumbnails):
        row, col = divmod(index, columns)
        y, x = row * cell_height, col * thumb_width
        sheet[y : y + thumb.shape[0], x : x + thumb_width] = thumb

    return sheet
