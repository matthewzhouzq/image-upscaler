import numpy as np
import pytest
from PIL import Image

from data.degrade import bicubic_downscale, make_lr_hr_pair, modcrop, to_float


def _img(w: int, h: int) -> Image.Image:
    rng = np.random.default_rng(0)
    return Image.fromarray(rng.integers(0, 256, (h, w, 3), dtype=np.uint8))


def test_modcrop_makes_sizes_divisible():
    assert modcrop(_img(103, 66)).size == (100, 64)


def test_modcrop_keeps_top_left():
    img = _img(103, 66)
    assert np.array_equal(np.asarray(modcrop(img)), np.asarray(img)[:64, :100])


def test_downscale_size():
    assert bicubic_downscale(_img(100, 64)).size == (25, 16)


def test_downscale_rejects_uncropped():
    with pytest.raises(ValueError):
        bicubic_downscale(_img(103, 66))


def test_flat_image_stays_flat():
    # A constant colour must come back as the same constant: catches range and normalisation bugs.
    flat = Image.new("RGB", (64, 64), (120, 30, 200))
    assert (np.asarray(bicubic_downscale(flat)) == (120, 30, 200)).all()


def test_make_pair_from_file(tmp_path):
    path = tmp_path / "x.png"
    _img(103, 66).convert("RGBA").save(path)  # alpha channel on purpose
    lr, hr = make_lr_hr_pair(str(path))
    assert hr.mode == "RGB" and hr.size == (100, 64) and lr.size == (25, 16)


def test_to_float_range_and_dtype():
    x = to_float(_img(8, 8))
    assert x.dtype == np.float32 and x.shape == (8, 8, 3)
    assert 0.0 <= x.min() and x.max() <= 1.0
