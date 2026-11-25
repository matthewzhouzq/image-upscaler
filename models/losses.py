"""Losses for the GAN phase: perceptual (VGG features) and adversarial.

Why not just L1: when many sharp textures are plausible, the pixel loss is lowest for their
average, which is blur. A perceptual loss compares what a pretrained classifier "sees", and the
adversarial loss punishes outputs a discriminator can tell from real photos.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import nn

# ImageNet statistics VGG was trained with. Inputs must be normalized the same way.
_MEAN = (0.485, 0.456, 0.406)
_STD = (0.229, 0.224, 0.225)


class VGGPerceptualLoss(nn.Module):
    """L1 between VGG19 conv5_4 features, before the ReLU (ESRGAN, Wang et al. 2018).

    Before the ReLU because many activations are negative there, and the ReLU would throw that
    signal away. The VGG is frozen: it is a fixed ruler, not something we train.
    `pretrained=False` gives random weights, for tests that must not download ~550 MB.
    """

    def __init__(self, pretrained: bool = True) -> None:
        super().__init__()
        from torchvision.models import VGG19_Weights, vgg19

        weights = VGG19_Weights.IMAGENET1K_V1 if pretrained else None
        # features[34] is conv5_4; slicing to 35 stops right after it, before its ReLU.
        self.features = vgg19(weights=weights).features[:35].eval()
        for p in self.features.parameters():
            p.requires_grad_(False)
        self.register_buffer("mean", torch.tensor(_MEAN).view(1, 3, 1, 1))
        self.register_buffer("std", torch.tensor(_STD).view(1, 3, 1, 1))

    def train(self, mode: bool = True) -> VGGPerceptualLoss:
        super().train(mode)
        self.features.eval()  # keep the ruler fixed even when the training loop calls .train()
        return self

    def forward(self, sr: torch.Tensor, hr: torch.Tensor) -> torch.Tensor:
        sr_feat = self.features((sr - self.mean) / self.std)
        with torch.no_grad():
            hr_feat = self.features((hr - self.mean) / self.std)
        return F.l1_loss(sr_feat, hr_feat)


def discriminator_loss(real_logits: torch.Tensor, fake_logits: torch.Tensor) -> torch.Tensor:
    """Standard GAN loss for D: push real patches toward 1 and generated ones toward 0."""
    real = F.binary_cross_entropy_with_logits(real_logits, torch.ones_like(real_logits))
    fake = F.binary_cross_entropy_with_logits(fake_logits, torch.zeros_like(fake_logits))
    return real + fake


def generator_adversarial_loss(fake_logits: torch.Tensor) -> torch.Tensor:
    """G wins when D calls its output real."""
    return F.binary_cross_entropy_with_logits(fake_logits, torch.ones_like(fake_logits))
