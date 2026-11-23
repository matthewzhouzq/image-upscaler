"""THE scoring script (see CLAUDE.md, Evaluation contract). Every method's results come from here.

Usage:
    python eval.py --method bicubic                 # all four test sets
    python eval.py --method bicubic --sets Set5     # just one

Writes one row per (method, test set) to results/results.csv; re-running a method replaces its rows.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image

from data.degrade import SCALE, make_lr_hr_pair, to_float
from metrics import score

TEST_SETS = ("Set5", "Set14", "BSD100", "Urban100")
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


def evaluate_set(method: Method, set_dir: Path) -> dict[str, object]:
    """Score `method` on every HR image in `set_dir`; returns one results row."""
    paths = sorted(set_dir.glob("*.png"))
    if not paths:
        raise FileNotFoundError(f"no .png images in {set_dir}")
    psnrs, ssims = [], []
    for p in paths:
        lr, hr = make_lr_hr_pair(str(p))  # the one shared downscale; never build LR any other way
        sr = method.upscale(lr)
        if isinstance(sr, Image.Image):
            sr = to_float(sr)
        s = score(sr, to_float(hr))  # clamps, rounds, Y channel, 4 px border, as the contract says
        psnrs.append(s["psnr"])
        ssims.append(s["ssim"])
    return {
        "method": method.name,
        "train_data": method.train_data,
        "params": method.params,
        "test_set": set_dir.name,
        "n_images": len(paths),
        # Mean of per-image scores: the convention papers report.
        "psnr": round(float(np.mean(psnrs)), 4),
        "ssim": round(float(np.mean(ssims)), 4),
        "lpips": "",  # from Phase 3
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
    parser.add_argument("--method", required=True, choices=sorted(METHODS))
    parser.add_argument("--sets", nargs="+", default=list(TEST_SETS), choices=TEST_SETS)
    parser.add_argument("--datasets", type=Path, default=Path("datasets"))
    parser.add_argument("--out", type=Path, default=RESULTS_CSV)
    args = parser.parse_args()

    method = METHODS[args.method]
    rows = []
    for name in args.sets:
        row = evaluate_set(method, args.datasets / name)
        rows.append(row)
        print(f"{method.name:10s} {name:9s} n={row['n_images']:3d}  PSNR {row['psnr']:.2f} dB  SSIM {row['ssim']:.4f}")
    upsert_rows(rows, args.out)
    print(f"wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
