import numpy as np
import pytest

from metrics import psnr, rgb_to_y, score, ssim, to_uint8

rng = np.random.default_rng(0)


def _rgb(h: int = 48, w: int = 40) -> np.ndarray:
    return rng.integers(0, 256, (h, w, 3), dtype=np.uint8)


def test_y_range_matches_bt601():
    black, white = np.zeros((1, 1, 3), np.uint8), np.full((1, 1, 3), 255, np.uint8)
    assert rgb_to_y(black)[0, 0] == pytest.approx(16.0)
    assert rgb_to_y(white)[0, 0] == pytest.approx(235.0)


def test_identical_images():
    img = _rgb()
    s = score(img, img)
    assert s["psnr"] == float("inf") and s["ssim"] == pytest.approx(1.0)


def test_psnr_known_value():
    a = np.zeros((10, 10))
    assert psnr(a, a + 10.0) == pytest.approx(10 * np.log10(255**2 / 100))


def test_clamp_and_round():
    x = np.array([[[-0.5, 0.5, 1.5]]])
    assert to_uint8(x).tolist() == [[[0, 128, 255]]]


def test_border_is_cropped():
    # Damage only the outer 4 px: the score must not notice.
    hr = _rgb()
    sr = hr.copy()
    sr[:4], sr[-4:], sr[:, :4], sr[:, -4:] = 0, 0, 0, 0
    assert score(sr, hr)["psnr"] == float("inf")


def test_shape_mismatch_raises():
    with pytest.raises(ValueError):
        score(_rgb(48, 40), _rgb(48, 44))


def test_ssim_matches_skimage():
    # Cross-check against an independent implementation with the same settings.
    skm = pytest.importorskip("skimage.metrics")
    a = rgb_to_y(_rgb(64, 64))
    b = np.clip(a + rng.normal(0, 8, a.shape), 0, 255)
    ref = skm.structural_similarity(
        a, b, data_range=255, gaussian_weights=True, sigma=1.5, use_sample_covariance=False
    )
    assert ssim(a, b) == pytest.approx(ref, abs=1e-6)
