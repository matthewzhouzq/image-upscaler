"""Total-variation reconstruction.

The image we want minimizes

    E(x) = 1/2 ||A x - y||^2  +  λ TV(x)

A is a Gaussian blur followed by ×4 subsampling, y is the low-resolution image, and
TV(x) = Σ sqrt(dx^2 + dy^2) penalizes gradients so the result stays piecewise smooth
instead of oscillating to fit noise. This is the Rudin-Osher-Fatemi idea with a
downsampling operator in the data term.

The solver is a linearized Chambolle-Pock step. The exact prox of ||A x - y||^2 is a
linear system; one gradient step on that term, then a projection of the dual variable
onto the λ-ball, is the same saddle-point iteration with the prox replaced by its
linearization. Forward differences have squared norm at most 8, so the dual step
sizes must satisfy tau * sigma_dual < 1/8.

The blur is circular (wrap-around). That makes A and its adjoint exact transposes of
each other. The scored 4 px border does not cover the whole wrap seam; that is a
property of this solver, not a change to the metric.
"""

from __future__ import annotations

import numpy as np

from classical.resize import keys_kernel, upsample
from data.degrade import SCALE


def gaussian_kernel(sigma: float) -> np.ndarray:
    if sigma <= 0:
        raise ValueError("blur sigma must be positive")
    radius = max(1, int(np.ceil(3.0 * sigma)))
    taps = np.arange(-radius, radius + 1, dtype=np.float64)
    kernel = np.exp(-0.5 * (taps / sigma) ** 2)
    kernel /= kernel.sum()
    return kernel


def _conv_last(moved: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    radius = len(kernel) // 2
    pad = [(0, 0)] * (moved.ndim - 1) + [(radius, radius)]
    padded = np.pad(moved, pad, mode="wrap")
    windows = np.lib.stride_tricks.sliding_window_view(padded, len(kernel), axis=-1)
    return windows @ kernel


def blur(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """Separable circular convolution. A symmetric kernel is its own adjoint."""
    out = np.moveaxis(_conv_last(np.moveaxis(image, 1, -1), kernel), -1, 1)
    return np.moveaxis(_conv_last(np.moveaxis(out, 0, -1), kernel), -1, 0)


def downsample(image: np.ndarray, kernel: np.ndarray, scale: int = SCALE) -> np.ndarray:
    return blur(image, kernel)[::scale, ::scale]


def upsample_adjoint(lr: np.ndarray, kernel: np.ndarray, scale: int = SCALE) -> np.ndarray:
    """Adjoint of `downsample`: insert zeros, then the same blur.

    No extra scale factor. Subsampling's adjoint is zero-insertion, and the blur is symmetric.
    """
    height, width = lr.shape[:2]
    up = np.zeros((height * scale, width * scale, lr.shape[2]), dtype=np.float64)
    up[::scale, ::scale] = lr
    return blur(up, kernel)


def gradient(image: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    gx = np.zeros_like(image)
    gy = np.zeros_like(image)
    gx[:, :-1] = image[:, 1:] - image[:, :-1]
    gy[:-1, :] = image[1:, :] - image[:-1, :]
    return gx, gy


def divergence(px: np.ndarray, py: np.ndarray) -> np.ndarray:
    """Adjoint of `gradient`, with a minus sign: <grad x, p> = -<x, div p>."""
    out = np.zeros_like(px)
    out[:, 0] = px[:, 0]
    out[:, 1:-1] = px[:, 1:-1] - px[:, :-2]
    out[:, -1] = -px[:, -2]
    out[0, :] += py[0, :]
    out[1:-1, :] += py[1:-1, :] - py[:-2, :]
    out[-1, :] += -py[-2, :]
    return out


def energy(image: np.ndarray, lr: np.ndarray, kernel: np.ndarray, lam: float, scale: int = SCALE) -> float:
    residual = downsample(image, kernel, scale) - lr
    data = 0.5 * float(np.sum(residual * residual))
    gx, gy = gradient(image)
    tv = lam * float(np.sum(np.sqrt(gx * gx + gy * gy)))
    return data + tv


def solve(
    lr: np.ndarray,
    blur_sigma: float,
    lam: float,
    iterations: int,
    tau: float,
    sigma_dual: float,
    scale: int = SCALE,
) -> np.ndarray:
    """Minimize the energy above, starting from a Keys-cubic upsample of `lr`."""
    if iterations < 1:
        raise ValueError("iterations must be at least 1")
    if tau * sigma_dual >= 1.0 / 8.0:
        raise ValueError(f"tau * sigma_dual must be < 1/8, got {tau * sigma_dual}")
    kernel = gaussian_kernel(blur_sigma)
    estimate = upsample(lr, keys_kernel(-0.5), support=2.0, scale=scale)
    px = np.zeros_like(estimate)
    py = np.zeros_like(estimate)
    for _ in range(iterations):
        data_grad = upsample_adjoint(downsample(estimate, kernel, scale) - lr, kernel, scale)
        previous = estimate
        # K* p = -div p, and the primal step subtracts tau * K* p.
        estimate = estimate - tau * data_grad + tau * divergence(px, py)
        extrapolated = 2.0 * estimate - previous
        gx, gy = gradient(extrapolated)
        px = px + sigma_dual * gx
        py = py + sigma_dual * gy
        norm = np.sqrt(px * px + py * py)
        px *= np.minimum(1.0, lam / np.maximum(norm, 1e-12))
        py *= np.minimum(1.0, lam / np.maximum(norm, 1e-12))
    return estimate
