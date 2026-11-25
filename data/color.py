"""MATLAB rgb2ycbcr, shared by training and inference.

SRCNN learns the Y channel only. This has to be the same BT.601 matrix as
`metrics.rgb_to_y`, or we would train on one luminance and score another.
"""

from __future__ import annotations

import numpy as np
import torch

# Rows are R, G, B. Columns are Y, Cb, Cr. rgb @ _M + _BIAS matches MATLAB
# rgb2ycbcr for RGB in [0, 1]: Y lands in [16, 235], Cb/Cr around [16, 240].
_M = np.array(
    [
        [65.481, -37.797, 112.0],
        [128.553, -74.203, -93.786],
        [24.966, 112.0, -18.214],
    ],
    dtype=np.float64,
)
_BIAS = np.array([16.0, 128.0, 128.0], dtype=np.float64)
_INV = np.linalg.inv(_M)


def rgb_to_ycbcr(rgb: np.ndarray) -> np.ndarray:
    """Float RGB HxWx3 in [0, 1] -> YCbCr in MATLAB's 0-255 units."""
    return np.asarray(rgb, dtype=np.float64) @ _M + _BIAS


def ycbcr_to_rgb(ycbcr: np.ndarray) -> np.ndarray:
    """Inverse of `rgb_to_ycbcr`. Result is float RGB, not yet clipped."""
    return (np.asarray(ycbcr, dtype=np.float64) - _BIAS) @ _INV


def rgb_tensor_to_y(rgb: torch.Tensor) -> torch.Tensor:
    """N,3,H,W float RGB in [0, 1] -> N,1,H,W Y, divided by 255.

    Why /255: the network trains on a roughly [0, 1] luminance. The 65.481 / 128.553 / 24.966
    weights are the Y column of the matrix above, so this matches `metrics.rgb_to_y`.
    """
    r, g, b = rgb[:, 0:1], rgb[:, 1:2], rgb[:, 2:3]
    y = 16.0 + 65.481 * r + 128.553 * g + 24.966 * b
    return y / 255.0
