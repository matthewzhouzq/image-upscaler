import numpy as np
import pytest
from PIL import Image

from classical.methods import build_classical_method
from classical.tv import divergence, downsample, energy, gaussian_kernel, gradient, solve, upsample_adjoint
from classical.wrong_blur import evaluate_directory
from data.degrade import to_float
from eval import build_method, evaluate_set


def test_gradient_and_divergence_are_adjoints():
    rng = np.random.default_rng(0)
    image = rng.normal(size=(9, 7, 2))
    px, py = rng.normal(size=(9, 7, 2)), rng.normal(size=(9, 7, 2))
    gx, gy = gradient(image)
    left = np.sum(gx * px + gy * py)
    right = -np.sum(image * divergence(px, py))
    assert left == pytest.approx(right)


def test_downsample_adjoint():
    rng = np.random.default_rng(1)
    kernel = gaussian_kernel(1.2)
    image = rng.normal(size=(16, 20, 3))
    low = rng.normal(size=(4, 5, 3))
    left = np.sum(downsample(image, kernel) * low)
    right = np.sum(image * upsample_adjoint(low, kernel))
    assert left == pytest.approx(right, rel=1e-8, abs=1e-8)


def test_energy_falls():
    rng = np.random.default_rng(2)
    hr = rng.random((24, 24, 3))
    kernel = gaussian_kernel(1.5)
    lr = downsample(hr, kernel)
    initial = energy(np.repeat(np.repeat(lr, 4, axis=0), 4, axis=1), lr, kernel, lam=0.002)
    solved = solve(lr, blur_sigma=1.5, lam=0.002, iterations=15, tau=0.2, sigma_dual=0.4)
    assert energy(solved, lr, kernel, lam=0.002) < initial


def test_wrong_sigma_loses_psnr(tmp_path):
    folder = tmp_path / "Stripes"
    folder.mkdir()
    x = np.linspace(0, 1, 64)
    stripe = 0.5 + 0.5 * np.sin(2 * np.pi * x * 6)
    image = np.stack([np.broadcast_to(stripe, (64, 64))] * 3, axis=-1)
    Image.fromarray((image * 255).astype(np.uint8)).save(folder / "a.png")
    cfg = {
        "sigma_true": 2.0,
        "sigma_assumed": 0.6,
        "iterations": 40,
        "lambda": 0.001,
        "tau": 0.2,
        "sigma_dual": 0.4,
    }
    matched, wrong = evaluate_directory(folder, cfg)
    assert matched["method"] == "tv-matched-blur"
    assert wrong["method"] == "tv-wrong-blur"
    assert matched["psnr"] > wrong["psnr"] + 0.3


def test_classical_methods_score_a_toy_set(tmp_path):
    folder = tmp_path / "Toy"
    folder.mkdir()
    Image.fromarray(np.full((32, 32, 3), 80, np.uint8)).save(folder / "a.png")
    for name in ("bicubic-keys", "lanczos", "ibp", "tv"):
        row = evaluate_set(build_method(name), folder)
        assert row["method"] == name and row["params"] == 0 and row["train_data"] == "none"
        assert row["psnr"] > 20
        assert build_classical_method(name).name == name


def test_rejects_unstable_step_sizes():
    lr = np.zeros((4, 4, 1))
    with pytest.raises(ValueError):
        solve(lr, blur_sigma=1.0, lam=0.01, iterations=1, tau=1.0, sigma_dual=1.0)
