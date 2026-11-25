import numpy as np
from PIL import Image

from classical.ibp import back_project, pillow_bicubic
from classical.resize import keys_kernel, upsample
from data.degrade import bicubic_downscale, to_float
from metrics import score


def _up(image: np.ndarray) -> np.ndarray:
    return upsample(image, keys_kernel(-0.5), 2.0)


def test_edge_psnr_rises_and_residual_shrinks():
    # A hard edge is where a single bicubic upsample is soft. Damped back-projection
    # should sharpen it. Smooth ramps can go the other way; that is why `step` stays small.
    pixels = np.zeros((64, 64, 3), dtype=np.uint8)
    pixels[:, 32:] = 255
    hr = Image.fromarray(pixels)
    lr = bicubic_downscale(hr)
    lr_f = to_float(lr)
    start = _up(lr_f)
    refined = back_project(lr_f, _up, iterations=8, step=0.2)
    before = np.mean((pillow_bicubic(start, 16, 16) - lr_f) ** 2)
    after = np.mean((pillow_bicubic(refined, 16, 16) - lr_f) ** 2)
    assert after < before
    hr_f = to_float(hr)
    assert score(np.clip(refined, 0, 1), hr_f)["psnr"] > score(np.clip(start, 0, 1), hr_f)["psnr"]


def test_constant_stays_constant():
    image = np.full((8, 10, 3), 0.3)
    out = back_project(image, _up, iterations=2, step=0.5)
    assert out.shape == (32, 40, 3)
    np.testing.assert_allclose(out, 0.3, atol=1e-5)
