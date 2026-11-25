import numpy as np
import pytest
import torch
from PIL import Image

from data.realworld import DegradationConfig, RealWorldPatchDataset, StageConfig, degrade, gaussian_kernel


def _hr(h=64, w=48, seed=0):
    return torch.from_numpy(np.random.default_rng(seed).random((3, h, w), dtype=np.float32))


def test_kernel_sums_to_one_and_is_rotated():
    k = gaussian_kernel(15, 3.0, 0.5, theta=0.0)
    assert float(k.sum()) == pytest.approx(1.0, abs=1e-6)
    # Wide in x, narrow in y: more weight along the middle row than the middle column.
    assert float(k[7].sum()) > float(k[:, 7].sum())
    turned = gaussian_kernel(15, 3.0, 0.5, theta=np.pi / 2)
    assert torch.allclose(turned, k.T, atol=1e-6)


def test_even_kernel_rejected():
    with pytest.raises(ValueError):
        gaussian_kernel(8, 1.0, 1.0, 0.0)


def test_degrade_lands_on_exact_lr_grid():
    # The generator's ×4 output must line up with HR pixel for pixel, whatever the random chain did.
    cfg = DegradationConfig()
    for seed in range(20):
        lr = degrade(_hr(), cfg, np.random.default_rng(seed))
        assert lr.shape == (3, 16, 12)
        assert 0.0 <= float(lr.min()) and float(lr.max()) <= 1.0


def test_degrade_is_reproducible_from_the_rng():
    cfg = DegradationConfig()
    a = degrade(_hr(), cfg, np.random.default_rng(7))
    b = degrade(_hr(), cfg, np.random.default_rng(7))
    assert torch.equal(a, b)


def test_degradation_actually_degrades():
    # Real-world LR should be further from the clean HR than a plain area downscale is.
    hr = _hr(128, 128)
    clean = torch.nn.functional.interpolate(hr[None], size=(32, 32), mode="area")[0]
    lr = degrade(hr, DegradationConfig(), np.random.default_rng(1))
    assert float((lr - clean).abs().mean()) > 0.01


def test_rejects_uncropped_hr():
    with pytest.raises(ValueError):
        degrade(_hr(63, 48), DegradationConfig(), np.random.default_rng(0))


def test_config_merges_yaml_over_defaults_and_catches_typos():
    cfg = DegradationConfig.from_dict({"stage2": {"blur_prob": 0.0}, "jpeg_quality": [50, 60]})
    assert cfg.stage2.blur_prob == 0.0
    assert cfg.stage2.sigma == DegradationConfig().stage2.sigma  # untouched keys keep stage-2 defaults
    assert cfg.jpeg_quality == (50, 60)
    with pytest.raises(ValueError):
        StageConfig.from_dict({"blur_probb": 1.0})
    with pytest.raises(ValueError):
        DegradationConfig.from_dict({"stage3": {}})


def test_dataset_pairs_have_matching_sizes(tmp_path):
    rng = np.random.default_rng(0)
    for i in range(2):
        Image.fromarray(rng.integers(0, 256, (70, 90, 3), dtype=np.uint8)).save(tmp_path / f"{i}.png")
    ds = RealWorldPatchDataset(tmp_path, patch_size=32, patches_per_epoch=4, degradation=DegradationConfig())
    lr, hr = ds[0]
    assert hr.shape == (3, 32, 32) and lr.shape == (3, 8, 8)
    lr2, hr2 = ds[0]
    assert torch.equal(lr, lr2) and torch.equal(hr, hr2)  # same index, same epoch, same sample
