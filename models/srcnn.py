"""SRCNN: three convolutions on the bicubic-upsampled Y channel (Dong et al., TPAMI 2016).

The LR image is enlarged with bicubic first. The network then only has to restore the
high frequencies that upsample lost, which is why a 9×9, 5×5, 5×5 stack is enough.
Colour is not learned: Cb and Cr are copied from that same bicubic upsample.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torch import nn

from data.color import rgb_to_ycbcr, ycbcr_to_rgb
from data.degrade import SCALE, to_float


class SRCNN(nn.Module):
    """Y in, Y out, same height and width.

    Kernels are valid (no internal padding), as in the paper. A reflect pad of half the
    total shrink is applied first so the output still lines up with the HR image: `score`
    rejects a shape mismatch, and the paper's unpadded stack would be 16 px smaller.
    """

    def __init__(
        self,
        channels: tuple[int, int] = (64, 32),
        kernels: tuple[int, int, int] = (9, 5, 5),
        init_std: float = 0.001,
    ) -> None:
        super().__init__()
        c1, c2 = channels
        k1, k2, k3 = kernels
        if any(k % 2 == 0 for k in kernels):
            raise ValueError(f"kernels {kernels} must be odd so the border pad is symmetric")
        self.kernels = kernels
        self.conv1 = nn.Conv2d(1, c1, k1)
        self.conv2 = nn.Conv2d(c1, c2, k2)
        self.conv3 = nn.Conv2d(c2, 1, k3)
        # 9, 5, 5 shrink by 16, so 8 px of context on each side.
        self.pad = sum(k - 1 for k in kernels) // 2
        self.reset_parameters(init_std)

    def reset_parameters(self, std: float) -> None:
        """Gaussian with a small std, as in the paper. PyTorch's default init is far larger."""
        for layer in (self.conv1, self.conv2, self.conv3):
            nn.init.normal_(layer.weight, mean=0.0, std=std)
            nn.init.zeros_(layer.bias)

    def parameter_groups(self) -> tuple[list[nn.Parameter], list[nn.Parameter]]:
        """Earlier layers, then the reconstruction layer.

        Why split: Dong et al. train the last layer at 10× the learning rate of the first two.
        """
        early = list(self.conv1.parameters()) + list(self.conv2.parameters())
        last = list(self.conv3.parameters())
        return early, last

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.shape[-2] <= self.pad or x.shape[-1] <= self.pad:
            raise ValueError(f"input {tuple(x.shape)} is smaller than the reflect pad ({self.pad} px)")
        x = F.pad(x, (self.pad, self.pad, self.pad, self.pad), mode="reflect")
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        return self.conv3(x)


def srcnn_from_config(cfg: dict) -> SRCNN:
    """Build the architecture described by a training config. Hyperparameters stay in the YAML."""
    model_cfg = cfg["model"]
    channels = tuple(int(c) for c in model_cfg["channels"])
    kernels = tuple(int(k) for k in model_cfg["kernels"])
    if len(channels) != 2 or len(kernels) != 3:
        raise ValueError("model.channels must be [c1, c2] and model.kernels [k1, k2, k3]")
    return SRCNN(channels=channels, kernels=kernels, init_std=float(model_cfg["init_std"]))


def upscale_image(model: SRCNN, lr: Image.Image) -> np.ndarray:
    """LR PIL image -> float RGB HxWx3 in [0, 1] at ×4.

    Sets `eval`. The caller that is training must switch back to `train` afterwards.
    Y is predicted; Cb and Cr come from the bicubic upsample. RGB order is kept
    (a BGR frame would swap the red and blue weights in the Y matrix).
    """
    model.eval()
    width, height = lr.size
    bicubic = lr.resize((width * SCALE, height * SCALE), resample=Image.Resampling.BICUBIC)
    ycbcr = rgb_to_ycbcr(to_float(bicubic))
    y = torch.from_numpy(np.ascontiguousarray(ycbcr[..., 0] / 255.0, dtype=np.float32))
    y = y[None, None]
    device = next(model.parameters()).device
    with torch.no_grad():
        predicted = model(y.to(device))
    y_hat = predicted.detach().float().cpu().numpy()[0, 0] * 255.0
    ycbcr = np.array(ycbcr, copy=True)
    ycbcr[..., 0] = y_hat
    rgb = ycbcr_to_rgb(ycbcr)
    return np.clip(rgb, 0.0, 1.0).astype(np.float32)


def save_checkpoint(path: Path, model: SRCNN, cfg: dict, epoch: int, val_psnr: float) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {"model": model.state_dict(), "config": cfg, "epoch": epoch, "val_psnr": val_psnr},
        path,
    )


def load_upscaler(checkpoint: Path, device: torch.device | None = None) -> tuple:
    """Load a checkpoint and return (upscale, train_data, param_count) for `eval.py`.

    `weights_only` is off because the checkpoint stores the YAML config next to the weights,
    and the config is what rebuilds the matching architecture.
    """
    ckpt = torch.load(Path(checkpoint), map_location="cpu", weights_only=False)
    cfg = ckpt["config"]
    model = srcnn_from_config(cfg)
    model.load_state_dict(ckpt["model"])
    if device is None:
        device = pick_device("auto")
    model.to(device)
    model.eval()
    params = sum(p.numel() for p in model.parameters())
    train_data = str(cfg.get("train_data", "DIV2K"))

    def upscale(lr: Image.Image) -> np.ndarray:
        return upscale_image(model, lr)

    return upscale, train_data, params


def pick_device(requested: str) -> torch.device:
    """`auto` is CUDA, then Apple MPS, then CPU. Timing still belongs to `bench/`, not here."""
    if requested == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        if torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")
    return torch.device(requested)
