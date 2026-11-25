import numpy as np
import pytest
from PIL import Image

from classical.resize import keys_kernel, lanczos_kernel, resize, upsample
from data.degrade import bicubic_downscale


def _pattern(h=48, w=40) -> np.ndarray:
    y = np.linspace(0, 1, h)[:, None, None]
    x = np.linspace(0, 1, w)[None, :, None]
    image = np.zeros((h, w, 3))
    image[..., 0] = x[..., 0]
    image[..., 1] = y[..., 0]
    image[..., 2] = 0.5 + 0.5 * np.sin(2 * np.pi * 4 * x[..., 0]) * np.cos(2 * np.pi * 3 * y[..., 0])
    return image


def test_flat_image_is_unchanged():
    flat = np.full((12, 16, 3), 0.4)
    out = upsample(flat, keys_kernel(-0.5), 2.0)
    assert out.shape == (48, 64, 3)
    assert out == pytest.approx(0.4, abs=1e-10)


def test_keys_matches_pillow_bicubic():
    # Same kernel and the same pixel-center grid, so the two resizes should agree past 8-bit.
    image = _pattern()
    ours = resize(image, 24, 20, keys_kernel(-0.5), 2.0)
    pillow = []
    for channel in range(3):
        plane = Image.fromarray(image[..., channel].astype(np.float32), mode="F")
        plane = plane.resize((20, 24), Image.Resampling.BICUBIC)
        pillow.append(np.asarray(plane, dtype=np.float64))
    assert ours == pytest.approx(np.stack(pillow, axis=-1), abs=1e-5)


def test_lanczos_matches_pillow():
    image = _pattern()
    ours = resize(image, 24, 20, lanczos_kernel(3), 3.0)
    pillow = []
    for channel in range(3):
        plane = Image.fromarray(image[..., channel].astype(np.float32), mode="F")
        plane = plane.resize((20, 24), Image.Resampling.LANCZOS)
        pillow.append(np.asarray(plane, dtype=np.float64))
    assert ours == pytest.approx(np.stack(pillow, axis=-1), abs=1e-5)


def test_upsampling_a_downscaled_patch_lines_up():
    hr = Image.fromarray((_pattern(64, 48) * 255).astype(np.uint8))
    lr = bicubic_downscale(hr)
    up = upsample(np.asarray(lr, dtype=np.float64) / 255.0, keys_kernel(-0.5), 2.0)
    assert up.shape[:2] == hr.size[::-1]
