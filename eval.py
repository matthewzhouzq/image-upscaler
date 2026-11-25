"""THE scoring script (see CLAUDE.md, Evaluation contract). Every method's results come from here.

Usage:
    python eval.py --method bicubic                 # all four test sets
    python eval.py --method bicubic --sets Set5     # just one
    python eval.py --method srcnn --checkpoint outputs/srcnn/best.pt
    python eval.py --method edsr_lite --checkpoint outputs/edsr_lite/best.pt
    python eval.py --method edsr_lite_gan           # reads outputs/edsr_lite_gan/best.pt
    python eval.py --method lanczos                 # also: bicubic-keys, ibp, tv

Writes one row per (method, test set) to results/results.csv; re-running a method replaces its rows.
LPIPS is computed by default (AlexNet weights download on first use); --no-lpips is a print-only
quick look that writes nothing.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image

from classical.methods import CLASSICAL_NAMES, build_classical_method
from data.degrade import SCALE, make_lr_hr_pair, to_float
from metrics import LPIPSMetric, score
from models.edsr_lite import load_upscaler as load_edsr
from models.srcnn import load_upscaler

TEST_SETS = ("Set5", "Set14", "BSD100", "Urban100")
METHOD_NAMES = ("bicubic", "srcnn", "edsr_lite", "edsr_lite_gan", *CLASSICAL_NAMES)
DEFAULT_CHECKPOINTS = {
    "srcnn": Path("outputs/srcnn/best.pt"),
    "edsr_lite": Path("outputs/edsr_lite/best.pt"),
    "edsr_lite_gan": Path("outputs/edsr_lite_gan/best.pt"),
}
TRAIN_CONFIGS = {
    "srcnn": "configs/srcnn.yaml",
    "edsr_lite": "configs/edsr_lite.yaml",
    "edsr_lite_gan": "configs/edsr_lite_gan.yaml",
}
RESULTS_CSV = Path("results/results.csv")
FIELDS = ["method", "train_data", "params", "test_set", "n_images", "psnr", "ssim", "lpips", "ms_per_image"]


@dataclass(frozen=True)
class Method:
    """Anything that upscales: LR PIL image in, SR image out (PIL, or float HxWx3 array in [0, 1]).

    `train_data` and `params` go into the results row so learned and classical methods share one table.
    """

    name: str
    upscale: Callable[[Image.Image], Image.Image | np.ndarray]
    train_data: str = "none"
    params: int = 0


def _bicubic(lr: Image.Image) -> Image.Image:
    w, h = lr.size
    return lr.resize((w * SCALE, h * SCALE), resample=Image.Resampling.BICUBIC)


METHODS: dict[str, Method] = {
    "bicubic": Method("bicubic", _bicubic),
}


def build_method(name: str, checkpoint: Path | None = None) -> Method:
    """Bicubic needs no weights. Learned methods read a checkpoint so the row records that net."""
    if name == "bicubic":
        return METHODS["bicubic"]
    if name in CLASSICAL_NAMES:
        return build_classical_method(name)
    if name not in DEFAULT_CHECKPOINTS:
        raise KeyError(name)
    path = Path(checkpoint) if checkpoint is not None else DEFAULT_CHECKPOINTS[name]
    if not path.is_file():
        raise FileNotFoundError(
            f"no {name} checkpoint at {path}. Train one with: python train.py --config {TRAIN_CONFIGS[name]}"
        )
    if name == "srcnn":
        upscale, train_data, params = load_upscaler(path)
        return Method("srcnn", upscale, train_data=train_data, params=params)
    # The GAN generator is an EDSR-lite network, so the same loader rebuilds it from the saved config.
    upscale, train_data, params, method_name = load_edsr(path)
    return Method(method_name, upscale, train_data=train_data, params=params)


def evaluate_set(method: Method, set_dir: Path, lpips: LPIPSMetric | None = None) -> dict[str, object]:
    """Score `method` on every HR image in `set_dir`; returns one results row.

    Without `lpips` the column stays blank, rather than a number from a different setup.
    """
    paths = sorted(set_dir.glob("*.png"))
    if not paths:
        raise FileNotFoundError(f"no .png images in {set_dir}")
    psnrs, ssims, lpipses = [], [], []
    for p in paths:
        lr, hr = make_lr_hr_pair(str(p))  # the one shared downscale; never build LR any other way
        sr = method.upscale(lr)
        if isinstance(sr, Image.Image):
            sr = to_float(sr)
        s = score(sr, to_float(hr), lpips=lpips)  # clamps, rounds, Y channel, 4 px border, as the contract says
        psnrs.append(s["psnr"])
        ssims.append(s["ssim"])
        if lpips is not None:
            lpipses.append(s["lpips"])
    return {
        "method": method.name,
        "train_data": method.train_data,
        "params": method.params,
        "test_set": set_dir.name,
        "n_images": len(paths),
        # Mean of per-image scores: the convention papers report.
        "psnr": round(float(np.mean(psnrs)), 4),
        "ssim": round(float(np.mean(ssims)), 4),
        "lpips": round(float(np.mean(lpipses)), 4) if lpipses else "",  # RGB, AlexNet, lower is better
        "ms_per_image": "",  # only from the bench/ harness, never timed here
    }


def upsert_rows(rows: list[dict[str, object]], csv_path: Path) -> None:
    """Write `rows` to the results CSV, replacing any earlier rows for the same (method, test_set)."""
    keys = {(r["method"], r["test_set"]) for r in rows}
    existing: list[dict[str, object]] = []
    if csv_path.exists():
        with csv_path.open(newline="") as f:
            existing = [r for r in csv.DictReader(f) if (r["method"], r["test_set"]) not in keys]
    order = {name: i for i, name in enumerate(TEST_SETS)}
    merged = sorted(existing + rows, key=lambda r: (str(r["method"]), order.get(str(r["test_set"]), 99)))
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(merged)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--method", required=True, choices=METHOD_NAMES)
    parser.add_argument("--sets", nargs="+", default=list(TEST_SETS), choices=TEST_SETS)
    parser.add_argument("--datasets", type=Path, default=Path("datasets"))
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=RESULTS_CSV)
    parser.add_argument(
        "--no-lpips",
        action="store_true",
        help="quick look: skip LPIPS and print only. Nothing is written, so a saved LPIPS is never blanked",
    )
    args = parser.parse_args()

    method = build_method(args.method, args.checkpoint)
    lpips = None if args.no_lpips else LPIPSMetric()
    rows = []
    for name in args.sets:
        row = evaluate_set(method, args.datasets / name, lpips=lpips)
        rows.append(row)
        extra = f"  LPIPS {row['lpips']:.4f}" if row["lpips"] != "" else ""
        print(
            f"{method.name:<14s} {name:9s} n={row['n_images']:3d}  PSNR {row['psnr']:.2f} dB  SSIM {row['ssim']:.4f}{extra}"
        )
    if args.no_lpips:
        # upsert_rows replaces whole rows, so writing here would blank an LPIPS saved by a full run.
        # Keeping the old LPIPS instead could pair it with a PSNR from a different checkpoint.
        print(f"--no-lpips: printed only, {args.out} left unchanged")
        return
    upsert_rows(rows, args.out)
    print(f"wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
