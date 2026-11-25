"""Patch discriminator for the GAN phase: real HR patch or generated one?

It outputs a grid of logits, one per overlapping region, instead of a single number, so it judges
local texture everywhere rather than the patch as a whole. Every conv uses spectral norm, which
caps how sharply the discriminator can change its mind. That keeps it from overpowering the
generator early on, the usual way GAN training collapses.
"""

from __future__ import annotations

import torch
from torch import nn
from torch.nn.utils import spectral_norm


class PatchDiscriminator(nn.Module):
    """RGB in [0, 1] -> logits at 1/2**n_layers of the input size. Higher means "looks real"."""

    def __init__(self, n_feats: int = 64, n_layers: int = 4) -> None:
        super().__init__()
        if n_layers < 1:
            raise ValueError("n_layers must be at least 1")
        layers: list[nn.Module] = [spectral_norm(nn.Conv2d(3, n_feats, 3, 1, 1)), nn.LeakyReLU(0.2, inplace=True)]
        channels = n_feats
        for _ in range(n_layers):
            out = min(channels * 2, n_feats * 8)
            layers += [
                spectral_norm(nn.Conv2d(channels, out, 4, 2, 1)),  # stride 2 halves the size
                nn.LeakyReLU(0.2, inplace=True),
                spectral_norm(nn.Conv2d(out, out, 3, 1, 1)),
                nn.LeakyReLU(0.2, inplace=True),
            ]
            channels = out
        layers.append(spectral_norm(nn.Conv2d(channels, 1, 3, 1, 1)))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def discriminator_from_config(cfg: dict) -> PatchDiscriminator:
    d_cfg = cfg["discriminator"]
    return PatchDiscriminator(n_feats=int(d_cfg["n_feats"]), n_layers=int(d_cfg["n_layers"]))
