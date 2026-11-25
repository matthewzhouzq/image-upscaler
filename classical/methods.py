"""Register the math-track upscalers as eval methods. Hyperparameters stay in configs/."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml
from PIL import Image

from classical.ibp import back_project
from classical.resize import keys_kernel, lanczos_kernel, upsample
from classical.tv import solve
from data.degrade import SCALE, to_float

CLASSICAL_NAMES = ("bicubic-keys", "lanczos", "ibp", "tv")


def load_config(name: str) -> dict:
    path = Path("configs") / name
    with path.open() as handle:
        cfg = yaml.safe_load(handle)
    if not isinstance(cfg, dict):
        raise ValueError(f"{path} did not contain a mapping")
    return cfg


def _as_float(lr: Image.Image) -> np.ndarray:
    return np.asarray(to_float(lr), dtype=np.float64)


def _clip(image: np.ndarray) -> np.ndarray:
    return np.clip(image, 0.0, 1.0).astype(np.float32)


def build_classical_method(name: str):
    """params=0 and train_data=none: nothing here was learned.

    `Method` is imported here, not at module import: eval.py imports this module while it is
    still defining `Method`.
    """
    from eval import Method
    if name == "bicubic-keys":
        cfg = load_config("bicubic_keys.yaml")
        kernel = keys_kernel(float(cfg["a"]))
        support = float(cfg["support"])

        def upscale(lr: Image.Image) -> np.ndarray:
            return _clip(upsample(_as_float(lr), kernel, support, SCALE))

    elif name == "lanczos":
        cfg = load_config("lanczos.yaml")
        lobes = int(cfg["lobes"])
        kernel = lanczos_kernel(lobes)

        def upscale(lr: Image.Image) -> np.ndarray:
            return _clip(upsample(_as_float(lr), kernel, float(lobes), SCALE))

    elif name == "ibp":
        cfg = load_config("ibp.yaml")
        kernel_name = str(cfg["upsample"])
        if kernel_name == "lanczos":
            lobes = int(cfg["lobes"])
            kernel, support = lanczos_kernel(lobes), float(lobes)
        elif kernel_name == "bicubic-keys":
            kernel, support = keys_kernel(float(cfg["a"])), float(cfg["support"])
        else:
            raise ValueError(f"ibp upsample must be lanczos or bicubic-keys, got {kernel_name!r}")
        iterations = int(cfg["iterations"])
        step = float(cfg["step"])

        def upscale(lr: Image.Image) -> np.ndarray:
            image = _as_float(lr)
            estimate = back_project(
                image,
                lambda low: upsample(low, kernel, support, SCALE),
                iterations,
                step,
            )
            return _clip(estimate)

    elif name == "tv":
        cfg = load_config("tv.yaml")

        def upscale(lr: Image.Image) -> np.ndarray:
            estimate = solve(
                _as_float(lr),
                blur_sigma=float(cfg["blur_sigma"]),
                lam=float(cfg["lambda"]),
                iterations=int(cfg["iterations"]),
                tau=float(cfg["tau"]),
                sigma_dual=float(cfg["sigma_dual"]),
                scale=SCALE,
            )
            return _clip(estimate)

    else:
        raise KeyError(name)
    return Method(name, upscale, train_data="none", params=0)
