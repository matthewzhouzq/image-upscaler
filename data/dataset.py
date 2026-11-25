"""Random ×4 training patches. LR always comes from the shared bicubic downscale."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset

from data.degrade import SCALE, bicubic_downscale, modcrop, to_float


def pil_to_tensor(img: Image.Image) -> torch.Tensor:
    """PIL RGB -> CHW float32 in [0, 1]. Uses `to_float`, so 255 is divided in one place."""
    array = np.ascontiguousarray(to_float(img))
    return torch.from_numpy(array).permute(2, 0, 1).contiguous()


def _source_size(patch_size: int, scale: int) -> int:
    """HR crop that can be downscaled and still hold `patch_size` away from the bicubic edge.

    A 33 px patch (the paper's sub-image) is not divisible by 4, so the downscale runs on a
    larger window and the training patch is the center of the upsampled result.
    """
    margin = scale  # one low-resolution pixel of real context on each side
    needed = patch_size + 2 * margin
    remainder = needed % scale
    if remainder:
        needed += scale - remainder
    return needed


def _augment(img: Image.Image, rng: np.random.Generator) -> Image.Image:
    """Flips and 90° turns. Square patches only: a 90° turn of a rectangle would swap the sides."""
    if rng.random() < 0.5:
        img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if rng.random() < 0.5:
        img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    turns = {
        1: Image.Transpose.ROTATE_90,
        2: Image.Transpose.ROTATE_180,
        3: Image.Transpose.ROTATE_270,
    }
    k = int(rng.integers(0, 4))
    if k:
        img = img.transpose(turns[k])
    return img


class SRPatchDataset(Dataset):
    """One epoch is `patches_per_epoch` random crops, not one crop per file.

    Why crop then downscale: the LR patch is made by `bicubic_downscale`, the same function
    `eval.py` uses, so the network cannot win by training on a different resize.
    """

    def __init__(
        self,
        hr_dir: str | Path,
        patch_size: int,
        patches_per_epoch: int,
        scale: int = SCALE,
        augment: bool = True,
        seed: int = 0,
    ) -> None:
        if scale != SCALE:
            raise ValueError(f"scale must be {SCALE}")
        if patch_size < scale:
            raise ValueError(f"patch_size {patch_size} is smaller than scale {scale}")
        self.hr_dir = Path(hr_dir)
        self.paths = sorted(self.hr_dir.glob("*.png"))
        if not self.paths:
            raise FileNotFoundError(f"no .png images in {self.hr_dir}")
        self.patch_size = patch_size
        self.patches_per_epoch = patches_per_epoch
        self.scale = scale
        self.augment = augment
        self.seed = seed
        self.epoch = 0

    def set_epoch(self, epoch: int) -> None:
        """Mix the epoch into the crop seed so the next epoch is not a replay of this one."""
        self.epoch = epoch

    def __len__(self) -> int:
        return self.patches_per_epoch

    def _rng(self, index: int) -> np.random.Generator:
        worker = torch.utils.data.get_worker_info()
        worker_id = 0 if worker is None else worker.id
        sequence = np.random.SeedSequence([self.seed, self.epoch, index, worker_id])
        return np.random.default_rng(sequence)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        """Return (bicubic, hr) at HR resolution, each CHW float in [0, 1].

        SRCNN does not see the small LR. It sees the bicubic upsample, then learns the residual
        detail the upsample missed. The upsample is Pillow bicubic, same as the baseline in eval.
        """
        rng = self._rng(index)
        path = self.paths[int(rng.integers(0, len(self.paths)))]
        with Image.open(path) as image:
            hr = modcrop(image.convert("RGB"), self.scale)
            hr.load()
        window = _source_size(self.patch_size, self.scale)
        width, height = hr.size
        if width < window or height < window:
            raise ValueError(
                f"{path.name} is {hr.size} after modcrop; a {self.patch_size}px patch needs a {window}px crop"
            )
        left = int(rng.integers(0, width - window + 1))
        top = int(rng.integers(0, height - window + 1))
        hr = hr.crop((left, top, left + window, top + window))
        if self.augment:
            hr = _augment(hr, rng)
        lr = bicubic_downscale(hr, self.scale)
        bicubic = lr.resize(hr.size, resample=Image.Resampling.BICUBIC)
        offset = (window - self.patch_size) // 2
        if offset:
            box = (offset, offset, offset + self.patch_size, offset + self.patch_size)
            hr = hr.crop(box)
            bicubic = bicubic.crop(box)
        return pil_to_tensor(bicubic), pil_to_tensor(hr)
