import numpy as np
import pytest

from services.image_service import STYLE_ENGINES, apply_style


@pytest.mark.parametrize("style", list(STYLE_ENGINES.keys()))
def test_style_engines_preserve_image_shape(style):
    source = np.full((48, 48, 3), 128, dtype=np.uint8)
    result = apply_style(source, style, 70)

    assert result.shape == source.shape
    assert result.dtype == np.uint8


def test_unknown_style_is_rejected():
    source = np.zeros((16, 16, 3), dtype=np.uint8)
    with pytest.raises(ValueError):
        apply_style(source, "unknown", 70)
