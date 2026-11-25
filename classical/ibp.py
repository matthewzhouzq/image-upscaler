"""Iterative back-projection (Irani and Peleg).

Start from an upsampled image. Each step blurs and subsamples it, compares that to the real
low-resolution image, and adds the upsampled error back. The forward blur is Pillow bicubic
in float, the same resize that built the test inputs, so the iteration is inverting the
degradation we actually score. Rounding to uint8 inside the loop would wipe out the residual.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

from data.degrade import SCALE


def pillow_bicubic(image: np.ndarray, out_w: int, out_h: int) -> np.ndarray:
    """Float HxWxC -> float out_h x out_w x C through Pillow's BICUBIC, one channel at a time.

    Mode F keeps the residual in float. Mode RGB would quantize to 8 bits and the update would stall.
    """
    planes = []
    for channel in range(image.shape[2]):
        plane = Image.fromarray(np.ascontiguousarray(image[..., channel], dtype=np.float32), mode="F")
        plane = plane.resize((out_w, out_h), resample=Image.Resampling.BICUBIC)
        planes.append(np.asarray(plane, dtype=np.float64))
    return np.stack(planes, axis=-1)


def back_project(lr: np.ndarray, upsample, iterations: int, step: float) -> np.ndarray:
    """Refine an upsampled image so that, downscaled, it matches `lr`.

    `upsample(image)` must return the ×4 image. `step` damps the update: 1 is the plain
    Irani-Peleg step, and a smaller value stays stable when the up and down kernels differ.
    """
    if iterations < 1:
        raise ValueError("iterations must be at least 1")
    height, width = lr.shape[:2]
    estimate = upsample(lr)
    expected = (height * SCALE, width * SCALE)
    if estimate.shape[:2] != expected:
        raise ValueError(f"upsample returned {estimate.shape[:2]}, expected {expected}")
    for _ in range(iterations):
        residual = lr - pillow_bicubic(estimate, width, height)
        estimate = estimate + step * upsample(residual)
    return estimate
