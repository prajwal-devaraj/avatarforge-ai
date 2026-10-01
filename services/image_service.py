import cv2
import numpy as np
from PIL import Image, ImageEnhance

from utils.image_utils import blend_with_source
from utils.validators import ALLOWED_FORMATS


STYLE_LABELS = {
    "cartoon": "Signature Cartoon",
    "sketch": "Pencil Sketch",
    "comic": "Comic Ink",
    "portrait": "Soft Portrait",
    "grayscale": "Grayscale Art",
    "edgepop": "Edge Pop",
}


def prepare_image(file_storage) -> np.ndarray:
    """Decode, normalize, and resize a supported user image."""
    image = Image.open(file_storage)
    if image.format not in ALLOWED_FORMATS:
        raise ValueError("Unsupported image format")
    image = image.convert("RGB")
    image.thumbnail((2200, 2200))
    return np.asarray(image)


def signature_cartoon(image_rgb: np.ndarray, intensity: int) -> np.ndarray:
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    passes = 1 + round(intensity / 35)
    color = image_bgr.copy()
    for _ in range(passes):
        color = cv2.bilateralFilter(color, d=9, sigmaColor=120 + intensity, sigmaSpace=120 + intensity)

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 7)
    edges = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, blockSize=9, C=7
    )
    styled = cv2.bitwise_and(color, color, mask=edges)
    styled_rgb = cv2.cvtColor(styled, cv2.COLOR_BGR2RGB)
    return blend_with_source(image_rgb, styled_rgb, intensity)


def pencil_sketch(image_rgb: np.ndarray, intensity: int) -> np.ndarray:
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    inverted = 255 - gray
    blur_size = 15 + 2 * round(intensity / 20)
    if blur_size % 2 == 0:
        blur_size += 1
    blurred = cv2.GaussianBlur(inverted, (blur_size, blur_size), 0)
    dodge = cv2.divide(gray, 255 - blurred, scale=256)
    sketch_rgb = cv2.cvtColor(dodge, cv2.COLOR_GRAY2RGB)
    return blend_with_source(image_rgb, sketch_rgb, intensity)


def comic_ink(image_rgb: np.ndarray, intensity: int) -> np.ndarray:
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    smooth = cv2.bilateralFilter(image_bgr, 9, 150, 150)
    levels = 5 if intensity >= 65 else 7
    step = max(1, 256 // levels)
    poster = (smooth // step) * step + step // 2
    poster = np.clip(poster, 0, 255).astype(np.uint8)

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 55, 130)
    edges = cv2.dilate(edges, np.ones((2, 2), np.uint8), iterations=1)
    poster[edges > 0] = (18, 18, 18)
    comic_rgb = cv2.cvtColor(poster, cv2.COLOR_BGR2RGB)
    return blend_with_source(image_rgb, comic_rgb, intensity)


def soft_portrait(image_rgb: np.ndarray, intensity: int) -> np.ndarray:
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    sigma = 35 + intensity * 1.2
    smooth = cv2.bilateralFilter(image_bgr, 9, sigma, sigma)
    smooth_rgb = cv2.cvtColor(smooth, cv2.COLOR_BGR2RGB)

    lab = cv2.cvtColor(smooth_rgb, cv2.COLOR_RGB2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.4 + intensity / 100, tileGridSize=(8, 8))
    l_channel = clahe.apply(l_channel)
    enhanced = cv2.cvtColor(cv2.merge((l_channel, a_channel, b_channel)), cv2.COLOR_LAB2RGB)

    pil = Image.fromarray(enhanced)
    pil = ImageEnhance.Color(pil).enhance(1.02 + intensity / 500)
    portrait = np.asarray(pil)
    return blend_with_source(image_rgb, portrait, intensity)


def grayscale_art(image_rgb: np.ndarray, intensity: int) -> np.ndarray:
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=1.8 + intensity / 80, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    gray_rgb = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
    return blend_with_source(image_rgb, gray_rgb, intensity)


def edge_pop(image_rgb: np.ndarray, intensity: int) -> np.ndarray:
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    smooth = cv2.bilateralFilter(image_bgr, 7, 95 + intensity, 95 + intensity)
    hsv = cv2.cvtColor(smooth, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] *= 1.10 + intensity / 250
    hsv[:, :, 2] *= 1.02 + intensity / 500
    hsv = np.clip(hsv, 0, 255).astype(np.uint8)
    vivid = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 70, 150)
    edges = cv2.dilate(edges, np.ones((2, 2), np.uint8), iterations=1)
    vivid[edges > 0] = (12, 12, 12)
    edge_rgb = cv2.cvtColor(vivid, cv2.COLOR_BGR2RGB)
    return blend_with_source(image_rgb, edge_rgb, intensity)


STYLE_ENGINES = {
    "cartoon": signature_cartoon,
    "sketch": pencil_sketch,
    "comic": comic_ink,
    "portrait": soft_portrait,
    "grayscale": grayscale_art,
    "edgepop": edge_pop,
}


def apply_style(image_rgb: np.ndarray, style: str, intensity: int) -> np.ndarray:
    """Apply one registered style engine to an RGB image."""
    try:
        engine = STYLE_ENGINES[style]
    except KeyError as exc:
        raise ValueError("That style is not supported.") from exc
    return engine(image_rgb, intensity)
