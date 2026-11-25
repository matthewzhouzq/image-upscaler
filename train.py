"""Config-driven training. Hyperparameters live in the YAML, not in this file.

Usage (from the repo root):
    python train.py --config configs/srcnn.yaml
    python train.py --config configs/edsr_lite.yaml
    python train.py --config configs/edsr_lite_gan.yaml
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
from data.realworld import DegradationConfig, RealWorldPatchDataset
from data.degrade import SCALE, make_lr_hr_pair, to_float
from metrics import LPIPSMetric, score
from models.discriminator import discriminator_from_config
from models.edsr_lite import edsr_from_config
from models.edsr_lite import upscale_image as edsr_upscale
from models.losses import VGGPerceptualLoss, discriminator_loss, generator_adversarial_loss
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
GAN_KEYS = ("lr", "lr_d", "loss_weights", "discriminator", "degradation", "perceptual", "select_best_by")


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
    elif architecture == "edsr_lite_gan":
        missing += [key for key in GAN_KEYS if key not in cfg]
    else:
        raise ValueError(f"architecture must be srcnn, edsr_lite or edsr_lite_gan, got {architecture!r}")
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
    if architecture == "edsr_lite_gan":
        if cfg["loss"] != "gan" or cfg["optimizer"] != "adam":
            raise ValueError("edsr_lite_gan uses loss: gan (weights in loss_weights) and adam")
        return edsr_from_config(cfg), "realworld", "rgb"
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
    if cfg["architecture"] == "edsr_lite_gan":
        return run_gan_training(cfg)
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


def train_gan_epoch(
    generator: nn.Module,
    discriminator: nn.Module,
    perceptual: nn.Module,
    loader: DataLoader,
    opt_g: torch.optim.Optimizer,
    opt_d: torch.optim.Optimizer,
    device: torch.device,
    weights: dict,
) -> dict[str, float]:
    """One epoch of alternating updates: D first, then G. Returns mean losses.

    D sees `sr.detach()` so its step does not push gradients into G. During the G step D is
    frozen, so G's adversarial loss changes only G. Forgetting either is a common silent bug.
    """
    generator.train()
    discriminator.train()
    w_pix, w_perc, w_adv = (float(weights[k]) for k in ("pixel", "perceptual", "adversarial"))
    totals = {"d": 0.0, "g": 0.0, "pixel": 0.0, "perceptual": 0.0, "adversarial": 0.0}
    seen = 0
    for low, hr in loader:
        low, hr = low.to(device), hr.to(device)
        sr = generator(low)

        for p in discriminator.parameters():
            p.requires_grad_(True)
        d_loss = discriminator_loss(discriminator(hr), discriminator(sr.detach()))
        opt_d.zero_grad(set_to_none=True)
        d_loss.backward()
        opt_d.step()

        for p in discriminator.parameters():
            p.requires_grad_(False)
        pixel = F.l1_loss(sr, hr)
        perc = perceptual(sr, hr)
        adv = generator_adversarial_loss(discriminator(sr))
        g_loss = w_pix * pixel + w_perc * perc + w_adv * adv
        opt_g.zero_grad(set_to_none=True)
        g_loss.backward()
        opt_g.step()

        batch = low.shape[0]
        for key, value in (("d", d_loss), ("g", g_loss), ("pixel", pixel), ("perceptual", perc), ("adversarial", adv)):
            totals[key] += float(value.detach()) * batch
        seen += batch
    if seen == 0:
        raise RuntimeError("training loader produced no batches")
    return {key: value / seen for key, value in totals.items()}


@torch.no_grad()
def validate_gan(model: nn.Module, hr_dir: Path, lpips: LPIPSMetric | None) -> dict[str, float]:
    """Mean PSNR (and LPIPS, if given) on HR images, with LR from `make_lr_hr_pair` as in eval.py."""
    model.eval()
    paths = sorted(Path(hr_dir).glob("*.png"))
    if not paths:
        raise FileNotFoundError(f"no .png images in {hr_dir}")
    scores = [score(edsr_upscale(model, lr), to_float(hr), lpips=lpips) for lr, hr in map(make_lr_hr_pair, map(str, paths))]
    out = {"psnr": float(np.mean([s["psnr"] for s in scores]))}
    if lpips is not None:
        out["lpips"] = float(np.mean([s["lpips"] for s in scores]))
    return out


def run_gan_training(cfg: dict) -> Path:
    """Fine-tune EDSR-lite as a GAN generator on real-world degraded patches.

    Starts from `init_from` (a PSNR-trained checkpoint) when given: a GAN started from random
    weights spends its first epochs learning colors the pixel loss would have taught for free.
    The best checkpoint is picked by `select_best_by`. Picking by PSNR would favor the
    blurriest epoch, which defeats the point of the GAN, so the config uses LPIPS.
    """
    set_seed(int(cfg["seed"]))
    device = pick_device(str(cfg["device"]))
    generator, _, _ = build_model(cfg)
    init_from = cfg.get("init_from")
    if init_from:
        path = Path(init_from)
        if not path.is_file():
            raise FileNotFoundError(f"init_from checkpoint {path} not found; train configs/edsr_lite.yaml first")
        generator.load_state_dict(torch.load(path, map_location="cpu", weights_only=False)["model"])
    generator = generator.to(device)
    discriminator = discriminator_from_config(cfg).to(device)
    perceptual = VGGPerceptualLoss(pretrained=bool(cfg["perceptual"].get("pretrained", True))).to(device)

    betas = tuple(float(value) for value in cfg.get("betas", (0.9, 0.99)))
    opt_g = torch.optim.Adam(generator.parameters(), lr=float(cfg["lr"]), betas=betas)
    opt_d = torch.optim.Adam(discriminator.parameters(), lr=float(cfg["lr_d"]), betas=betas)

    select = str(cfg["select_best_by"])
    if select not in ("lpips", "psnr"):
        raise ValueError(f"select_best_by must be lpips or psnr, got {select!r}")
    lpips = LPIPSMetric(device=str(device)) if select == "lpips" else None

    dataset = RealWorldPatchDataset(
        cfg["train_dir"],
        patch_size=int(cfg["patch_size"]),
        patches_per_epoch=int(cfg["patches_per_epoch"]),
        degradation=DegradationConfig.from_dict(cfg["degradation"]),
        scale=int(cfg["scale"]),
        augment=True,
        seed=int(cfg["seed"]),
    )
    loader = DataLoader(
        dataset,
        batch_size=int(cfg["batch_size"]),
        shuffle=False,
        num_workers=int(cfg["num_workers"]),
        worker_init_fn=_seed_worker if int(cfg["num_workers"]) else None,
    )
    out_dir = Path(cfg["out_dir"])
    best_path, last_path = out_dir / "best.pt", out_dir / "last.pt"
    best = float("inf") if select == "lpips" else float("-inf")
    params = sum(p.numel() for p in generator.parameters())
    print(f"device {device}  generator params {params}  train {cfg['train_dir']}  init {init_from or 'random'}")
    run = _wandb_run(cfg)
    try:
        for epoch in range(int(cfg["epochs"])):
            dataset.set_epoch(epoch)
            losses = train_gan_epoch(
                generator, discriminator, perceptual, loader, opt_g, opt_d, device, cfg["loss_weights"]
            )
            val = validate_gan(generator, Path(cfg["val_dir"]), lpips)
            save_checkpoint(last_path, generator, cfg, epoch, val["psnr"])
            torch.save(discriminator.state_dict(), out_dir / "discriminator_last.pt")
            current = val[select]
            if (current < best) if select == "lpips" else (current > best):
                best = current
                save_checkpoint(best_path, generator, cfg, epoch, val["psnr"])
            shown = f"  val LPIPS {val['lpips']:.4f}" if "lpips" in val else ""
            print(f"epoch {epoch:3d}  G {losses['g']:.4f}  D {losses['d']:.4f}  val PSNR {val['psnr']:.2f} dB{shown}")
            if run is not None:
                run.log({**{f"train/{k}": v for k, v in losses.items()}, **{f"val/{k}": v for k, v in val.items()}, "epoch": epoch})
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
