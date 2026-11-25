import numpy as np
import torch
import yaml
from PIL import Image

from models.srcnn import srcnn_from_config
from train import build_optimizer, load_config, run_training, train_one_epoch


def _tiny_cfg(tmp_path):
    cfg = yaml.safe_load(open("configs/srcnn.yaml"))
    train = tmp_path / "train"
    val = tmp_path / "val"
    train.mkdir()
    val.mkdir()
    Image.new("RGB", (64, 64), (10, 20, 30)).save(train / "a.png")
    gradient = np.linspace(0, 255, 64, dtype=np.uint8)
    pixels = np.ascontiguousarray(np.broadcast_to(gradient.reshape(1, 64, 1), (64, 64, 3)))
    Image.fromarray(pixels).save(train / "b.png")
    Image.fromarray(pixels).save(val / "v.png")
    cfg.update(
        {
            "train_dir": str(train),
            "val_dir": str(val),
            "out_dir": str(tmp_path / "out"),
            "epochs": 1,
            "batch_size": 2,
            "patches_per_epoch": 4,
            "num_workers": 0,
            "device": "cpu",
            "wandb": {"enabled": False},
        }
    )
    return cfg


def test_config_has_two_learning_rates():
    cfg = load_config("configs/srcnn.yaml")
    optimizer = build_optimizer(srcnn_from_config(cfg), cfg)
    assert [group["lr"] for group in optimizer.param_groups] == [1.0e-5, 1.0e-4]


def test_loss_drops_on_a_repeated_patch():
    cfg = load_config("configs/srcnn.yaml")
    net = srcnn_from_config(cfg)
    # A high rate on purpose: this checks the graph, not the paper's schedule.
    optimizer = torch.optim.SGD(net.parameters(), lr=0.5)
    image = torch.rand(1, 3, 33, 33)
    batch = [(image, image)] * 8
    first = train_one_epoch(net, batch, optimizer, torch.device("cpu"))
    last = train_one_epoch(net, batch, optimizer, torch.device("cpu"))
    assert last < first * 0.5


def test_run_training_writes_a_checkpoint(tmp_path):
    best = run_training(_tiny_cfg(tmp_path))
    assert best.is_file()
    assert (tmp_path / "out" / "last.pt").is_file()
