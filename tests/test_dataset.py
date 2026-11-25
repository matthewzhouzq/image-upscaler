import numpy as np
import pytest
import torch
from PIL import Image

from data.dataset import SRPatchDataset


def _write_images(folder, n=2, size=(80, 64)):
    folder.mkdir(parents=True)
    rng = np.random.default_rng(0)
    for index in range(n):
        pixels = rng.integers(0, 256, (size[1], size[0], 3), dtype=np.uint8)
        Image.fromarray(pixels).save(folder / f"img_{index:03d}.png")
    return folder


def test_paper_patch_is_not_a_multiple_of_four(tmp_path):
    # 33 is the sub-image size from Dong et al. It is not divisible by 4; the crop around it is.
    data = SRPatchDataset(_write_images(tmp_path / "hr"), patch_size=33, patches_per_epoch=1, augment=False, seed=0)
    bicubic, hr = data[0]
    assert bicubic.shape == hr.shape == (3, 33, 33)


def test_pair_shapes_and_range(tmp_path):
    data = SRPatchDataset(_write_images(tmp_path / "hr"), patch_size=32, patches_per_epoch=4, augment=True, seed=1)
    bicubic, hr = data[0]
    assert bicubic.shape == hr.shape == (3, 32, 32)
    assert bicubic.dtype == torch.float32
    assert 0.0 <= float(bicubic.min()) and float(hr.max()) <= 1.0


def test_getitem_is_deterministic_until_epoch_changes(tmp_path):
    data = SRPatchDataset(_write_images(tmp_path / "hr"), patch_size=32, patches_per_epoch=2, seed=3)
    first, _ = data[0]
    again, _ = data[0]
    assert torch.equal(first, again)
    data.set_epoch(1)
    later, _ = data[0]
    assert not torch.equal(first, later)


def test_flat_color_stays_flat(tmp_path):
    folder = tmp_path / "hr"
    folder.mkdir()
    Image.new("RGB", (64, 64), (120, 30, 200)).save(folder / "flat.png")
    data = SRPatchDataset(folder, patch_size=32, patches_per_epoch=1, augment=False, seed=0)
    bicubic, hr = data[0]
    assert torch.allclose(bicubic, hr)
    assert torch.allclose(hr[:, 0, 0], torch.tensor([120, 30, 200], dtype=torch.float32) / 255)


def test_rejects_small_image(tmp_path):
    folder = tmp_path / "hr"
    folder.mkdir()
    Image.new("RGB", (16, 16), (1, 2, 3)).save(folder / "tiny.png")
    data = SRPatchDataset(folder, patch_size=32, patches_per_epoch=1, augment=False)
    with pytest.raises(ValueError):
        data[0]


def test_empty_dir(tmp_path):
    with pytest.raises(FileNotFoundError):
        SRPatchDataset(tmp_path, patch_size=32, patches_per_epoch=1)
