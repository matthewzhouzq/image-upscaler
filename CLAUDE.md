# CLAUDE.md — upscaler

Context for Claude (and humans) working in this repo. Keep it current: when a convention changes or a phase finishes, update this file in the same PR.

## What this project is

A ×4 image super-resolution project built by two people, in two halves:

1. **Train it** – build SR models from scratch (SRCNN → EDSR-lite → real-world degradations + GAN), alongside a **pure-math track** (hand-written bicubic/Lanczos, iterative back-projection, TV-regularized reconstruction) so we can compare classical methods against learned ones.
2. **Ship it** – export the best model to ONNX/TensorRT (FP16/INT8), serve it behind a FastAPI service with tiling and dynamic batching, load-test it, and show live metrics on a dashboard.

The goal is a portfolio-quality repo: real numbers, honest comparisons, and a README a stranger can understand in 30 seconds.

## Team

- **Matthew** (matthewzhouzq) and **DawDa07**.
- Owners per workstream are tracked in the roadmap doc. Phase 1 (data pipeline, eval script, SRCNN) is built together; after that the math and ML tracks run in parallel.

## Phases

- [x] **1 – SRCNN baseline**: dataset class, bicubic baseline, SRCNN, training loop, `eval.py`
- [x] **1.5 – Pure-math track**: own bicubic/Lanczos, back-projection, TV optimization, wrong-blur experiment
- [x] **2 – EDSR-lite**: residual blocks, pixel shuffle, L1 loss, ablations
- [ ] **3 – Real-world + GAN**: second-order degradation pipeline, perceptual + adversarial loss, LPIPS
- [ ] **4 – Export + optimize**: ONNX, TensorRT FP16/INT8, speed-vs-quality table
- [ ] **5 – Tiled serving**: FastAPI, tiling with overlap blending, dynamic batching, Locust load tests
- [ ] **6 – Dashboard + write-up**: live metrics, before/after demo, README

Tick these off as phases finish.

## Planned layout

This is the target layout; update it when the real structure differs.

```
data/        # dataset classes, degradation pipeline (realworld.py: training-only second-order chain)
models/      # srcnn.py, edsr_lite.py, discriminator.py, losses.py
classical/   # bicubic/lanczos, back-projection, TV solver (math track)
configs/     # one YAML per experiment
train.py     # single config-driven training script
eval.py      # THE scoring script — see "Evaluation contract"
export/      # onnx_export.py, build_trt.py, calibrate.py
bench/       # latency harness + results CSVs
serve/       # FastAPI app, tiler, batcher, metrics
loadtest/    # locustfile.py
dashboard/
results/     # tables and sample crops used by the README
```

Commands, from the repo root. Don't assume a command works until it's listed.

```bash
python train.py --config configs/srcnn.yaml
python eval.py --method bicubic
python eval.py --method srcnn --checkpoint outputs/srcnn/best.pt
python train.py --config configs/edsr_lite.yaml
python eval.py --method edsr_lite --checkpoint outputs/edsr_lite/best.pt
python eval.py --method bicubic-keys
python eval.py --method lanczos
python eval.py --method ibp
python eval.py --method tv
python -m classical.wrong_blur --config configs/wrong_blur.yaml
python train.py --config configs/edsr_lite_gan.yaml          # needs outputs/edsr_lite/best.pt first
python eval.py --method edsr_lite_gan
python eval.py --method bicubic --no-lpips                   # any method; quick look, prints only, writes nothing
```

## Evaluation contract (do not change without both people agreeing)

Every method — math or ML — is scored by `eval.py` on the same data, so results are comparable.

- Scale is **×4** everywhere.
- LR inputs are made from HR images with **one shared bicubic downscale function** (in `data/`). Never use a different resize for test inputs.
- Before scoring, outputs are **clamped to [0, 1] and rounded to uint8**.
- **PSNR and SSIM on the Y channel** (YCbCr), with a **4-pixel border cropped**. This is the convention papers use.
- **LPIPS** on RGB, from Phase 3 on: AlexNet backbone (`lpips` package), on the same clamped, uint8-rounded images scaled to [−1, 1], with the **same 4-pixel border crop** as PSNR/SSIM, so all three numbers describe the same pixels. Papers differ on cropping for LPIPS; this is our choice. Mean of per-image values, like PSNR/SSIM.
- Test sets: **Set5, Set14, BSD100, Urban100**; DIV2K valid for validation during training.
- Every method returns a row in `results/` with: method, training data, parameter count, PSNR, SSIM, LPIPS, time per image (ms).
- Speed numbers come from the shared harness in `bench/` only: warm-up runs, `torch.cuda.synchronize()`, median of 100 runs, fixed 256×256 LR input.

## Conventions

- Python 3.11, PyTorch. Type hints on public functions; short docstrings that say *why*, not just *what*.
- Every experiment is a YAML config in `configs/`; no hard-coded hyperparameters in scripts.
- Set and log random seeds.
- Log runs to the shared Weights & Biases project so both of us see every result.
- **Never commit datasets, checkpoints or large images.** They go in the shared Drive folder or Hugging Face Hub. Keep `.gitignore` up to date.
- Small sample crops for the README are fine in `results/`.

## Git workflow

- `main` always runs. No direct pushes to `main`.
- One branch per feature (`feat/tv-solver`, `fix/eval-border-crop`), opened as a pull request and reviewed by the other person.
- Commit messages: short imperative summary line, details below if needed.

## How Claude should help here

We're building this to learn, so:

- **Explain before writing.** When a new concept comes up (pixel shuffle, TV regularization, INT8 calibration…), explain it briefly before or alongside the code.
- **Prefer guiding and reviewing over writing whole modules.** Small snippets, skeletons and fixes are fine; ask before generating a large file from scratch.
- **Point out bugs that silently ruin results**: off-by-one border crops, RGB vs BGR, [0,255] vs [0,1] ranges, evaluating on training data, missing `model.eval()` / `torch.no_grad()`, timing without `synchronize()`.
- **Respect the evaluation contract.** If a change would alter how results are measured, flag it instead of making it.
- When suggesting numbers (expected PSNR, latency), say they're approximate and where they come from.
