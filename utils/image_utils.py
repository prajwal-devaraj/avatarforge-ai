import io

import cv2
import numpy as np
from PIL import Image


def blend_with_source(source_rgb: np.ndarray, styled_rgb: np.ndarray, intensity: int) -> np.ndarray:
    """Blend a style with the source using one consistent intensity scale."""
    alpha = intensity / 100.0
    return cv2.addWeighted(styled_rgb, alpha, source_rgb, 1.0 - alpha, 0)


def encode_jpeg(image_rgb: np.ndarray, quality: int = 94) -> io.BytesIO:
    """Encode an RGB NumPy image as an in-memory JPEG stream."""
    output = Image.fromarray(image_rgb)
    image_io = io.BytesIO()
    output.save(image_io, "JPEG", quality=quality, optimize=True)
    image_io.seek(0)
    return image_io
