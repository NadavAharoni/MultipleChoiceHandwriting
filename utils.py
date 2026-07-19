from pathlib import Path
import cv2

def ensure_dir(path: Path):
    path.mkdir(parents=True,exist_ok=True)

def save_image(path: Path,image):
    ensure_dir(path.parent)
    ok,buf=cv2.imencode(path.suffix,image)
    if not ok:
        raise RuntimeError(f'Failed encoding {path}')
    buf.tofile(str(path))

def image_name(path: Path):
    return path.stem
