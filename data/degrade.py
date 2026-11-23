"""The ONE shared HR -> LR degradation used for all test inputs (see CLAUDE.md, Evaluation contract).

Every method, classical or learned, must get its LR inputs from `make_lr_hr_pair`, so results are comparable.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

SCALE = 4


def modcrop(hr: Image.Image, scale: int = SCALE) -> Image.Image:
    """Crop HR so width and height are both divisible by `scale`.

    Why: if HR is 103 px wide, LR becomes 25 px, and 25 x 4 = 100 != 103. The metric code
    would then have to pad or resize, which shifts every pixel.
    """
    # TODO: crop from the bottom-right, so pixel (0, 0) stays where it is.
    # Hints: `hr.size` is (width, height), not (height, width).
    #        `hr.crop((left, top, right, bottom))` returns a new image.
    raise NotImplementedError


def bicubic_downscale(hr: Image.Image, scale: int = SCALE) -> Image.Image:
    """Shrink HR by `scale` with antialiased bicubic.

    Why Pillow: when shrinking, it blurs (low-pass filters) before sampling, as MATLAB's imresize does.
    torch's F.interpolate(mode="bicubic") does not unless antialias=True, and the aliasing shows up in PSNR.
    """
    # TODO: 1. If either side isn't divisible by `scale`, raise ValueError (the caller forgot modcrop).
    #       2. Return hr.resize((new_w, new_h), resample=Image.Resampling.BICUBIC).
    raise NotImplementedError


def make_lr_hr_pair(path: str, scale: int = SCALE) -> tuple[Image.Image, Image.Image]:
    """Load an image file and return (lr, hr), with hr already modcropped. Use this everywhere."""
    # TODO: open the file, convert it to "RGB" (drops alpha and palettes; keeps RGB order, not BGR),
    #       modcrop it, then downscale it.
    raise NotImplementedError


def to_float(img: Image.Image) -> np.ndarray:
    """uint8 PIL image -> float32 HxWxC array in [0, 1]. The ONE place we divide by 255."""
    # TODO: np.asarray(...) with dtype float32, then divide by 255.
    raise NotImplementedError
