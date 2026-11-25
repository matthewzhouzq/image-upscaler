"""Config-driven training. Hyperparameters live in the YAML, not in this file.

Usage (from the repo root):
    python train.py --config configs/srcnn.yaml
    python train.py --config configs/edsr_lite.yaml
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
import yaml
from torch import nn
from torch.utils.data import DataLoader

from data.color import rgb_tensor_to_y
from data.dataset import SRPatchDataset
from data.degrade import SCALE, make_lr_hr_pair, to_float
from metrics import score
from models.edsr_lite import edsr_from_config
from models.edsr_lite import upscale_image as edsr_upscale
from models.srcnn import pick_device, save_checkpoint, srcnn_from_config
from models.srcnn import upscale_image as srcnn_upscale

COMMON = (
    "architecture",
    "seed",
    "scale",
    "patch_size",
    "batch_size",
    "patches_per_epoch",
    "epochs",
    "num_workers",
    "loss",
    "optimizer",
    "train_dir",
    "val_dir",
    "out_dir",
    "train_data",
    "device",
    "model",
)
SRCNN_KEYS = ("lr_early", "lr_last", "momentum")
EDSR_KEYS = ("lr",)


def load_config(path: Path) -> dict:
    with Path(path).open() as handle:
        cfg = yaml.safe_load(handle)
    if not isinstance(cfg, dict):
        raise ValueError(f"{path} did not contain a mapping")
    missing = [key for key in COMMON if key not in cfg]
    architecture = cfg.get("architecture")
    if architecture == "srcnn":
        missing += [key for key in SRCNN_KEYS if key not in cfg]
    elif architecture == "edsr_lite":
        missing += [key for key in EDSR_KEYS if key not in cfg]
    else:
        raise ValueError(f"architecture must be srcnn or edsr_lite, got {architecture!r}")
    if missing:
        raise ValueError(f"{path} is missing keys: {', '.join(missing)}")
    return cfg


def set_seed(seed: int) -> None:
    """Seed Python, NumPy, and PyTorch. Crop sampling has its own seed inside the dataset."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def build_model(cfg: dict) -> tuple[nn.Module, str, str]:
    """Return (model, dataset samples, loss target).

    SRCNN trains on the bicubic upsample and on Y only. EDSR-lite trains on the small LR and on RGB.
    Mixing those up trains the pixel-shuffle head on an image that is already ×4.
    """
    architecture = cfg["architecture"]
    if architecture == "srcnn":
        if cfg["loss"] != "mse" or cfg["optimizer"] != "sgd":
            raise ValueError("srcnn uses mse and sgd (Dong et al.)")
        return srcnn_from_config(cfg), "bicubic", "y"
    if cfg["loss"] not in ("l1", "mse"):
        raise ValueError(f"edsr_lite loss must be l1 or mse, got {cfg['loss']!r}")
    if cfg["optimizer"] != "adam":
        raise ValueError(f"edsr_lite optimizer must be adam, got {cfg['optimizer']!r}")
    return edsr_from_config(cfg), "lr", "rgb"


def build_optimizer(model: nn.Module, cfg: dict) -> torch.optim.Optimizer:
    if cfg["optimizer"] == "sgd":
        early, last = model.parameter_groups()
        return torch.optim.SGD(
            [
                {"params": early, "lr": float(cfg["lr_early"])},
                {"params": last, "lr": float(cfg["lr_last"])},
            ],
            momentum=float(cfg["momentum"]),
        )
    if cfg["optimizer"] == "adam":
        betas = tuple(float(value) for value in cfg.get("betas", (0.9, 0.999)))
        return torch.optim.Adam(model.parameters(), lr=float(cfg["lr"]), betas=betas)
    raise ValueError(f"optimizer must be sgd or adam, got {cfg['optimizer']!r}")


def _criterion(loss_name: str):
    if loss_name == "mse":
        return F.mse_loss
    if loss_name == "l1":
        return F.l1_loss
    raise ValueError(f"loss must be mse or l1, got {loss_name!r}")


def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    loss_name: str = "mse",
    target: str = "y",
) -> float:
    """Mean loss over the epoch. The border is included; eval crops 4 px later, in `metrics.score`.

    `target='y'` is SRCNN: the network sees luminance of the bicubic image. `target='rgb'` is
    EDSR-lite: the network sees the small LR and is scored against RGB. Both are still judged
    on Y by `eval.py`.
    """
    model.train()
    criterion = _criterion(loss_name)
    total = 0.0
    seen = 0
    for low, hr in loader:
        low = low.to(device)
        hr = hr.to(device)
        if target == "y":
            predicted = model(rgb_tensor_to_y(low))
            truth = rgb_tensor_to_y(hr)
        elif target == "rgb":
            predicted = model(low)
            truth = hr
        else:
            raise ValueError(f"target must be y or rgb, got {target!r}")
        loss = criterion(predicted, truth)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        batch = low.shape[0]
        total += float(loss.detach()) * batch
        seen += batch
    if seen == 0:
        raise RuntimeError("training loader produced no batches")
    return total / seen


@torch.no_grad()
def validate(model: nn.Module, hr_dir: Path, upscale) -> float:
    """Mean Y-channel PSNR on a folder of HR images, via the same `score` eval.py uses.

    LR is built with `make_lr_hr_pair`, not with the training dataset, so a second resize
    cannot leak into the number we watch while training.
    """
    model.eval()
    paths = sorted(Path(hr_dir).glob("*.png"))
    if not paths:
        raise FileNotFoundError(f"no .png images in {hr_dir}")
    psnrs: list[float] = []
    for path in paths:
        lr, hr = make_lr_hr_pair(str(path))
        sr = upscale(model, lr)
        psnrs.append(score(sr, to_float(hr))["psnr"])
    return float(np.mean(psnrs))


def _seed_worker(worker_id: int) -> None:
    worker_seed = torch.initial_seed() % 2**32
    random.seed(worker_seed)
    np.random.seed(worker_seed)


def _wandb_run(cfg: dict):
    wandb_cfg = cfg.get("wandb") or {}
    if not wandb_cfg.get("enabled", False):
        return None
    import wandb

    return wandb.init(project=wandb_cfg["project"], name=wandb_cfg.get("run_name"), config=cfg)


def run_training(cfg: dict) -> Path:
    """Train from a config dict. Returns the path of the best validation checkpoint."""
    if int(cfg["scale"]) != SCALE:
        raise ValueError(f"scale must be {SCALE}")
    set_seed(int(cfg["seed"]))
    device = pick_device(str(cfg["device"]))
    model, samples, target = build_model(cfg)
    model = model.to(device)
    upscale = srcnn_upscale if cfg["architecture"] == "srcnn" else edsr_upscale
    optimizer = build_optimizer(model, cfg)
    dataset = SRPatchDataset(
        cfg["train_dir"],
        patch_size=int(cfg["patch_size"]),
        patches_per_epoch=int(cfg["patches_per_epoch"]),
        scale=int(cfg["scale"]),
        augment=True,
        seed=int(cfg["seed"]),
        samples=samples,
    )
    loader = DataLoader(
        dataset,
        batch_size=int(cfg["batch_size"]),
        shuffle=False,
        num_workers=int(cfg["num_workers"]),
        worker_init_fn=_seed_worker if int(cfg["num_workers"]) else None,
    )
    out_dir = Path(cfg["out_dir"])
    best_path = out_dir / "best.pt"
    last_path = out_dir / "last.pt"
    best_psnr = float("-inf")
    params = sum(p.numel() for p in model.parameters())
    print(f"device {device}  params {params}  train {cfg['train_dir']}")
    run = _wandb_run(cfg)
    try:
        for epoch in range(int(cfg["epochs"])):
            dataset.set_epoch(epoch)
            loss = train_one_epoch(model, loader, optimizer, device, loss_name=str(cfg["loss"]), target=target)
            val_psnr = validate(model, Path(cfg["val_dir"]), upscale)
            model.train()
            save_checkpoint(last_path, model, cfg, epoch, val_psnr)
            if val_psnr > best_psnr:
                best_psnr = val_psnr
                save_checkpoint(best_path, model, cfg, epoch, val_psnr)
            print(f"epoch {epoch:3d}  loss {loss:.6f}  val PSNR {val_psnr:.2f} dB")
            if run is not None:
                run.log({"train/loss": loss, "val/psnr": val_psnr, "epoch": epoch})
    finally:
        if run is not None:
            run.finish()
    return best_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    cfg = load_config(args.config)
    best = run_training(cfg)
    print(f"best checkpoint {best}")


if __name__ == "__main__":
    main()
