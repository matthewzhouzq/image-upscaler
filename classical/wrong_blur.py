"""Wrong-blur experiment. This does not use the shared bicubic test inputs.

The official table always downscales with `make_lr_hr_pair`. Here the low-resolution image is a
Gaussian of one sigma, and TV is solved with either that sigma or a different one. The PSNR
drop between the two rows is the cost of assuming the wrong blur. Rows are named
`tv-matched-blur` and `tv-wrong-blur` so they cannot be read as the bicubic-degraded scores.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import yaml
from PIL import Image

from classical.tv import downsample, gaussian_kernel, solve
from data.degrade import SCALE, modcrop, to_float
from eval import upsert_rows
from metrics import score


def load_config(path: Path) -> dict:
    with Path(path).open() as handle:
        cfg = yaml.safe_load(handle)
    if not isinstance(cfg, dict):
        raise ValueError(f"{path} did not contain a mapping")
    return cfg


def _solve(lr: np.ndarray, sigma: float, cfg: dict) -> np.ndarray:
    estimate = solve(
        lr,
        blur_sigma=sigma,
        lam=float(cfg["lambda"]),
        iterations=int(cfg["iterations"]),
        tau=float(cfg["tau"]),
        sigma_dual=float(cfg["sigma_dual"]),
        scale=SCALE,
    )
    return np.clip(estimate, 0.0, 1.0).astype(np.float32)


def evaluate_directory(folder: Path, cfg: dict) -> list[dict[str, object]]:
    paths = sorted(folder.glob("*.png"))
    if not paths:
        raise FileNotFoundError(f"no .png images in {folder}")
    true_sigma = float(cfg["sigma_true"])
    wrong_sigma = float(cfg["sigma_assumed"])
    kernel = gaussian_kernel(true_sigma)
    matched_psnr, matched_ssim = [], []
    wrong_psnr, wrong_ssim = [], []
    for path in paths:
        hr = to_float(modcrop(Image.open(path).convert("RGB"), SCALE))
        lr = downsample(hr, kernel, SCALE)
        matched = score(_solve(lr, true_sigma, cfg), hr)
        wrong = score(_solve(lr, wrong_sigma, cfg), hr)
        matched_psnr.append(matched["psnr"])
        matched_ssim.append(matched["ssim"])
        wrong_psnr.append(wrong["psnr"])
        wrong_ssim.append(wrong["ssim"])
    base = {
        "train_data": f"gaussian-sigma-{true_sigma:g}",
        "params": 0,
        "test_set": folder.name,
        "n_images": len(paths),
        "lpips": "",
        "ms_per_image": "",
    }
    return [
        {
            **base,
            "method": "tv-matched-blur",
            "psnr": round(float(np.mean(matched_psnr)), 4),
            "ssim": round(float(np.mean(matched_ssim)), 4),
        },
        {
            **base,
            "method": "tv-wrong-blur",
            "train_data": f"true-{true_sigma:g}-assumed-{wrong_sigma:g}",
            "psnr": round(float(np.mean(wrong_psnr)), 4),
            "ssim": round(float(np.mean(wrong_ssim)), 4),
        },
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=Path("configs/wrong_blur.yaml"))
    parser.add_argument("--datasets", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    cfg = load_config(args.config)
    datasets = Path(args.datasets) if args.datasets is not None else Path(cfg["datasets"])
    out = Path(args.out) if args.out is not None else Path(cfg["out"])
    rows: list[dict[str, object]] = []
    for name in cfg["sets"]:
        pair = evaluate_directory(datasets / name, cfg)
        rows.extend(pair)
        drop = pair[0]["psnr"] - pair[1]["psnr"]
        print(
            f"{name:9s}  matched {pair[0]['psnr']:.2f} dB   "
            f"wrong {pair[1]['psnr']:.2f} dB   drop {drop:.2f} dB"
        )
    upsert_rows(rows, out)
    print(f"wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()
