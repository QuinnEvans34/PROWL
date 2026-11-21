"""Isolated CPU-only inspection. No nnU-Net trainer import or unrestricted pickle."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import time

WEIGHT_SHA = "7232a6296d320da1d60debe873a1d3fcad74e9404272db8f7440e30d62c5997a"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--weights", type=Path, required=True)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--source-sha256", required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--numpy-float-metadata", action="store_true")
    args = p.parse_args()
    start = time.monotonic()
    assert args.weights.stat().st_size == 466715133
    assert hashlib.sha256(args.weights.read_bytes()).hexdigest() == WEIGHT_SHA
    source = args.source.read_bytes()
    assert hashlib.sha256(source).hexdigest() == args.source_sha256
    import torch
    torch.set_num_threads(2)
    torch.set_default_device("cpu")
    unsafe = torch.serialization.get_unsafe_globals_in_checkpoint(args.weights)
    # Optional exact legacy scalar support, never weights_only=False or user classes.
    result = dict(weight_sha256=WEIGHT_SHA, source_sha256=args.source_sha256,
                  torch_version=torch.__version__, device="cpu", unsafe_globals=unsafe,
                  model_calls=0, optimizer_updates=0, clinical_data_reads=0)
    try:
        if args.numpy_float_metadata:
            import numpy as np
            assert set(unsafe) == {"numpy.core.multiarray.scalar", "numpy.dtype"}
            allowed = [(np._core.multiarray.scalar, "numpy.core.multiarray.scalar"),
                       np.dtype, np.dtypes.Float64DType, np.dtypes.Float32DType]
            with torch.serialization.safe_globals(allowed):
                checkpoint = torch.load(args.weights, map_location="cpu", weights_only=True)
            result["restricted_numpy_metadata"] = ["numpy.core.multiarray.scalar", "numpy.dtype", "numpy.dtypes.Float64DType", "numpy.dtypes.Float32DType"]
        else:
            checkpoint = torch.load(args.weights, map_location="cpu", weights_only=True)
    except Exception as exc:
        result.update(status="SAFE_LOAD_REFUSED", error=repr(exc), seconds=time.monotonic()-start)
        with args.output.open("x") as f:
            json.dump(result, f, indent=2)
        print(json.dumps(result))
        return
    state = checkpoint["state_dict"]
    assert all(isinstance(k, str) and isinstance(t, torch.Tensor) for k, t in state.items())
    assert all(t.device.type == "cpu" and torch.isfinite(t).all() for t in state.values())
    result.update(status="SAFE_LOAD_PASS", checkpoint_keys=list(checkpoint),
                  epoch=checkpoint.get("epoch"), state_entries=len(state),
                  state_elements=sum(t.numel() for t in state.values()),
                  tensors={k: dict(shape=list(t.shape), dtype=str(t.dtype), elements=t.numel())
                           for k, t in state.items()})
    if args.smoke:
        # Compile only the pinned upstream nn.Module definitions; trainers never execute.
        names = {"Decoder", "STUNet", "BasicResBlock", "Upsample_Layer_nearest"}
        nodes = [n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name in names]
        assert {n.name for n in nodes} == names
        scope = {"torch": torch, "nn": torch.nn}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(args.source), "exec"), scope)
        torch.manual_seed(42)
        model = scope["STUNet"](1, 3, pool_op_kernel_sizes=[[2,2,2]]*5,
                                conv_kernel_sizes=[[3,3,3]]*6, enable_deep_supervision=True)
        target = model.state_dict()
        new_heads = {k: t.clone() for k,t in target.items() if k.startswith("seg_outputs.")}
        loaded, skipped = {}, {}
        for k,t in state.items():
            if k.startswith("seg_outputs."):
                skipped[k] = list(t.shape)
                continue
            assert k in target and t.shape == target[k].shape and t.dtype == target[k].dtype, k
            loaded[k] = t
        assert set(loaded) == {k for k in target if not k.startswith("seg_outputs.")}
        changed = sum(not torch.equal(target[k], v) for k,v in loaded.items())
        target.update(loaded)
        model.load_state_dict(target, strict=True)
        assert all(torch.equal(model.state_dict()[k], v) for k,v in loaded.items())
        assert all(torch.equal(model.state_dict()[k], v) for k,v in new_heads.items())
        result.update(original_parameter_elements=sum(t.numel() for t in state.values()),
                      transferred_parameter_elements=sum(t.numel() for t in loaded.values()),
                      new_parameter_elements=sum(t.numel() for t in new_heads.values()),
                      model_parameter_elements=sum(p.numel() for p in model.parameters()),
                      changed_from_random_tensors=changed, loaded_keys=list(loaded),
                      skipped_head_shapes=skipped, new_head_shapes={k:list(t.shape) for k,t in new_heads.items()},
                      transferred_exact=True, new_heads_preserved=True)
        del checkpoint, state, loaded, target
        x = torch.randn(1,1,64,64,64, device="cpu")
        y = torch.randint(0,3,(1,64,64,64), device="cpu")
        outputs = model(x)
        assert len(outputs) == 5 and outputs[0].shape == (1,3,64,64,64)
        losses = []
        for logits in outputs:
            labels = torch.nn.functional.interpolate(y[:,None].float(), size=logits.shape[2:],
                                                     mode="nearest")[:,0].long()
            losses.append(torch.nn.functional.cross_entropy(logits, labels))
        loss = sum(losses)/len(losses)
        assert torch.isfinite(loss)
        loss.backward()
        grads = [p.grad for p in model.parameters()]
        assert all(g is not None and torch.isfinite(g).all() for g in grads)
        assert any(torch.count_nonzero(g) for g in grads)
        result.update(status="CPU_SYNTHETIC_FORWARD_BACKWARD_PASS", model_calls=1,
                      output_shapes=[list(o.shape) for o in outputs], loss=float(loss.detach()),
                      finite_all_gradients=True, nonzero_gradients=True,
                      optimizer_updates=0, production_training_qualified=False)
    result["seconds"] = time.monotonic()-start
    with args.output.open("x") as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ("tensors","loaded_keys")}))


if __name__ == "__main__":
    main()
