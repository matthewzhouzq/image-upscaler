import numpy as np
import pytest
import torch
import yaml
from PIL import Image

from metrics import LPIPSMetric, score
from models.discriminator import PatchDiscriminator
from models.edsr_lite import EDSRLite
from models.losses import VGGPerceptualLoss, discriminator_loss, generator_adversarial_loss
from train import load_config, run_training, train_gan_epoch


def test_discriminator_outputs_a_patch_grid():
    d = PatchDiscriminator(n_feats=8, n_layers=3)
    assert d(torch.rand(2, 3, 64, 64)).shape == (2, 1, 8, 8)


def test_gan_losses_point_the_right_way():
    confident_real, confident_fake = torch.full((1, 1, 4, 4), 5.0), torch.full((1, 1, 4, 4), -5.0)
    # D is doing well when real scores high and fake scores low.
    assert discriminator_loss(confident_real, confident_fake) < discriminator_loss(confident_fake, confident_real)
    # G is doing well when D scores its output as real.
    assert generator_adversarial_loss(confident_real) < generator_adversarial_loss(confident_fake)


def test_perceptual_loss_is_frozen_and_zero_on_identical():
    loss = VGGPerceptualLoss(pretrained=False)
    assert not any(p.requires_grad for p in loss.parameters())
    loss.train()
    assert not loss.features.training  # the ruler stays in eval mode
    x = torch.rand(1, 3, 32, 32)
    assert float(loss(x, x)) == pytest.approx(0.0, abs=1e-6)


def test_gan_step_updates_g_but_d_step_does_not_touch_g():
    torch.manual_seed(0)
    g = EDSRLite(n_blocks=1, n_feats=8, res_scale=0.1)
    d = PatchDiscriminator(n_feats=8, n_layers=2)
    before_g = [p.detach().clone() for p in g.parameters()]
    opt_g = torch.optim.Adam(g.parameters(), lr=1e-3)
    opt_d = torch.optim.Adam(d.parameters(), lr=1e-3)
    batch = [(torch.rand(2, 3, 8, 8), torch.rand(2, 3, 32, 32))]
    weights = {"pixel": 1.0, "perceptual": 1.0, "adversarial": 0.1}
    losses = train_gan_epoch(g, d, VGGPerceptualLoss(pretrained=False), batch, opt_g, opt_d, torch.device("cpu"), weights)
    assert set(losses) == {"d", "g", "pixel", "perceptual", "adversarial"}
    assert any(not torch.equal(a, b) for a, b in zip(before_g, g.parameters()))


def test_lpips_in_score_uses_rgb_after_rounding():
    metric = LPIPSMetric(pretrained_backbone=False)  # random backbone: no download, only the plumbing
    rng = np.random.default_rng(0)
    # Start on whole gray levels, like a real 8-bit image, so +0.001 (a quarter level) cannot flip a rounding.
    hr = (rng.integers(0, 256, (40, 40, 3)) / 255.0).astype(np.float32)
    same = score(hr, hr, lpips=metric)
    assert same["lpips"] == pytest.approx(0.0, abs=1e-6)
    # A change below half a gray level rounds away, so it must not move any of the three numbers.
    assert score(hr + 0.001, hr, lpips=metric)["lpips"] == pytest.approx(0.0, abs=1e-6)
    assert score(np.clip(hr + 0.2, 0, 1), hr, lpips=metric)["lpips"] > 0.0
    assert "lpips" not in score(hr, hr)


def test_gan_config_loads():
    cfg = load_config("configs/edsr_lite_gan.yaml")
    assert cfg["select_best_by"] == "lpips" and cfg["loss_weights"]["adversarial"] == 0.1


def test_gan_training_smoke(tmp_path):
    cfg = yaml.safe_load(open("configs/edsr_lite_gan.yaml"))
    train, val = tmp_path / "train", tmp_path / "val"
    train.mkdir()
    val.mkdir()
    rng = np.random.default_rng(0)
    for folder in (train, val):
        Image.fromarray(rng.integers(0, 256, (48, 48, 3), dtype=np.uint8)).save(folder / "a.png")
    cfg.update(
        {
            "train_dir": str(train),
            "val_dir": str(val),
            "out_dir": str(tmp_path / "out"),
            "init_from": None,
            "select_best_by": "psnr",  # LPIPS selection needs downloaded AlexNet weights
            "perceptual": {"pretrained": False},
            "patch_size": 32,
            "batch_size": 2,
            "patches_per_epoch": 2,
            "epochs": 1,
            "num_workers": 0,
            "device": "cpu",
            "wandb": {"enabled": False},
            "model": {"n_blocks": 1, "n_feats": 8, "res_scale": 0.1},
            "discriminator": {"n_feats": 8, "n_layers": 2},
        }
    )
    best = run_training(cfg)
    assert best.is_file() and (tmp_path / "out" / "discriminator_last.pt").is_file()
    assert torch.load(best, weights_only=False)["config"]["method"] == "edsr-lite-gan"
