from pathlib import Path
import cv2


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def save_image(path: Path, image):
    ensure_dir(path.parent)
    cv2.imwrite(str(path), image)


def image_name(path: Path):
    return path.stem
