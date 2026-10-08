#!/usr/bin/env python3
"""Train Level 4.5 segmentation — SegResNet (scratch or SuPreM-transfer).

Stage 0 (overfit gate) — prove the loop by memorizing 1-2 cases:
  python scripts/train.py --overfit 2 --max-iters 600 --scratch

General training on the dev subset:
  python scripts/train.py --split dev_subset --epochs 60

Logs to MLflow and checkpoints to outputs/checkpoints/. Resumable via --resume.
"""
import argparse
import signal
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils.config import load_config, get
from src.utils.seed import set_seed
from src.utils import paths as P
from src.data.dataset import get_dataset
from src.models.segresnet import build_model, load_suprem, load_init_weights, set_encoder_requires_grad, sha256_file
from src.training.losses import build_loss
from src.training.metrics import DiceEvaluator
from src.training import trainer as T

from monai.data import DataLoader, list_data_collate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/level45.yaml")
    ap.add_argument("--experiment", help="Versioned full-run YAML (duration/cohorts/cadences); no pilot limits")
    ap.add_argument("--preflight", action="store_true", help="Check experiment metadata only; do not train")
    ap.add_argument("--inspect-input-paths", action="store_true", help="Also stat selected image/mask/weight paths during preflight")
    ap.add_argument("--split", default="dev_subset")
    ap.add_argument("--overfit", type=int, default=None, help="limit to N cases (Stage 0)")
    ap.add_argument("--max-iters", type=int, default=None)
    ap.add_argument("--epochs", type=int, default=None)
    ap.add_argument("--scratch", action="store_true", help="force from-scratch (no SuPreM)")
    ap.add_argument("--transfer", action="store_true", help="force SuPreM transfer")
    ap.add_argument("--log-every", type=int, default=25)
    ap.add_argument("--ckpt-every", type=int, default=200)
    ap.add_argument("--no-mlflow", action="store_true")
    ap.add_argument("--run-name", default=None, help="MLflow run name (auto-built from the config if omitted)")
    ap.add_argument("--positive", action="store_true", help="draw overfit cases from tumor-positive cases only")
    ap.add_argument("--no-cache", action="store_true", help="disable caching (plain Dataset, slowest)")
    ap.add_argument("--cache", choices=["ram", "disk", "none"], default=None,
                    help="dataset cache mode (overrides config training.cache): "
                         "ram=RAM CacheDataset, disk=persistent SSD cache (scales past RAM, survives resume), none")
    ap.add_argument("--val-split", default="val")
    ap.add_argument("--val-limit", type=int, default=0, help=">0 enables validation on N held-out cases")
    ap.add_argument("--val-every", type=int, default=500)
    ap.add_argument("--val-positive", action="store_true",
                    help="validate on tumor-positive cases only (meaningful lesion Dice)")
    ap.add_argument("--resume", default=None)
    ap.add_argument("--stop-after-step", type=int, default=None,
                    help="operational stop: end the loop at this global step while keeping --max-iters "
                         "as the LR-scheduler horizon (so you can pause a long run and continue later "
                         "with the SAME schedule). e.g. --max-iters 24000 --stop-after-step 12000")
    ap.add_argument("--strict-resume", dest="strict_resume", action="store_true", default=None,
                    help="fail closed on resume: require matching recipe metadata + optimizer/scheduler "
                         "state (default ON for anatomy5, OFF otherwise)")
    ap.add_argument("--no-strict-resume", dest="strict_resume", action="store_false",
                    help="allow lenient resume (fresh optimizer fallback) even for anatomy5")
    ap.add_argument("--patch", type=int, default=None,
                    help="override cube patch size for training AND sliding-window eval (e.g. 128)")
    ap.add_argument("--num-samples", type=int, default=None,
                    help="override crops per volume per step (lower this if a bigger --patch runs out of memory)")
    ap.add_argument("--spacing", type=float, default=None,
                    help="override isotropic target spacing in mm (e.g. 1.0 for finer resolution)")
    ap.add_argument("--crop-pancreas", type=float, default=None,
                    help="oracle ROI: crop to the ground-truth pancreas + this many mm of margin (e.g. 20)")
    ap.add_argument("--crop-native", type=int, default=None,
                    help="CLARITY: crop to pancreas in NATIVE space (before resample) + this many native-voxel margin (e.g. 24)")
    ap.add_argument("--whole-box", action="store_true",
                    help="EXP-12: feed the WHOLE pancreas box (padded/cropped to one --patch cube) instead of random sub-patches; use with --crop-native/--crop-pancreas")
    ap.add_argument("--roi-source", choices=["union", "pancreas"], default=None,
                    help="what the ROI crop is built from: union (pancreas+lesion, legacy) or pancreas (organ only, no lesion leak)")
    ap.add_argument("--loss", choices=["dice_focal", "dice_ce", "tversky", "tversky_focal"], default=None,
                    help="EXP-18: override the loss. tversky/tversky_focal penalize false positives to fight over-segmentation")
    ap.add_argument("--tversky-alpha", type=float, default=None, help="Tversky FALSE-POSITIVE weight (raise to fight over-segmentation, e.g. 0.7)")
    ap.add_argument("--tversky-beta", type=float, default=None, help="Tversky false-negative weight (e.g. 0.3)")
    # ---- EXP-26 anatomy-aware ----
    ap.add_argument("--label-mode", choices=["pancreas_lesion", "anatomy5"], default=None,
                    help="anatomy5 = 5-class model (bg/head/body/tail/lesion) with the collapsed "
                         "primary + head/body/tail auxiliary loss")
    ap.add_argument("--pancreas-resolver", choices=["combined", "hbt_union"], default=None,
                    help="how the pancreas organ mask is built (decoupled from label-mode)")
    ap.add_argument("--lambda-anat", type=float, default=None,
                    help="EXP-26 auxiliary weight: 26A control = 0.0, 26B treatment = 0.3")
    ap.add_argument("--init-weights", default=None,
                    help="load this frozen init checkpoint (scripts/make_init_checkpoint.py) so both "
                         "arms start byte-identical; records its SHA-256 in the run metadata")
    ap.add_argument("--train-ids", default=None, help="explicit frozen training cohort id file (bypasses --split)")
    ap.add_argument("--val-ids", default=None, help="explicit frozen validation cohort id file (bypasses --val-split/--val-positive)")
    ap.add_argument("--report-ids", default=None, help="frozen report cohort id file (hashed into metadata; not trained on)")
    ap.add_argument("--neg-ids", default=None, help="frozen tumor-free report cohort id file (hashed into metadata)")
    args = ap.parse_args()

    if args.preflight and not args.experiment:
        ap.error('--preflight requires --experiment')
    if args.experiment:
        from src.training import experiment_config as experiments
        experiment_started = time.monotonic()
        # One source of truth: do not allow CLI defaults/overrides to change a frozen recipe.
        allowed = {'--experiment', '--preflight', '--inspect-input-paths'}
        unexpected = [a.split('=')[0] for a in sys.argv[1:] if a.startswith('--') and a.split('=')[0] not in allowed]
        if unexpected: ap.error(f'Put experiment settings in YAML, not extra flags: {unexpected}')
        cfg = experiments.load_experiment(args.experiment)
        report = experiments.preflight(cfg, inspect_payload_paths=args.inspect_input_paths or not args.preflight)
        if args.preflight:
            import json
            print(json.dumps(report, indent=2))
            return 0 if report['ready'] else 2
        if not report['ready']:
            raise SystemExit('Experiment not ready:\n' + '\n'.join(report['errors']))
        experiments.prepare_run(cfg, report)
        experiments.apply_arguments(args, cfg)
    else:
        cfg = load_config(args.config)
    # experiment overrides: change field of view without editing the config file.
    # patch drives both the training crop and the inference window so they always match.
    if args.patch:
        cfg["sampling"]["patch_size"] = [args.patch, args.patch, args.patch]
        cfg["inference"]["sw_roi_size"] = [args.patch, args.patch, args.patch]
        print(f"[override] patch/roi -> {args.patch}^3")
    if args.num_samples:
        cfg["sampling"]["num_samples"] = args.num_samples
        print(f"[override] num_samples -> {args.num_samples}")
    if args.spacing:
        cfg["preprocessing"]["target_spacing"] = [args.spacing, args.spacing, args.spacing]
        print(f"[override] target_spacing -> {args.spacing}mm")
    if args.crop_pancreas is not None:
        cfg["preprocessing"]["crop_to_pancreas_margin_mm"] = args.crop_pancreas
        print(f"[override] crop to pancreas ROI + {args.crop_pancreas}mm margin (oracle ROI)")
    if args.crop_native is not None:
        cfg["preprocessing"]["crop_native_margin_vox"] = args.crop_native
        print(f"[override] CLARITY crop-native: pancreas ROI in native space + {args.crop_native}-voxel margin, then resample")
    if args.whole_box:
        cfg["preprocessing"]["whole_box"] = True
        print(f"[override] WHOLE-BOX: feeding the entire pancreas box as one {get(cfg, 'sampling.patch_size')} cube (no random sub-patch)")
    if args.roi_source:
        cfg["preprocessing"]["roi_source"] = args.roi_source
        print(f"[override] ROI source = {args.roi_source} ({'pancreas organ only, no lesion leak' if args.roi_source=='pancreas' else 'pancreas+lesion, legacy'})")
    if args.loss:
        cfg.setdefault("loss", {})["name"] = args.loss
        print(f"[override] loss -> {args.loss}")
    if args.tversky_alpha is not None:
        cfg.setdefault("loss", {})["tversky_alpha"] = args.tversky_alpha
        print(f"[override] tversky alpha (false-positive weight) -> {args.tversky_alpha}")
    if args.tversky_beta is not None:
        cfg.setdefault("loss", {})["tversky_beta"] = args.tversky_beta
        print(f"[override] tversky beta (false-negative weight) -> {args.tversky_beta}")
    # ---- EXP-26 anatomy-aware wiring ----
    if args.label_mode:
        cfg["label_mode"] = args.label_mode
        if args.label_mode == "anatomy5":
            cfg["model"]["out_channels"] = 5
            cfg.setdefault("loss", {})["name"] = "anatomy_aware"   # build_loss also auto-detects label_mode
            # anatomy5's pancreas is head∪body∪tail; crop to that organ box, no lesion leak.
            cfg["preprocessing"]["roi_source"] = cfg["preprocessing"].get("roi_source", "pancreas")
        print(f"[override] label_mode -> {args.label_mode} (out_channels={cfg['model']['out_channels']})")
    if args.pancreas_resolver:
        cfg["pancreas_resolver"] = args.pancreas_resolver
        print(f"[override] pancreas_resolver -> {args.pancreas_resolver}")
    if args.lambda_anat is not None:
        cfg.setdefault("loss", {})["lambda_anat"] = args.lambda_anat
        print(f"[override] lambda_anat -> {args.lambda_anat}  ({'26A control' if args.lambda_anat == 0 else '26B treatment' if args.lambda_anat == 0.3 else 'custom'})")
    set_seed(int(get(cfg, "seed", 42)))
    device = T.get_device(cfg)
    dp = P.data_paths(cfg)

    # EXP-26 anatomy5 must run with the shared init + all four frozen cohorts (Codex safeguard #3):
    # missing files must ABORT, never silently become empty sets or a random init.
    if cfg.get("label_mode") == "anatomy5":
        _required = {"--init-weights": args.init_weights, "--train-ids": args.train_ids,
                     "--val-ids": args.val_ids, "--report-ids": args.report_ids, "--neg-ids": args.neg_ids}
        _missing = [k for k, v in _required.items() if not v]
        assert not _missing, f"anatomy5 REQUIRES {_missing} (shared init + frozen cohorts) — refusing to run."
        for k, v in _required.items():
            assert Path(v).exists(), f"anatomy5 {k} file not found: {v}"
        print("[anatomy5] shared init + 4 frozen cohort files present  OK")

    # SAFETY GUARD (Codex audit 2026-07-19): a TRAINING split must never intersect val/test.
    # This is the assertion that would have caught the make_scaled_split leakage before it ever trained.
    def _read_ids(name):
        f = Path(dp["splits_dir"]) / f"{name}.txt"
        return {x.strip() for x in f.read_text().split() if x.strip()} if f.exists() else set()
    def _read_ids_file(path):
        return {x.strip() for x in Path(path).read_text().split() if x.strip()} if path and Path(path).exists() else set()

    if args.train_ids:
        # EXP-26 frozen-cohort guard: the explicit training cohort must be disjoint from EVERY
        # evaluated cohort (val20 / report40 / report40_neg) AND the official test split.
        _tr = _read_ids_file(args.train_ids)
        _others = {"val-ids": _read_ids_file(args.val_ids), "report-ids": _read_ids_file(args.report_ids),
                   "neg-ids": _read_ids_file(args.neg_ids), "official-test": _read_ids("test")}
        for _name, _s in _others.items():
            _leak = _tr & _s
            assert not _leak, (f"LEAKAGE ABORT: --train-ids shares {len(_leak)} case(s) with {_name} "
                               f"(e.g. {sorted(_leak)[:5]}).")
        print(f"[cohort-check] --train-ids ({len(_tr)} cases) disjoint from val/report/neg/test  OK")
    elif args.split not in ("val", "test"):
        _train_ids = _read_ids(args.split)
        _leak = _train_ids & (_read_ids("val") | _read_ids("test"))
        assert not _leak, (f"LEAKAGE ABORT: training split '{args.split}' shares {len(_leak)} case(s) with "
                           f"val/test (e.g. {sorted(_leak)[:5]}). Rebuild it from train.txt (make_scaled_split.py).")
        print(f"[split-check] '{args.split}' is disjoint from val+test ({len(_train_ids)} train cases)  OK")

    epoch_iters = int(get(cfg, "training.epoch_iters", 250))
    total_iters = args.max_iters or (args.epochs or int(get(cfg, "training.max_epochs", 100))) * epoch_iters

    # --- cache mode: --no-cache > --cache > config training.cache (default ram) ---
    if args.no_cache:
        cache_mode = "none"
    elif args.cache:
        cache_mode = args.cache
    else:
        cache_mode = str(get(cfg, "training.cache", "ram"))
        if cache_mode not in ("ram", "disk", "none"):
            cache_mode = "ram"
    if cache_mode == "disk":
        cdir = get(cfg, "training.cache_dir", None) or str(dp["output_dir"] / "cache")
        print(f"[cache] mode=disk -> {cdir} (first epoch fills it, then fast + resume-safe)")
    else:
        print(f"[cache] mode={cache_mode}")

    # --- data ---
    seed = int(get(cfg, "seed", 42))
    override_ids = None
    split_label = args.split
    if args.train_ids:
        override_ids = [x.strip() for x in Path(args.train_ids).read_text().split() if x.strip()]
        split_label = f"ids:{Path(args.train_ids).stem}"
        print(f"[cohort] training on {len(override_ids)} cases from {args.train_ids}")
    elif args.positive:
        import pandas as pd
        m = pd.read_csv(dp["manifest"])
        override_ids = m[(m["split"] == "train") & (m["has_lesion"].astype(bool))]["case_id"].tolist()
        print(f"[positive] {len(override_ids)} tumor-positive train cases available")
    ds = get_dataset(cfg, args.split, train=True, cache=cache_mode,
                     limit=args.overfit, ids=override_ids)
    n_cases = len(ds)

    # DETERMINISTIC, RESUMABLE data pipeline. The (case index, augmentation) at global step S is a
    # pure function of (seed, S): each epoch's shuffle is seeded by (seed, epoch), and the MONAI
    # random-transform stream is reseeded per step by (seed, S). Consequences:
    #   * a Ctrl-C + --resume reproduces the SAME trajectory as an uninterrupted run (step S always
    #     uses the same case + same augmentation), so interruptions are scientifically invisible;
    #   * both EXP-26 arms see identical data per step regardless of how each is interrupted, so the
    #     ONLY difference between them stays lambda_anat.
    _perm_cache = {}
    _SEED_MOD = 2_147_483_647

    def _epoch_perm(e):
        if e not in _perm_cache:
            g = torch.Generator().manual_seed((seed * 1_000_003 + e) % _SEED_MOD)
            _perm_cache[e] = torch.randperm(n_cases, generator=g).tolist()
        return _perm_cache[e]

    def get_batch(step):
        e, pos = divmod(step, n_cases)
        idx = _epoch_perm(e)[pos]
        try:
            ds.transform.set_random_state(seed=(seed * 1_000_003 + step) % _SEED_MOD)
        except Exception as ex:
            if cfg.get("label_mode") == "anatomy5":
                raise RuntimeError(f"anatomy5 requires a seedable transform RNG; set_random_state failed: {ex}")
        return list_data_collate([ds[idx]])

    print(f"device={device}  split={split_label}  cases={n_cases}  total_iters={total_iters}")

    val_loader = None
    if args.val_ids:
        # explicit frozen validation cohort (bypasses --val-split/--val-positive/--val-limit)
        val_ids = [x.strip() for x in Path(args.val_ids).read_text().split() if x.strip()]
        val_ds = get_dataset(cfg, args.val_split, train=False, cache=cache_mode, ids=val_ids)
        val_loader = DataLoader(val_ds, batch_size=1, shuffle=False, num_workers=0)
        print(f"validation: {len(val_ds)} cases from {args.val_ids} every {args.val_every} iters (sliding-window)")
    elif args.val_limit > 0:
        val_ids = None
        if args.val_positive:
            import pandas as pd
            m = pd.read_csv(dp["manifest"])
            vset = {x.strip() for x in (dp["splits_dir"] / f"{args.val_split}.txt").read_text().split() if x.strip()}
            val_ids = m[(m["case_id"].isin(vset)) & (m["has_lesion"].astype(bool))]["case_id"].tolist()
        val_ds = get_dataset(cfg, args.val_split, train=False, cache=cache_mode, limit=args.val_limit, ids=val_ids)
        val_loader = DataLoader(val_ds, batch_size=1, shuffle=False, num_workers=0)
        tag = "tumor-positive " if args.val_positive else ""
        print(f"validation: {len(val_ds)} {tag}cases every {args.val_every} iters (sliding-window)")

    # --- model (scratch vs transfer) ---
    use_pretrained = get(cfg, "transfer.use_pretrained", True)
    if args.scratch:
        use_pretrained = False
    if args.transfer:
        use_pretrained = True
    model = build_model(cfg)
    init_sha = None
    if args.init_weights:
        # EXP-26: both arms load ONE frozen init file -> byte-identical weights at step 0.
        init_sha = load_init_weights(model, args.init_weights)
        use_pretrained = True   # this init is SuPreM-derived
        print(f"[init] loaded frozen init {args.init_weights}  sha256={init_sha}")
    model = model.to(device)
    if not args.init_weights:
        if use_pretrained and dp["pretrained_weights"].exists():
            if args.experiment:
                experiments.load_suprem_checked(model, cfg['_experiment']['initialization'])
            else:
                load_suprem(model, dp["pretrained_weights"])
        elif use_pretrained:
            if args.experiment:
                raise RuntimeError('Selected SuPreM checkpoint is unavailable; scratch fallback forbidden')
            print(f"[warn] pretrained weights missing at {dp['pretrained_weights']} — training from scratch")
            use_pretrained = False

    # optional encoder freeze for transfer warm-up
    freeze_iters = 0
    if use_pretrained and int(get(cfg, "transfer.freeze_encoder_epochs", 0)) > 0:
        freeze_iters = min(int(get(cfg, "transfer.freeze_encoder_epochs")) * epoch_iters, total_iters // 4)
        set_encoder_requires_grad(model, False)
        print(f"[transfer] encoder frozen for first {freeze_iters} iters")

    optimizer, base_lr = T.build_optimizer(cfg, model, transfer=use_pretrained)
    warmup = min(int(get(cfg, "scheduler.warmup_epochs", 2)) * epoch_iters, total_iters // 5)
    min_lr_ratio = float(get(cfg, "scheduler.min_lr", 1e-6)) / base_lr
    if args.overfit:
        min_lr_ratio = 1.0  # flat LR (no decay) so it can fully memorize the overfit set
    scheduler = T.build_scheduler(optimizer, warmup, total_iters, min_lr_ratio)
    loss_fn = build_loss(cfg)
    is_anat = cfg.get("label_mode") == "anatomy5"
    evaluator = DiceEvaluator(num_classes=int(get(cfg, "model.out_channels", 3)),
                              collapse=("anatomy5" if is_anat else None))

    # --- run identity + checkpoint metadata (built BEFORE resume so we can verify the checkpoint
    #     we resume actually belongs to THIS recipe — Codex resume-identity fix) ---
    import datetime
    loss_cfg = cfg.get("loss", {})
    samp_cfg = cfg.get("sampling", {})
    patch_sz = (samp_cfg.get("patch_size") or [96])[0]
    box_tag = "_wholebox" if get(cfg, "preprocessing.whole_box", False) else ""
    lam_tag = f"_lam{loss_cfg.get('lambda_anat', 0.0)}" if is_anat else ""
    run_name = args.run_name or (
        f"{'transfer' if use_pretrained else 'scratch'}_{loss_cfg.get('name', 'dice_ce')}"
        f"_bg{int(bool(loss_cfg.get('include_background', False)))}"
        f"_p{patch_sz}{box_tag}{lam_tag}_{samp_cfg.get('strategy', 'posneg')}_{total_iters}i"
    )
    run_stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    def _hash(path):
        return sha256_file(path) if path and Path(path).exists() else None
    out_ch = int(get(cfg, "model.out_channels", 3))
    class_names = (["bg", "head", "body", "tail", "lesion"] if is_anat
                   else ["bg", "pancreas", "lesion"][:out_ch])
    run_meta = {
        "label_mode": cfg.get("label_mode", "pancreas_lesion"),
        "pancreas_resolver": cfg.get("pancreas_resolver", "combined") if not is_anat else "hbt_union",
        "out_channels": out_ch,
        "class_names": class_names,
        "collapse_map": ({"1": "pancreas", "2": "pancreas", "3": "pancreas", "4": "lesion"} if is_anat else None),
        # full spatial recipe — eval MUST match these or the numbers are invalid (Codex fix #3)
        "patch_size": list(get(cfg, "sampling.patch_size", [96, 96, 96])),
        "sw_roi_size": list(get(cfg, "inference.sw_roi_size", [96, 96, 96])),
        "target_spacing": list(get(cfg, "preprocessing.target_spacing", [1.5, 1.5, 1.5])),
        "crop_native_margin_vox": get(cfg, "preprocessing.crop_native_margin_vox"),
        "crop_to_pancreas_margin_mm": get(cfg, "preprocessing.crop_to_pancreas_margin_mm"),
        "roi_source": get(cfg, "preprocessing.roi_source", "union"),
        "whole_box": bool(get(cfg, "preprocessing.whole_box", False)),
        "lambda_anat": float(loss_cfg.get("lambda_anat", 0.0)),
        "loss_name": loss_cfg.get("name"),
        "seed": seed,
        "total_iters": total_iters,        # LR-scheduler horizon (Codex: verify on resume)
        "val_every": args.val_every,
        "init_weights": args.init_weights,
        "init_sha256": init_sha,
        "cohort_sha256": {
            "train": _hash(args.train_ids), "val20": _hash(args.val_ids),
            "report40": _hash(args.report_ids), "report40_neg": _hash(args.neg_ids),
        },
    }
    if is_anat:
        print(f"[meta] anatomy5  out_channels={out_ch}  lambda_anat={run_meta['lambda_anat']}  "
              f"init_sha={str(init_sha)[:12]}  cohort_sha(train)={str(run_meta['cohort_sha256']['train'])[:12]}")

    # per-arm ACTIVE checkpoint dir for anatomy5 so 26A and 26B never share best.pt/last.pt
    # (prevents one arm from clobbering — or being resumed from — the other's checkpoint).
    ckpt_dir = dp["output_dir"] / "checkpoints" / get(cfg, "mlflow.experiment", "run")
    if is_anat:
        ckpt_dir = ckpt_dir / run_name

    # --- resume (identity-verified; strict optimizer/scheduler for anatomy5) ---
    strict_resume = is_anat if args.strict_resume is None else args.strict_resume
    start = 0
    best = -1.0
    best_panc = 0.0
    best_val = -1.0
    if args.resume:
        # Verify the checkpoint belongs to THIS recipe BEFORE restoring anything, so you can never
        # accidentally resume 26A from a 26B checkpoint, a different horizon, cohort, init, or crop.
        _ck = torch.load(str(args.resume), map_location="cpu", weights_only=False)
        _meta = _ck.get("extra", {}) if isinstance(_ck, dict) else {}
        _keys = ["label_mode", "lambda_anat", "init_sha256", "cohort_sha256", "seed",
                 "patch_size", "sw_roi_size", "target_spacing", "crop_native_margin_vox",
                 "crop_to_pancreas_margin_mm", "whole_box", "roi_source", "loss_name",
                 "total_iters", "val_every"]
        _mism = {k: (_meta.get(k), run_meta.get(k)) for k in _keys if str(_meta.get(k)) != str(run_meta.get(k))}
        if strict_resume and (not _meta or _mism):
            _lines = "\n".join(f"    {k}: checkpoint={a!r}  now={b!r}" for k, (a, b) in _mism.items())
            raise SystemExit("RESUME ABORT: checkpoint recipe does not match the current command:\n"
                             + (_lines or "    (checkpoint has no metadata)")
                             + "\nResume with the EXACT original command + --resume, or fix the mismatch.")
        start, best = T.load_checkpoint(args.resume, model, optimizer, scheduler,
                                        map_location=device, strict=strict_resume)
        # last.pt now stores best_val directly (self-contained); still cross-check the sibling best.pt.
        if best is not None and best >= 0:
            best_val = float(best)
        sib = Path(args.resume).parent / "best.pt"
        if sib.exists() and sib.resolve() != Path(args.resume).resolve():
            try:
                bv = torch.load(str(sib), map_location="cpu", weights_only=False).get("best")
                if bv is not None and float(bv) > best_val:
                    best_val = float(bv)
            except Exception as e:
                print(f"[resume] could not read sibling best.pt ({e}); using loaded best_val")
        if not (start < total_iters):
            raise SystemExit(f"RESUME ABORT: checkpoint step {start} >= total_iters {total_iters} "
                             f"(already complete — nothing to resume).")
        if freeze_iters and start >= freeze_iters:
            set_encoder_requires_grad(model, True)
        print(f"resumed from {args.resume} at step {start}; best_val restored to {best_val:.4f}")

    # --- MLflow ---
    ml = None
    if not args.no_mlflow:
        try:
            import mlflow
            mlflow.set_tracking_uri(get(cfg, "mlflow.tracking_uri", "sqlite:///outputs/mlflow.db"))
            mlflow.set_experiment(get(cfg, "mlflow.experiment", "pants-level45"))
            mlflow.start_run(run_name=run_name)
            mlflow.log_params({
                "mode": "transfer" if use_pretrained else "scratch",
                "split": args.split, "overfit": args.overfit, "total_iters": total_iters,
                "lr": base_lr, "patch": get(cfg, "sampling.patch_size"),
                "loss": loss_cfg.get("name"),
                "loss.include_background": loss_cfg.get("include_background", True),
                "loss.focal_gamma": loss_cfg.get("focal_gamma", 2.0),
                "loss.lambda_dice": loss_cfg.get("lambda_dice", 1.0),
                "loss.lambda_focal": loss_cfg.get("lambda_focal", 1.0),
                "loss.class_weights": loss_cfg.get("class_weights"),
                "sampling.strategy": samp_cfg.get("strategy", "posneg"),
                "sampling.pos": samp_cfg.get("pos"), "sampling.neg": samp_cfg.get("neg"),
            })
            print(f"[mlflow] run '{run_name}' -> {get(cfg, 'mlflow.tracking_uri')}")
            ml = mlflow
        except Exception as e:
            # EXP-12 ran in a venv without mlflow and its metrics were lost. Make that
            # impossible to miss now: a loud banner instead of a quiet one-liner. The
            # on-disk archive + run_ledger.csv below still capture the run regardless.
            print("\n" + "!" * 70)
            print(f"[MLflow NOT logging]  {e}")
            print("  This run will NOT appear in the MLflow UI. If you want live tracking,")
            print("  stop now and launch from .venv312 (which has mlflow installed).")
            print("  The per-run checkpoint archive + run_ledger.csv WILL still record it.")
            print("!" * 70 + "\n")
    else:
        print("[MLflow] skipped (--no-mlflow). Run still recorded in the on-disk archive + run_ledger.csv.")

    # ckpt_dir was set above (per-arm for anatomy5); do NOT reassign here.

    # --- per-run checkpoint archive (the fix for the EXP-12 loss) ---
    # Every run still writes the shared best.pt/last.pt (so existing eval/resume runbooks
    # keep working), but it ALSO writes immutable copies into a unique, timestamped folder
    # that no later run can touch. run_info.txt makes each archived checkpoint self-documenting,
    # so a checkpoint can never again become an orphan whose provenance is unknown.
    run_dir = ckpt_dir / "runs" / f"{run_name}__{run_stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_info.txt").write_text(
        f"run_name: {run_name}\n"
        f"timestamp: {run_stamp}\n"
        f"split: {args.split}\n"
        f"mode: {'transfer' if use_pretrained else 'scratch'}\n"
        f"total_iters: {total_iters}\n"
        f"config: {args.config}\n"
        f"patch: {get(cfg, 'sampling.patch_size')}\n"
        f"spacing: {get(cfg, 'preprocessing.target_spacing')}\n"
        f"whole_box: {get(cfg, 'preprocessing.whole_box', False)}\n"
        f"crop_native_margin_vox: {get(cfg, 'preprocessing.crop_native_margin_vox')}\n"
        f"crop_to_pancreas_margin_mm: {get(cfg, 'preprocessing.crop_to_pancreas_margin_mm')}\n"
        f"loss: {loss_cfg.get('name')} include_background={loss_cfg.get('include_background')}\n"
        f"seed: {get(cfg, 'seed', 42)}\n"
    )
    print(f"[archive] keeper checkpoints for this run -> {run_dir}")

    # Graceful pause: first Ctrl-C finishes the current step, saves last.pt atomically, and exits
    # cleanly so --resume picks up exactly where it stopped. A second Ctrl-C force-quits.
    _stop = {"flag": False}

    def _on_sigint(signum, frame):
        if _stop["flag"]:
            raise KeyboardInterrupt
        _stop["flag"] = True
        print("\n[SIGINT] finishing current step, saving last.pt, then exiting cleanly. "
              "Press Ctrl-C again to force-quit.")
    signal.signal(signal.SIGINT, _on_sigint)

    # Operational stop: end the loop early while keeping total_iters as the LR-schedule horizon,
    # so a long run can be split across sessions and continued later with the SAME cosine schedule.
    stop_at = min(total_iters, args.stop_after_step) if args.stop_after_step else total_iters
    if stop_at < total_iters:
        print(f"[stop-after] loop stops at step {stop_at}; LR-schedule horizon stays {total_iters}. "
              f"Resume with the same command to continue toward {total_iters}.")
    paused = False

    model.train()
    t0 = time.time()
    running = 0.0
    for step in range(start, stop_at):
        if args.experiment:
            experiments.check_resources(cfg, elapsed=time.monotonic() - experiment_started)
        if freeze_iters and step == freeze_iters:
            set_encoder_requires_grad(model, True)
            print(f"[transfer] encoder unfrozen at step {step}")

        batch = get_batch(step)
        img = batch["image"].to(device)
        lab = batch["label"].to(device)
        optimizer.zero_grad(set_to_none=True)
        logits = model(img)
        loss = loss_fn(logits, lab)
        if args.experiment and not torch.isfinite(loss).all():
            raise RuntimeError(f'Nonfinite training loss at update {step + 1}; previous checkpoints retained')
        loss.backward()
        optimizer.step()
        scheduler.step()
        running += float(loss.detach())
        if args.experiment:
            experiments.record_event(cfg, event='update', step=step + 1, loss=float(loss.detach()),
                                     learning_rate=optimizer.param_groups[0]['lr'])

        if (step + 1) % args.log_every == 0:
            evaluator.reset()
            evaluator.update(logits.detach(), lab)
            d = evaluator.aggregate()
            avg = running / args.log_every
            running = 0.0
            lr = optimizer.param_groups[0]["lr"]
            rate = (step + 1 - start) / (time.time() - t0)
            les = d.get("lesion")
            les_str = f"{les:.3f}" if les is not None else " n/a "  # n/a = no lesion in these patches
            print(f"step {step+1}/{total_iters}  loss {avg:.4f}  "
                  f"dice[panc {d.get('pancreas',0):.3f} | lesion {les_str}]  "
                  f"lr {lr:.2e}  {rate:.2f} it/s")
            comp = getattr(loss_fn, "last", None)
            if comp:
                # smoke-scale diagnostic: watch primary vs aux magnitudes early (Codex asked for this
                # BEFORE committing to lambda_anat=0.3). If aux >> primary in the first ~100 steps, revisit.
                print(f"    [loss] primary {comp.get('primary', 0):.4f} "
                      f"(dice {comp.get('dice', 0):.4f} focal {comp.get('focal', 0):.4f})  "
                      f"aux {comp.get('aux', 0):.4f}")
            if ml:
                metrics = {"train/loss": avg, "train/dice_pancreas": d.get("pancreas", 0), "lr": lr}
                if les is not None:
                    metrics["train/dice_lesion"] = les
                if comp:
                    metrics.update({f"train/loss_{k}": v for k, v in comp.items()})
                ml.log_metrics(metrics, step=step + 1)
            best_panc = max(best_panc, d.get("pancreas", 0.0))
            if val_loader is None and d["mean"] > best:  # train-dice best only when not validating
                best = d["mean"]
                T.save_checkpoint(ckpt_dir / "best.pt", model, optimizer, scheduler, step + 1, best, extra=run_meta)
                T.save_checkpoint(run_dir / "best.pt", model, optimizer, scheduler, step + 1, best, extra=run_meta)  # immutable archive copy

        if val_loader is not None and ((step + 1) % args.val_every == 0 or (args.experiment and step + 1 == stop_at)):
            from src.inference.sliding_window import validate
            vd = validate(model, val_loader, evaluator, cfg, device)
            vp, vl = vd.get("pancreas", 0.0), vd.get("lesion")
            vl_str = f"{vl:.3f}" if vl is not None else " n/a "
            print(f"  [val @ {step+1}] dice  pancreas {vp:.3f} | lesion {vl_str}  (n={len(val_loader.dataset)})")
            if ml:
                vm = {"val/dice_pancreas": vp}
                if vl is not None:
                    vm["val/dice_lesion"] = vl
                ml.log_metrics(vm, step=step + 1)
            score = vl if vl is not None else vd.get("mean", 0.0)
            if args.experiment:
                experiments.record_event(cfg, event='validation', step=step + 1,
                                         pancreas_dice=vp, lesion_dice=vl, selection_score=score)
            if score > best_val:
                best_val = score
                T.save_checkpoint(ckpt_dir / "best.pt", model, optimizer, scheduler, step + 1, best_val, extra=run_meta)
                T.save_checkpoint(run_dir / "best.pt", model, optimizer, scheduler, step + 1, best_val, extra=run_meta)  # immutable archive copy
                print(f"  [val] new best (lesion {score:.3f}) -> saved best.pt (+ archive)")

        # last.pt stores best_val (the val keeper) so a resume is self-contained (Codex fix #4)
        keeper = best_val if val_loader is not None else best
        if (step + 1) % args.ckpt_every == 0:
            T.save_checkpoint(ckpt_dir / "last.pt", model, optimizer, scheduler, step + 1, keeper, extra=run_meta)

        if _stop["flag"]:
            # save at the EXACT stopping step (not total_iters) so --resume continues correctly
            T.save_checkpoint(ckpt_dir / "last.pt", model, optimizer, scheduler, step + 1, keeper, extra=run_meta)
            T.save_checkpoint(run_dir / "last.pt", model, optimizer, scheduler, step + 1, keeper, extra=run_meta)
            paused = True
            end_step = step + 1
            print(f"[SIGINT] paused + saved last.pt at step {end_step}. Resume with the SAME command + "
                  f"--resume {ckpt_dir / 'last.pt'}")
            break
    else:
        end_step = stop_at   # loop finished naturally (no break)

    # Only stamp the checkpoint as "reached end_step" when NOT paused. A paused run already saved
    # its true step above; overwriting here with a higher step was the bug that made resume a no-op.
    if not paused:
        keeper = best_val if val_loader is not None else best
        T.save_checkpoint(ckpt_dir / "last.pt", model, optimizer, scheduler, end_step, keeper, extra=run_meta)
        T.save_checkpoint(run_dir / "last.pt", model, optimizer, scheduler, end_step, keeper, extra=run_meta)

    status = "paused" if paused else ("stopped" if end_step < total_iters else "complete")

    # persistent, MLflow-independent record of every run (one row per run, never overwritten)
    ledger = ckpt_dir / "run_ledger.csv"
    new_ledger = not ledger.exists()
    with open(ledger, "a") as f:
        if new_ledger:
            f.write("timestamp,run_name,split,mode,end_step,total_iters,status,best_val_lesion,archive_dir\n")
        bv = f"{best_val:.4f}" if best_val >= 0 else ""
        f.write(f"{run_stamp},{run_name},{args.split},"
                f"{'transfer' if use_pretrained else 'scratch'},{end_step},{total_iters},{status},{bv},{run_dir.name}\n")

    print(f"\n{status.upper()} at step {end_step}/{total_iters}. shared checkpoints in {ckpt_dir}")
    if end_step < total_iters:
        _rp = ckpt_dir / "last.pt"
        if paused:
            print(f"[continue] Ctrl-C pause: rerun the SAME command + --resume {_rp}")
        else:
            print(f"[continue] reached the --stop-after-step limit. To train toward {total_iters}: "
                  f"rerun with --resume {_rp} and REMOVE --stop-after-step (or set it to {total_iters}). "
                  f"Rerunning with the same --stop-after-step {args.stop_after_step} would do 0 steps.")
    print(f"[archive] keeper copies safe in {run_dir}  (best.pt + last.pt + run_info.txt)")
    print(f"[ledger]  run appended to {ledger}")
    if best_val >= 0:
        print(f"best VAL lesion-Dice {best_val:.3f}")
    if args.overfit:
        print("Stage 0 gate: PASS (pancreas overfit)" if best_panc > 0.90 else
              f"Stage 0 gate: not yet (best pancreas {best_panc:.3f}) — train longer")
    if ml:
        ml.end_run()
    if args.experiment:
        experiments.record_event(cfg, event='finished', state=status, completed_updates=end_step)


if __name__ == "__main__":
    sys.exit(main())
