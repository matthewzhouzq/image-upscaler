"""PSNR / SSIM exactly as the Evaluation contract in CLAUDE.md defines them.

Pipeline for every method: output -> clamp [0, 1] -> round to uint8 -> Y channel (BT.601) -> crop 4 px -> score.
Only `eval.py` should call `score`, so nothing computes metrics its own way.
"""

from __future__ import annotations

import numpy as np

BORDER = 4


def to_uint8(img: np.ndarray) -> np.ndarray:
    """Float image in [0, 1] -> uint8, clamping first. uint8 input passes through unchanged.

    Why round: real outputs are saved as 8-bit images. Scoring unrounded floats gives slightly
    higher PSNR than anyone could reproduce from the saved files.
    """
    if img.dtype == np.uint8:
        return img
    return np.round(np.clip(img, 0.0, 1.0) * 255.0).astype(np.uint8)


def rgb_to_y(img: np.ndarray) -> np.ndarray:
    """uint8 RGB HxWx3 -> float64 Y (brightness) in [16, 235], via MATLAB rgb2ycbcr / BT.601.

    Why this formula: it's the one SR papers use, so our PSNR is comparable to theirs.
    Expects RGB order: a BGR image from OpenCV would swap the R and B weights with no error.
    """
    if img.ndim != 3 or img.shape[2] != 3 or img.dtype != np.uint8:
        raise ValueError(f"expected uint8 HxWx3 RGB, got {img.dtype} {img.shape}")
    rgb = img.astype(np.float64) / 255.0
    return 16.0 + rgb @ np.array([65.481, 128.553, 24.966])


def _crop(y: np.ndarray, border: int) -> np.ndarray:
    return y[border:-border, border:-border] if border > 0 else y


def psnr(a: np.ndarray, b: np.ndarray) -> float:
    """PSNR in dB between two Y images on the 0-255 scale. Identical images give inf."""
    mse = np.mean((a - b) ** 2)
    return float("inf") if mse == 0 else float(10.0 * np.log10(255.0**2 / mse))


def _gaussian_window(size: int = 11, sigma: float = 1.5) -> np.ndarray:
    x = np.arange(size) - size // 2
    k = np.exp(-(x**2) / (2 * sigma**2))
    return k / k.sum()


def _filter_valid(x: np.ndarray, k: np.ndarray) -> np.ndarray:
    """Gaussian blur in 'valid' mode: only positions where the whole 11x11 window fits.

    Done as two 1-D passes (rows, then columns), which equals one 2-D Gaussian but is faster.
    """
    n = len(k)
    x = np.lib.stride_tricks.sliding_window_view(x, n, axis=0) @ k
    return np.lib.stride_tricks.sliding_window_view(x, n, axis=1) @ k


def ssim(a: np.ndarray, b: np.ndarray) -> float:
    """SSIM (Wang et al. 2004) between two Y images on the 0-255 scale.

    Compares local brightness (means), contrast (variances) and structure (covariance)
    in Gaussian-weighted 11x11 windows, then averages over the image.
    """
    k = _gaussian_window()
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2  # stabilise the division in flat regions
    mu_a, mu_b = _filter_valid(a, k), _filter_valid(b, k)
    var_a = _filter_valid(a * a, k) - mu_a**2
    var_b = _filter_valid(b * b, k) - mu_b**2
    cov = _filter_valid(a * b, k) - mu_a * mu_b
    s = ((2 * mu_a * mu_b + c1) * (2 * cov + c2)) / ((mu_a**2 + mu_b**2 + c1) * (var_a + var_b + c2))
    return float(s.mean())


def score(sr: np.ndarray, hr: np.ndarray, border: int = BORDER) -> dict[str, float]:
    """Score one SR output against its (modcropped) HR. Both HxWx3 RGB, float [0, 1] or uint8."""
    if sr.shape != hr.shape:
        raise ValueError(f"shape mismatch: sr {sr.shape} vs hr {hr.shape} (did you modcrop HR?)")
    y_sr, y_hr = (_crop(rgb_to_y(to_uint8(x)), border) for x in (sr, hr))
    return {"psnr": psnr(y_sr, y_hr), "ssim": ssim(y_sr, y_hr)}
