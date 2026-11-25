"""EDSR-lite: residual blocks on the low-resolution image, then a pixel-shuffle upsample.

SRCNN bicubic-upsamples first and runs every convolution on the large grid. This network does the
opposite. The expensive layers stay at LR resolution. Pixel-shuffle is the upsample: a convolution
writes r^2 channels, and those channels are laid out as an r by r spatial block. For ×4 that is
two ×2 shuffles, which is how EDSR does it (Lim et al., CVPRW 2017). One shuffle of 16 channels
would also be ×4; two stages keep each expansion at 4 channels per feature.

A full EDSR baseline (16 blocks, 64 features) is about 32.5 dB on Set5 ×4. Eight blocks will not
match that. Expect a step above SRCNN if it is trained properly, not the published number.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torch import nn

from data.dataset import pil_to_tensor
from data.degrade import SCALE
from models.srcnn import pick_device


class ResidualBlock(nn.Module):
    """Conv, ReLU, conv, then a scaled skip back to the input.

    The scale (0.1 in the paper) keeps a deep stack of skips from exploding. There is no
    batch norm: EDSR removed it because the normalization shifts the residual the skip is trying to learn.
    """

    def __init__(self, n_feats: int, res_scale: float) -> None:
        super().__init__()
        self.conv1 = nn.Conv2d(n_feats, n_feats, 3, padding=1)
        self.conv2 = nn.Conv2d(n_feats, n_feats, 3, padding=1)
        self.res_scale = res_scale

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = self.conv2(F.relu(self.conv1(x)))
        return x + residual * self.res_scale


class EDSRLite(nn.Module):
    """RGB LR in, RGB at ×4 out. The body learns a residual in feature space, then the tail upsamples."""

    def __init__(
        self,
        n_blocks: int,
        n_feats: int,
        res_scale: float,
        rgb_mean: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> None:
        super().__init__()
        if n_blocks < 1:
            raise ValueError("n_blocks must be at least 1")
        if n_feats < 1:
            raise ValueError("n_feats must be at least 1")
        self.head = nn.Conv2d(3, n_feats, 3, padding=1)
        self.body = nn.Sequential(*(ResidualBlock(n_feats, res_scale) for _ in range(n_blocks)))
        self.body_end = nn.Conv2d(n_feats, n_feats, 3, padding=1)
        # ×4 = two ×2 rearrangements. Each conv emits 4 feature-groups; PixelShuffle folds them into space.
        self.up = nn.Sequential(
            nn.Conv2d(n_feats, n_feats * 4, 3, padding=1),
            nn.PixelShuffle(2),
            nn.Conv2d(n_feats, n_feats * 4, 3, padding=1),
            nn.PixelShuffle(2),
        )
        self.tail = nn.Conv2d(n_feats, 3, 3, padding=1)
        mean = torch.tensor(rgb_mean, dtype=torch.float32).view(1, 3, 1, 1)
        self.register_buffer("mean", mean)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Mean is subtracted in LR RGB and added back after the upsample, so the body sees zero-centered colors.
        x = x - self.mean
        skip = self.head(x)
        x = skip + self.body_end(self.body(skip))
        x = self.tail(self.up(x))
        return x + self.mean


def edsr_from_config(cfg: dict) -> EDSRLite:
    """Build the network described by a training config. Depth, width, and the residual scale stay in YAML."""
    model_cfg = cfg["model"]
    mean = tuple(float(value) for value in model_cfg.get("rgb_mean", (0.0, 0.0, 0.0)))
    if len(mean) != 3:
        raise ValueError("model.rgb_mean must be three numbers")
    return EDSRLite(
        n_blocks=int(model_cfg["n_blocks"]),
        n_feats=int(model_cfg["n_feats"]),
        res_scale=float(model_cfg["res_scale"]),
        rgb_mean=mean,
    )


def upscale_image(model: EDSRLite, lr: Image.Image) -> np.ndarray:
    """LR PIL image -> float RGB HxWx3 in [0, 1] at ×4.

    Sets `eval`. The training loop switches back to `train` afterwards. RGB order is unchanged.
    """
    model.eval()
    tensor = pil_to_tensor(lr).unsqueeze(0)
    device = next(model.parameters()).device
    with torch.no_grad():
        predicted = model(tensor.to(device)).clamp(0.0, 1.0)
    image = predicted[0].permute(1, 2, 0).detach().cpu().numpy()
    if image.shape[0] != lr.size[1] * SCALE or image.shape[1] != lr.size[0] * SCALE:
        raise RuntimeError(f"EDSR output {image.shape[:2]} is not ×{SCALE} of {lr.size}")
    return image.astype(np.float32)


def load_upscaler(checkpoint: Path, device: torch.device | None = None) -> tuple:
    """Load a checkpoint and return (upscale, train_data, param_count, method_name).

    The method name comes from the saved config, so an ablation checkpoint does not overwrite
    the main EDSR-lite row. `weights_only` is off because the config is stored beside the weights.
    """
    ckpt = torch.load(Path(checkpoint), map_location="cpu", weights_only=False)
    cfg = ckpt["config"]
    model = edsr_from_config(cfg)
    model.load_state_dict(ckpt["model"])
    if device is None:
        device = pick_device("auto")
    model.to(device)
    model.eval()
    params = sum(p.numel() for p in model.parameters())
    train_data = str(cfg.get("train_data", "DIV2K"))
    method_name = str(cfg.get("method", "edsr-lite"))

    def upscale(lr: Image.Image) -> np.ndarray:
        return upscale_image(model, lr)

    return upscale, train_data, params, method_name
