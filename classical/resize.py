"""Separable bicubic and Lanczos resize. The kernels are written out so we can compare them to Pillow.

Keys cubic with a = -0.5 is the Catmull-Rom kernel Pillow calls BICUBIC. Lanczos-3 is Pillow's
LANCZOS. Pixel centers follow Pillow: output pixel i is read from input coordinate (i + 0.5) * scale,
and taps that fall off the edge are dropped and the rest renormalized.
"""

from __future__ import annotations

import numpy as np

from data.degrade import SCALE


def keys_kernel(a: float):
    """Cubic convolution weight. a = -0.5 is Catmull-Rom; a = -1 is the sharper Keys cubic."""

    def kernel(x: np.ndarray) -> np.ndarray:
        x = np.abs(np.asarray(x, dtype=np.float64))
        x2 = x * x
        x3 = x2 * x
        weight = np.zeros_like(x)
        near = x <= 1.0
        mid = (x > 1.0) & (x < 2.0)
        weight[near] = ((a + 2.0) * x3 - (a + 3.0) * x2 + 1.0)[near]
        weight[mid] = (a * x3 - 5.0 * a * x2 + 8.0 * a * x - 4.0 * a)[mid]
        return weight

    return kernel


def lanczos_kernel(lobes: int):
    """Lanczos window of `lobes` sincs. Three lobes is the usual image kernel."""

    def kernel(x: np.ndarray) -> np.ndarray:
        x = np.abs(np.asarray(x, dtype=np.float64))
        weight = np.ones_like(x)
        nonzero = x != 0.0
        inside = nonzero & (x < lobes)
        pix = np.pi * x[inside]
        weight[inside] = (np.sin(pix) / pix) * (np.sin(pix / lobes) / (pix / lobes))
        weight[x >= lobes] = 0.0
        return weight

    return kernel


def _resample_axis(image: np.ndarray, out_len: int, axis: int, kernel, support: float) -> np.ndarray:
    moved = np.moveaxis(image, axis, -1)
    in_len = moved.shape[-1]
    if out_len <= 0 or in_len <= 0:
        raise ValueError(f"cannot resample axis of length {in_len} to {out_len}")
    scale = in_len / out_len
    # Downscaling stretches the kernel (antialias). Upscaling keeps the kernel at its native width.
    filterscale = scale if scale > 1.0 else 1.0
    support_px = support * filterscale
    centers = (np.arange(out_len) + 0.5) * scale
    xmin = np.floor(centers - support_px + 0.5).astype(int)
    xmax = np.floor(centers + support_px + 0.5).astype(int)
    np.clip(xmin, 0, in_len, out=xmin)
    np.clip(xmax, 0, in_len, out=xmax)
    ksize = int(np.ceil(support_px)) * 2 + 1
    index = xmin[:, None] + np.arange(ksize)[None, :]
    valid = index < xmax[:, None]
    distance = (index + 0.5 - centers[:, None]) / filterscale
    weight = np.where(valid, kernel(distance), 0.0)
    total = weight.sum(axis=1, keepdims=True)
    weight = np.divide(weight, total, out=np.zeros_like(weight), where=total != 0)
    gathered = np.take(moved, np.clip(index, 0, in_len - 1), axis=-1)
    resampled = np.sum(gathered * weight, axis=-1)
    return np.moveaxis(resampled, -1, axis)


def resize(image: np.ndarray, out_h: int, out_w: int, kernel, support: float) -> np.ndarray:
    """Float HxWxC image -> float out_h x out_w x C. Width first, then height, same as Pillow."""
    image = np.asarray(image, dtype=np.float64)
    if image.ndim != 3:
        raise ValueError(f"expected HxWxC, got {image.shape}")
    out = _resample_axis(image, out_w, 1, kernel, support)
    return _resample_axis(out, out_h, 0, kernel, support)


def upsample(image: np.ndarray, kernel, support: float, scale: int = SCALE) -> np.ndarray:
    height, width = image.shape[:2]
    return resize(image, height * scale, width * scale, kernel, support)
