import numpy as np
import pytest
import torch
import yaml
from PIL import Image

from eval import build_method, evaluate_set
from models.edsr_lite import EDSRLite, ResidualBlock, edsr_from_config
from models.srcnn import save_checkpoint
from train import build_model, run_training, train_one_epoch


def test_forward_upsamples_by_four():
    net = EDSRLite(n_blocks=1, n_feats=4, res_scale=0.1)
    low = torch.rand(2, 3, 7, 9)
    assert net(low).shape == (2, 3, 28, 36)


def test_zero_residual_block_is_identity():
    block = ResidualBlock(4, res_scale=0.1)
    torch.nn.init.zeros_(block.conv1.weight)
    torch.nn.init.zeros_(block.conv1.bias)
    torch.nn.init.zeros_(block.conv2.weight)
    torch.nn.init.zeros_(block.conv2.bias)
    sample = torch.randn(1, 4, 6, 6)
    assert torch.allclose(block(sample), sample)


def test_yaml_depth_and_width():
    main = edsr_from_config(yaml.safe_load(open("configs/edsr_lite.yaml")))
    shallow = edsr_from_config(yaml.safe_load(open("configs/edsr_lite_shallow.yaml")))
    narrow = edsr_from_config(yaml.safe_load(open("configs/edsr_lite_narrow.yaml")))
    assert sum(p.numel() for p in main.parameters()) == 926_723
    assert sum(p.numel() for p in shallow.parameters()) < sum(p.numel() for p in main.parameters())
    assert sum(p.numel() for p in narrow.parameters()) < sum(p.numel() for p in shallow.parameters())


def test_l1_loss_drops():
    net = EDSRLite(n_blocks=1, n_feats=4, res_scale=0.1, rgb_mean=(0.0, 0.0, 0.0))
    optimizer = torch.optim.Adam(net.parameters(), lr=1e-2)
    low = torch.rand(1, 3, 8, 8)
    high = low.repeat_interleave(4, dim=2).repeat_interleave(4, dim=3)
    batch = [(low, high)] * 6
    first = train_one_epoch(net, batch, optimizer, torch.device("cpu"), loss_name="l1", target="rgb")
    last = train_one_epoch(net, batch, optimizer, torch.device("cpu"), loss_name="l1", target="rgb")
    assert last < first


def test_checkpoint_names_the_ablation(tmp_path):
    cfg = yaml.safe_load(open("configs/edsr_lite_l2.yaml"))
    cfg["model"]["n_blocks"] = 1
    cfg["model"]["n_feats"] = 4
    net, samples, target = build_model(cfg)
    assert samples == "lr" and target == "rgb" and cfg["loss"] == "mse"
    path = tmp_path / "best.pt"
    save_checkpoint(path, net, cfg, epoch=0, val_psnr=0.0)
    folder = tmp_path / "Toy"
    folder.mkdir()
    Image.fromarray(np.full((32, 32, 3), 90, np.uint8)).save(folder / "a.png")
    row = evaluate_set(build_method("edsr_lite", path), folder)
    assert row["method"] == "edsr-lite-l2" and row["train_data"] == "DIV2K"
    assert row["psnr"] > 20


def test_run_training_writes_a_checkpoint(tmp_path):
    cfg = yaml.safe_load(open("configs/edsr_lite_shallow.yaml"))
    train = tmp_path / "train"
    val = tmp_path / "val"
    train.mkdir()
    val.mkdir()
    pixels = np.zeros((64, 64, 3), np.uint8)
    pixels[:, 32:] = 255
    Image.fromarray(pixels).save(train / "a.png")
    Image.fromarray(pixels).save(val / "v.png")
    cfg["model"]["n_blocks"] = 1
    cfg["model"]["n_feats"] = 4
    cfg.update(
        {
            "train_dir": str(train),
            "val_dir": str(val),
            "out_dir": str(tmp_path / "out"),
            "epochs": 1,
            "batch_size": 2,
            "patches_per_epoch": 2,
            "num_workers": 0,
            "device": "cpu",
            "wandb": {"enabled": False},
        }
    )
    best = run_training(cfg)
    assert best.is_file()


def test_missing_checkpoint(tmp_path):
    with pytest.raises(FileNotFoundError):
        build_method("edsr_lite", tmp_path / "missing.pt")
