"""Second-order "real-world" degradation for TRAINING ONLY (Real-ESRGAN, Wang et al. 2021).

Real photos are not clean bicubic shrinks. A camera blurs, the image gets resized, sensor noise
appears, it is saved as JPEG, and then often the whole chain happens again when it is re-shared.
Training on random draws of that chain teaches the generator to clean up real inputs.

Contract note: the official test LR still comes from `data.degrade.make_lr_hr_pair`. This module
must never be used to build eval inputs. It uses torch resizes on purpose, because the point
is variety, not matching the shared bicubic.
"""

from __future__ import annotations

import io
import math
from dataclasses import dataclass, fields
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

from data.dataset import SRPatchDataset, _augment, pil_to_tensor
from data.degrade import SCALE, modcrop

RESIZE_MODES = ("area", "bilinear", "bicubic")


@dataclass(frozen=True)
class StageConfig:
    """Ranges for one pass of blur -> resize -> noise. Defaults follow Real-ESRGAN's first stage.

    `resize_probs` is (up, down, keep). Sigmas are in pixels; `noise_sigma` is on the 0-255 scale.
    """

    blur_prob: float = 1.0
    kernel_size: tuple[int, int] = (7, 21)
    sigma: tuple[float, float] = (0.2, 3.0)
    aniso_prob: float = 0.5
    resize_probs: tuple[float, float, float] = (0.2, 0.7, 0.1)
    resize_up: tuple[float, float] = (1.0, 1.5)
    resize_down: tuple[float, float] = (0.15, 1.0)
    gauss_noise_prob: float = 0.5
    noise_sigma: tuple[float, float] = (1.0, 30.0)
    poisson_scale: tuple[float, float] = (0.05, 3.0)
    gray_noise_prob: float = 0.4

    @classmethod
    def from_dict(cls, values: dict | None) -> StageConfig:
        """Build from YAML. Unknown keys are an error, so a typo cannot silently fall back to a default."""
        values = dict(values or {})
        known = {f.name for f in fields(cls)}
        unknown = set(values) - known
        if unknown:
            raise ValueError(f"unknown degradation keys: {', '.join(sorted(unknown))}")
        cast = {k: tuple(v) if isinstance(v, list) else v for k, v in values.items()}
        return cls(**cast)


@dataclass(frozen=True)
class DegradationConfig:
    stage1: StageConfig = StageConfig()
    stage2: StageConfig = StageConfig(
        blur_prob=0.8,
        sigma=(0.2, 1.5),
        resize_probs=(0.3, 0.4, 0.3),
        resize_up=(1.0, 1.2),
        resize_down=(0.3, 1.0),
        noise_sigma=(1.0, 25.0),
        poisson_scale=(0.05, 2.5),
    )
    jpeg_quality: tuple[int, int] = (30, 95)

    @classmethod
    def from_dict(cls, values: dict | None) -> DegradationConfig:
        values = dict(values or {})
        default = cls()
        unknown = set(values) - {"stage1", "stage2", "jpeg_quality"}
        if unknown:
            raise ValueError(f"unknown degradation keys: {', '.join(sorted(unknown))}")

        def merged(name: str) -> StageConfig:
            base = {f.name: getattr(getattr(default, name), f.name) for f in fields(StageConfig)}
            return StageConfig.from_dict({**base, **(values.get(name) or {})})

        quality = tuple(int(q) for q in values.get("jpeg_quality", default.jpeg_quality))
        return cls(stage1=merged("stage1"), stage2=merged("stage2"), jpeg_quality=quality)


def gaussian_kernel(size: int, sigma_x: float, sigma_y: float, theta: float) -> torch.Tensor:
    """size x size Gaussian, stretched along two axes and rotated by `theta`. Sums to 1.

    sigma_x == sigma_y is the usual round blur. Unequal sigmas give motion-like, directional blur.
    """
    if size % 2 == 0:
        raise ValueError("kernel size must be odd, so the kernel has a center pixel")
    half = size // 2
    ax = torch.arange(-half, half + 1, dtype=torch.float64)
    yy, xx = torch.meshgrid(ax, ax, indexing="ij")
    cos, sin = math.cos(theta), math.sin(theta)
    u = cos * xx + sin * yy  # coordinates in the rotated frame
    v = -sin * xx + cos * yy
    kernel = torch.exp(-0.5 * ((u / sigma_x) ** 2 + (v / sigma_y) ** 2))
    return (kernel / kernel.sum()).float()


def _blur(img: torch.Tensor, stage: StageConfig, rng: np.random.Generator) -> torch.Tensor:
    lo, hi = stage.kernel_size
    size = int(rng.choice(np.arange(lo, hi + 1, 2)))
    if rng.random() < stage.aniso_prob:
        sx, sy = rng.uniform(*stage.sigma, size=2)
        theta = float(rng.uniform(-math.pi, math.pi))
    else:
        sx = sy = float(rng.uniform(*stage.sigma))
        theta = 0.0
    kernel = gaussian_kernel(size, float(sx), float(sy), theta)
    weight = kernel.expand(3, 1, size, size)
    pad = size // 2
    # Reflect padding needs the image larger than the pad; tiny late-stage images fall back to replicate.
    mode = "reflect" if min(img.shape[-2:]) > pad else "replicate"
    padded = F.pad(img[None], (pad, pad, pad, pad), mode=mode)
    return F.conv2d(padded, weight, groups=3)[0]


def _resize(img: torch.Tensor, size: tuple[int, int], rng: np.random.Generator) -> torch.Tensor:
    """Resize with a random kernel. Antialias on shrinks, so this is varied, not aliased."""
    h, w = max(1, size[0]), max(1, size[1])
    mode = str(rng.choice(RESIZE_MODES))
    if mode == "area":
        out = F.interpolate(img[None], size=(h, w), mode="area")
    else:
        shrinking = h < img.shape[-2] or w < img.shape[-1]
        out = F.interpolate(img[None], size=(h, w), mode=mode, align_corners=False, antialias=shrinking)
    return out[0].clamp(0.0, 1.0)


def _noise(img: torch.Tensor, stage: StageConfig, rng: np.random.Generator) -> torch.Tensor:
    """Gaussian (read noise) or Poisson (shot noise). Gray noise is the same on all three channels."""
    gray = rng.random() < stage.gray_noise_prob
    shape = (1, *img.shape[1:]) if gray else tuple(img.shape)
    if rng.random() < stage.gauss_noise_prob:
        sigma = float(rng.uniform(*stage.noise_sigma)) / 255.0
        noise = torch.from_numpy(rng.normal(0.0, sigma, size=shape).astype(np.float32))
    else:
        scale = float(rng.uniform(*stage.poisson_scale))
        base = img.mean(dim=0, keepdim=True) if gray else img
        counts = rng.poisson(base.numpy().astype(np.float64) * 255.0)
        noise = (torch.from_numpy(counts.astype(np.float32)) / 255.0 - base) * scale
    return (img + noise.expand_as(img)).clamp(0.0, 1.0)


def _jpeg(img: torch.Tensor, quality: int) -> torch.Tensor:
    """Round-trip through a real JPEG encoder, so the block artifacts are the genuine ones."""
    array = (img.permute(1, 2, 0).numpy() * 255.0).round().clip(0, 255).astype(np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(array).save(buffer, format="JPEG", quality=int(quality))
    buffer.seek(0)
    with Image.open(buffer) as decoded:
        return pil_to_tensor(decoded.convert("RGB"))


def _stage(img: torch.Tensor, stage: StageConfig, target: tuple[int, int], rng: np.random.Generator) -> torch.Tensor:
    """One blur -> resize -> noise pass. The resize factor is relative to `target`."""
    if rng.random() < stage.blur_prob:
        img = _blur(img, stage, rng)
    kind = rng.choice(3, p=np.asarray(stage.resize_probs) / sum(stage.resize_probs))
    factor = 1.0
    if kind == 0:
        factor = float(rng.uniform(*stage.resize_up))
    elif kind == 1:
        factor = float(rng.uniform(*stage.resize_down))
    img = _resize(img, (round(target[0] * factor), round(target[1] * factor)), rng)
    return _noise(img, stage, rng)


def degrade(hr: torch.Tensor, cfg: DegradationConfig, rng: np.random.Generator, scale: int = SCALE) -> torch.Tensor:
    """HR CHW float in [0, 1] -> degraded LR at exactly 1/scale of its size.

    Stage 1 resizes relative to HR, stage 2 relative to the final LR size, then a last resize lands
    on the exact LR grid and a JPEG pass goes on top. Exact size matters: the generator's ×4 output
    has to line up pixel for pixel with the HR patch in the loss.
    """
    h, w = hr.shape[-2:]
    if h % scale or w % scale:
        raise ValueError(f"HR size {(h, w)} not divisible by {scale}")
    lr_size = (h // scale, w // scale)
    img = _stage(hr, cfg.stage1, (h, w), rng)
    img = _jpeg(img, int(rng.integers(cfg.jpeg_quality[0], cfg.jpeg_quality[1] + 1)))
    img = _stage(img, cfg.stage2, lr_size, rng)
    img = _resize(img, lr_size, rng)
    return _jpeg(img, int(rng.integers(cfg.jpeg_quality[0], cfg.jpeg_quality[1] + 1)))


class RealWorldPatchDataset(SRPatchDataset):
    """Random HR crops with LR from the random second-order chain instead of the shared bicubic.

    Same seeding, epochs and augmentations as `SRPatchDataset`. Only the LR recipe differs.
    """

    def __init__(
        self,
        hr_dir: str | Path,
        patch_size: int,
        patches_per_epoch: int,
        degradation: DegradationConfig,
        scale: int = SCALE,
        augment: bool = True,
        seed: int = 0,
    ) -> None:
        super().__init__(hr_dir, patch_size, patches_per_epoch, scale=scale, augment=augment, seed=seed, samples="lr")
        self.degradation = degradation

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        rng = self._rng(index)
        path = self.paths[int(rng.integers(0, len(self.paths)))]
        with Image.open(path) as image:
            hr = modcrop(image.convert("RGB"), self.scale)
            hr.load()
        width, height = hr.size
        if width < self.patch_size or height < self.patch_size:
            raise ValueError(f"{path.name} is {hr.size}; smaller than a {self.patch_size}px patch")
        left = int(rng.integers(0, width - self.patch_size + 1))
        top = int(rng.integers(0, height - self.patch_size + 1))
        hr = hr.crop((left, top, left + self.patch_size, top + self.patch_size))
        if self.augment:
            hr = _augment(hr, rng)
        hr_tensor = pil_to_tensor(hr)
        return degrade(hr_tensor, self.degradation, rng, self.scale), hr_tensor
