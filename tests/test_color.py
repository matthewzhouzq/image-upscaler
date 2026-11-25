import numpy as np
import pytest
import torch

from data.color import rgb_tensor_to_y, rgb_to_ycbcr, ycbcr_to_rgb
from metrics import rgb_to_y

rng = np.random.default_rng(0)


def test_endpoints_match_matlab_range():
    black = rgb_to_ycbcr(np.zeros((1, 1, 3)))
    white = rgb_to_ycbcr(np.ones((1, 1, 3)))
    assert black[0, 0].tolist() == pytest.approx([16.0, 128.0, 128.0])
    assert white[0, 0].tolist() == pytest.approx([235.0, 128.0, 128.0])


def test_y_matches_metrics():
    # The scored Y and the trained Y are the same channel. A different matrix would not error.
    rgb = rng.integers(0, 256, (16, 16, 3), dtype=np.uint8)
    ours = rgb_to_ycbcr(rgb.astype(np.float64) / 255.0)[..., 0]
    assert ours == pytest.approx(rgb_to_y(rgb))


def test_roundtrip():
    rgb = rng.random((20, 18, 3))
    assert ycbcr_to_rgb(rgb_to_ycbcr(rgb)) == pytest.approx(rgb, abs=1e-8)


def test_tensor_y_matches_numpy():
    rgb = rng.random((2, 3, 12, 10)).astype(np.float32)
    got = rgb_tensor_to_y(torch.from_numpy(rgb)).numpy()[:, 0]
    for index in range(2):
        expected = rgb_to_ycbcr(rgb[index].transpose(1, 2, 0))[..., 0] / 255.0
        assert got[index] == pytest.approx(expected, abs=1e-5)
