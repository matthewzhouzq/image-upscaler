import numpy as np
import pytest
import torch
import yaml
from PIL import Image

from data.dataset import pil_to_tensor
from data.degrade import bicubic_downscale
from eval import build_method, evaluate_set
from models.srcnn import SRCNN, load_upscaler, save_checkpoint, srcnn_from_config, upscale_image


def test_forward_keeps_spatial_size():
    net = SRCNN()
    x = torch.rand(2, 1, 33, 40)
    assert net(x).shape == x.shape


def test_yaml_is_the_paper_network():
    # 9×9×64 + 5×5×32 + 5×5×1, with biases: 57281. A silent kernel change would move this.
    cfg = yaml.safe_load(open("configs/srcnn.yaml"))
    net = srcnn_from_config(cfg)
    assert sum(p.numel() for p in net.parameters()) == 57281
    early, last = net.parameter_groups()
    assert {id(p) for p in last} == {id(p) for p in net.conv3.parameters()}
    assert len(early) == 4 and len(last) == 2


def test_identity_y_rebuilds_bicubic_rgb():
    # If the network returns Y unchanged, pasting Cb/Cr must reconstruct the bicubic RGB.
    hr = Image.new("RGB", (32, 32), (180, 40, 90))
    lr = bicubic_downscale(hr)
    net = SRCNN()
    net.forward = lambda y: y
    sr = upscale_image(net, lr)
    assert sr.shape == (32, 32, 3)
    assert sr == pytest.approx(np.asarray(pil_to_tensor(hr).permute(1, 2, 0)), abs=1e-5)


def test_missing_checkpoint(tmp_path):
    with pytest.raises(FileNotFoundError):
        build_method("srcnn", tmp_path / "missing.pt")


def test_checkpoint_roundtrip_on_a_toy_set(tmp_path):
    cfg = yaml.safe_load(open("configs/srcnn.yaml"))
    net = srcnn_from_config(cfg)
    path = tmp_path / "best.pt"
    save_checkpoint(path, net, cfg, epoch=0, val_psnr=0.0)
    _upscale, train_data, params = load_upscaler(path, device=torch.device("cpu"))
    assert train_data == "DIV2K" and params == 57281

    folder = tmp_path / "Toy"
    folder.mkdir()
    Image.new("RGB", (48, 32), (20, 80, 140)).save(folder / "a.png")
    row = evaluate_set(build_method("srcnn", path), folder)
    assert row["method"] == "srcnn" and row["params"] == 57281
    assert row["n_images"] == 1 and np.isfinite(row["psnr"])
    assert row["lpips"] == "" and row["ms_per_image"] == ""
