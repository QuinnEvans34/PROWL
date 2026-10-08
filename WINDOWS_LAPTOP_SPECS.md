# Windows Laptop — Machine Specs (secondary training machine)

> **For the main machine / any AI session:** this is the second machine in the PROWL project, a Windows laptop with an
> **NVIDIA RTX 4060 (8 GB VRAM, CUDA)**. It is *not* the MacBook Pro (Apple M5 Pro, MPS, 64 GB unified) described in
> `CLAUDE.md`. Use this file when planning jobs that will run here.
>
> - Collected: **2026-10-07 19:21 MDT** (America/Denver) from Windows itself (not WSL/VM).
> - Raw machine-readable dump: [`scripts/machine_specs/windows_laptop_specs.raw.json`](scripts/machine_specs/windows_laptop_specs.raw.json)
> - Refresh: double-click `scripts/machine_specs/collect_windows_specs.bat` (or run
>   `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\machine_specs\collect_windows_specs.ps1`), then update this file.

## At a glance

| | |
|---|---|
| **Hostname** | `QUINNS-LAPTOP` |
| **Model** | Lenovo `21FWS0DU00` (machine type 21FW, ThinkPad P1 Gen 6 family) · BIOS N3ZET56W (1.43) |
| **OS** | Windows 11 Pro 26H2, build 26300.9457, 64-bit |
| **CPU** | Intel Core i7-13800H, **14 cores (6P + 8E) / 20 threads**, 2.5 GHz base (P-cores turbo to ~5.2 GHz), L2 11.5 MB, L3 24 MB |
| **RAM** | **32 GB DDR5-5600** (1 × 32 GB SK Hynix HMCG88AGBSA092N SODIMM) · 2 slots, **1 free**, max 96 GB |
| **GPU (compute)** | **NVIDIA GeForce RTX 4060 Laptop GPU, 8 GB GDDR6 (8188 MiB)** · Ada Lovelace, **compute capability 8.9** · up to 3105 MHz SM · power cap 80 W (105 W max) · PCIe 4.0 x8 · WDDM driver mode |
| **GPU (display)** | Intel UHD Graphics (iGPU) driving the internal 2560×1600 @ 165 Hz panel |
| **NVIDIA driver** | 596.58 · max CUDA runtime supported by driver: **13.2** |
| **Storage** | 1 × 1 TB KIOXIA KXG8AZNV1T02 NVMe SSD · `C:` 1.02 TB NTFS, **~220 GB free** (as collected) |
| **Power** | Battery present; on AC at collection time; power plan **Balanced** |

## Software state (as collected)

| Item | Status |
|---|---|
| Python | 3.14.2 (default via `py`), 3.13, 3.11 (Microsoft Store). **No Python 3.12** |
| PyTorch | **Not installed** (default interpreter) |
| MONAI / nibabel / SimpleITK / MLflow | **Not installed** · numpy 2.4.0 present |
| CUDA toolkit (`nvcc`) | Not installed / not on PATH (not required — PyTorch wheels bundle the CUDA runtime) |
| conda | Not installed |
| git | 2.53.0.windows.1 |
| Docker | 29.6.2 (Docker Desktop) |
| WSL2 | Installed: `Ubuntu` (WSL 2, default) and `docker-desktop` — both stopped at collection time |

## What this means for PROWL training

**Key differences from the MacBook (main machine):**

| | MacBook Pro (main) | This Windows laptop |
|---|---|---|
| Backend | `mps` | **`cuda`** |
| Accelerator memory | 64 GB unified | **8 GB dedicated VRAM** (+ 32 GB system RAM) |
| Mixed precision | partial on MPS; repo defaults to fp32 | **fp16/bf16 AMP and TF32 fully supported** (CC 8.9) |
| CPU threads | 18 cores | 20 threads |
| Internal free disk | — | ~220 GB (**too small for the ~340 GB PanTS dataset**) |

1. **VRAM (8 GB) is the binding constraint.** Recipes tuned for 64 GB unified memory will not transfer directly.
   For SegResNet at ROI 96³ with `num_samples=4`, plan on **AMP (`torch.autocast("cuda", dtype=torch.bfloat16)` or fp16 + GradScaler)**
   and verify peak memory (`torch.cuda.max_memory_allocated()`) on a short smoke run before a long job. Fallbacks: reduce
   `num_samples`, use gradient accumulation, or a smaller ROI. Sliding-window inference: keep `sw_batch_size` small and stitch on CPU
   (`device="cpu"` for the output buffer), as the Mac recipe already does.
2. **AMP changes the numerics vs. Mac fp32 runs.** Treat CUDA+AMP results as a separate condition when comparing against
   MPS fp32 experiments; record device/precision in run metadata.
3. **Dataset location.** The full dataset will not fit on `C:` (~220 GB free). Use the external drive (configured via
   `configs/local/roots.yaml`, which is git-ignored) or a cohort subset. Prefer a fast USB-C/Thunderbolt SSD; data loading
   from slow external storage will bottleneck the GPU.
4. **Python environment.** The repo requires **Python 3.12** (MLflow does not install on 3.14). Install Python 3.12, create
   `.venv312`, and install a **CUDA build of PyTorch** (e.g. `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128`
   or the current CUDA index from pytorch.org) before `pip install -r requirements.txt` — the default `requirements.txt` is written for macOS/MPS.
5. **Windows specifics.** `DataLoader` uses `spawn` on Windows: entry points need `if __name__ == "__main__":` guards, and
   worker startup is slower (start with `num_workers` 4–8; 20 threads available). Shell scripts like `scripts/run_exp26_24k.sh`
   won't run natively — use PowerShell equivalents, Git Bash, or run the pipeline inside **WSL2 Ubuntu** (CUDA works in WSL2 with this
   Windows driver; no Linux NVIDIA driver needed).
6. **Thermals / power.** It's a laptop: keep it on AC, switch the Windows power mode to **Best performance** for long runs,
   and expect the GPU to hold ~80 W. It ran at 67 °C idle-ish at collection, so watch for thermal throttling on multi-hour jobs
   (`nvidia-smi -l 5`).
7. **Free memory headroom.** Only one RAM slot is populated; adding a second 32 GB DDR5-5600 SODIMM would give 64 GB and
   dual-DIMM operation, which helps CPU-side caching (`CacheDataset`/`PersistentDataset`) for 3D volumes.
