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
    w, h = hr.size  # PIL gives (width, height)
    # Trim the remainder off the right and bottom edges, so pixel (0, 0) stays where it is.
    return hr.crop((0, 0, w - w % scale, h - h % scale))


def bicubic_downscale(hr: Image.Image, scale: int = SCALE) -> Image.Image:
    """Shrink HR by `scale` with antialiased bicubic.

    Why Pillow: when shrinking, it blurs (low-pass filters) before sampling, as MATLAB's imresize does.
    torch's F.interpolate(mode="bicubic") does not unless antialias=True, and the aliasing shows up in PSNR.
    """
    w, h = hr.size
    if w % scale or h % scale:
        # Fail loudly: silently rounding here would give an LR that no longer lines up with HR.
        raise ValueError(f"HR size {hr.size} not divisible by {scale}; call modcrop first")
    return hr.resize((w // scale, h // scale), resample=Image.Resampling.BICUBIC)


def make_lr_hr_pair(path: str, scale: int = SCALE) -> tuple[Image.Image, Image.Image]:
    """Load an image file and return (lr, hr), with hr already modcropped. Use this everywhere."""
    # convert("RGB") drops alpha and palettes and keeps RGB order (OpenCV would give BGR).
    hr = modcrop(Image.open(path).convert("RGB"), scale)
    return bicubic_downscale(hr, scale), hr


def to_float(img: Image.Image) -> np.ndarray:
    """uint8 PIL image -> float32 HxWxC array in [0, 1]. The ONE place we divide by 255."""
    return np.asarray(img, dtype=np.float32) / 255.0
