from utils.validators import clamp_intensity


def test_clamp_intensity_defaults_to_70():
    assert clamp_intensity(None) == 70
    assert clamp_intensity("invalid") == 70


def test_clamp_intensity_enforces_bounds():
    assert clamp_intensity("0") == 10
    assert clamp_intensity("50") == 50
    assert clamp_intensity("500") == 100
