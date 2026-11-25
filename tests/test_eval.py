import csv

import numpy as np
import pytest
from PIL import Image

from eval import METHODS, Method, evaluate_set, upsert_rows


def _make_set(tmp_path, n=2, size=(64, 48)):
    d = tmp_path / "Toy"
    d.mkdir()
    # Smooth gradient: bicubic should do well on it, but not perfectly.
    x = np.linspace(0, 255, size[0])[None, :, None] * np.ones((size[1], 1, 3))
    for i in range(n):
        Image.fromarray(((x + 10 * i) % 256).astype(np.uint8)).save(d / f"img_{i:03d}.png")
    return d


def test_bicubic_row_has_contract_fields(tmp_path):
    row = evaluate_set(METHODS["bicubic"], _make_set(tmp_path))
    assert row["method"] == "bicubic" and row["test_set"] == "Toy" and row["n_images"] == 2
    assert 20 < row["psnr"] < 99 and 0 < row["ssim"] <= 1
    assert row["lpips"] == "" and row["ms_per_image"] == ""  # not measured by eval.py


def test_perfect_method_scores_inf(tmp_path):
    # An "oracle" that returns HR exactly must hit infinite PSNR: proves eval compares SR to the right HR.
    d = _make_set(tmp_path, n=1)
    hr = Image.open(next(d.glob("*.png"))).convert("RGB")
    row = evaluate_set(Method("oracle", lambda lr: hr), d)
    assert row["psnr"] == float("inf") and row["ssim"] == pytest.approx(1.0)


def test_empty_set_raises(tmp_path):
    (tmp_path / "Empty").mkdir()
    with pytest.raises(FileNotFoundError):
        evaluate_set(METHODS["bicubic"], tmp_path / "Empty")


def test_upsert_replaces_instead_of_duplicating(tmp_path):
    out = tmp_path / "results.csv"
    row = {"method": "bicubic", "train_data": "none", "params": 0, "test_set": "Set5",
           "n_images": 5, "psnr": 1.0, "ssim": 0.5, "lpips": "", "ms_per_image": ""}
    upsert_rows([row], out)
    upsert_rows([{**row, "psnr": 2.0}], out)
    upsert_rows([{**row, "test_set": "Set14"}], out)
    rows = list(csv.DictReader(out.open()))
    assert [(r["test_set"], r["psnr"]) for r in rows] == [("Set5", "2.0"), ("Set14", "1.0")]
