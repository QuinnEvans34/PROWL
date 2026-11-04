"""One bounded CPU saved-output review; no inference, scoring, repair or retry."""
import os,sys,json,time,subprocess,shutil,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.qualify_matched_physical_cascade_20261102 import sha,write,tree_bytes
from src.operations.full_training_platform import require_ac,watch_windows
OUT=Path("E:/PROWL/readiness/week05-seven-visual-review-20261104-a01")
BACK=Path("C:/Users/quinn/PROWL-Backups")/OUT.name
BASE=Path("E:/PROWL/artifacts/week05-autonomous70-20261103-a03")
PLAN_SHA="10d9674f0476d6d854a478bd9406c30a2ea154a854976d66378fb4701224dd8e"

def gate():
    require_ac()
    for drive in ["C:/","E:/"]:
        if shutil.disk_usage(drive).free<100*1024**3:raise RuntimeError("Free-space floor")
    if OUT.exists() and tree_bytes(OUT)>2*1024**3:raise RuntimeError("Output cap")

def worker():
    import nibabel as nib
    import numpy as np
    from src.inference.native_error_review_20261104 import canonical,selected_component,render
    started=time.monotonic();plan=json.loads((OUT/"plan.json").read_text());request=json.loads((BASE/"request.json").read_text())
    assert sha(OUT/"plan.json")==PLAN_SHA
    for k,v in plan["identities"].items():assert sha(BASE/(k.removesuffix("_sha256")+".json"))==v
    receipt=json.loads((OUT/"request.json").read_text())
    for p,h in receipt["code_pins"].items():assert sha(p)==h
    images=[];cases=[]
    for target in plan["cases"]:
        gate();i=target["case_id"];print("start",i,flush=True)
        case=next(c for c in request["cases"] if c["case_id"]==i);d=BASE/i/"autonomous"
        for k,v in target["source_report_sha256"].items():assert sha(d/(k+".json"))==v
        score=json.loads((d/"score.json").read_text());result=json.loads((d/"result.json").read_text());access=json.loads((d/"input-access.json").read_text())
        assert not access["pancreas_reference_loaded"] and not access["lesion_reference_loaded"]
        paths={k:Path(v) for k,v in case["files"].items()};paths["prediction"]=d/"prediction.nii.gz"
        expected={**case["identity"]["source_sha256"],"prediction":result["artifacts"]["prediction.nii.gz"]}
        bindings={}
        for k,p in paths.items():
            h=sha(p);assert h==expected[k],str(p);bindings[k]=h
        assert bindings["prediction"]==score["file_sha256"]["prediction"]
        for k in ["pancreas","lesion"]:assert bindings[k]==score["file_sha256"][k]
        ns={k:nib.load(p) for k,p in paths.items()};base=ns["ct"]
        assert base.header.get_xyzt_units()[0]=="mm"
        assert list(base.shape)==result["source_shape"] and np.allclose(base.affine,result["source_affine"],atol=1e-5,rtol=0)
        for k,n in ns.items():
            assert n.shape==base.shape and np.allclose(n.affine,base.affine,atol=1e-5,rtol=0),k
        units=[ns[k].header.get_xyzt_units()[0] for k in ["pancreas","lesion"]]
        assert units==target["reference_units"]==score["reference_units"]
        assert all(u in ["mm","unknown"] for u in units)
        ct,aff,transform=canonical(np.asarray(base.dataobj,dtype=np.float32),base.affine)
        pan0=np.asarray(ns["pancreas"].dataobj,dtype=bool);les0=np.asarray(ns["lesion"].dataobj,dtype=bool);pred0=np.asarray(ns["prediction"].dataobj,dtype=np.uint8)
        assert set(np.unique(pred0)).issubset({0,1,2})
        pan=canonical(pan0,base.affine)[0];les=canonical(les0,base.affine)[0];pred=canonical(pred0,base.affine)[0]
        evidence=result["evidence"];low=evidence["region_low"];high=evidence["region_high"]
        assert all(0<=low[j]<high[j]<=ct.shape[j] for j in range(3))
        assert np.allclose(evidence["parent_geometry"]["affine"],aff,atol=1e-5,rtol=0)
        fp=target["top_false_positive_components"]
        if i=="PanTS_00008711":
            spill=max(score["lesion_components"]["predicted"],key=lambda x:(x["voxels"]-x["overlap_voxels"],-x["component_id"]))
            assert spill["any_overlap"] and spill["component_id"]==4
            amendment=json.loads((OUT/"approved-amendment.json").read_text())
            assert sha(OUT/"approved-amendment.json")=="1463a206dfbf549804d4877cb82e996549ab0ba56990f6e7d7a946749349d979"
            assert spill==amendment["component"] and target["source_report_sha256"]==amendment["source_report_sha256"]
            write(OUT/"selection-amendment.json",dict(case_id=i,original_plan_sha256=PLAN_SHA,reason="Mac authorized target amendment: inspect partial-overlap spillover instead of trivial1voxel FP",removed=fp[2],added=spill,source_score_sha256=sha(d/"score.json")))
            fp=fp[:2]+[spill]
        for kind,components in [("miss",target["missed_reference_components"]),("fp",fp)]:
            for row in components:
                assert row in score["lesion_components"]["reference" if kind=="miss" else "predicted"]
                selected=canonical(selected_component(les0 if kind=="miss" else pred0==2,row),base.affine)[0]
                display_kind="spillover" if kind=="fp" and row["any_overlap"] else kind
                image,planes=render(ct,pan,les,pred,selected,aff,base.affine,low,high,f"{i} | {display_kind} component {row['component_id']} | {row['voxels']} voxels")
                name=f"{i}-{display_kind}-{row['component_id']:02d}.png";image.save(OUT/name)
                images.append(dict(file=name,sha256=sha(OUT/name),case_id=i,kind=display_kind,component=row,planes=planes))
                print("rendered",name,flush=True)
                del selected,image
                gate()
        cases.append(dict(case_id=i,source_sha256=bindings,source_report_sha256=target["source_report_sha256"],native_shape=list(base.shape),native_affine=base.affine.tolist(),ras_affine=aff.tolist(),orientation_transform=transform.tolist(),reference_units=units,unknown_reference_units_assumed_mm=score["unknown_reference_units_assumed_mm"],region_low=low,region_high=high,coverage=score["localization"]))
        del ct,pan,les,pred,pan0,les0,pred0,ns
    assert len(images)==26 and len(cases)==7
    write(OUT/"manifest.json",dict(schema="prowl.seven-native-error-review.v1",plan_sha256=PLAN_SHA,scope=plan["scope"],cases=cases,images=images,seconds=time.monotonic()-started,model_forwards=0,scoring_calls=0,image_review_performed=False,display=dict(window_hu=[-100,250],zoom_margin_mm=20,selection="maximum component area per axis; lowest index tie",interpolation="nearest display scaling only",orientation="lossless RAS; obliquity rejected")))

if __name__=="__main__":
    if "--worker" in sys.argv:worker()
    else:
        if OUT.exists() or BACK.exists():raise FileExistsError("Already started; no retry")
        gate();OUT.mkdir()
        raw=subprocess.check_output(["git","show","1b81693:docs/capstone/handoffs/WEEK-05-VISUAL-ERROR-REVIEW-20261104.json"])
        assert hashlib.sha256(raw).hexdigest()==PLAN_SHA
        (OUT/"plan.json").write_bytes(raw)
        amended=subprocess.check_output(["git","show","61eb806:docs/capstone/handoffs/WEEK-05-VISUAL-ERROR-REVIEW-AMENDMENT-20261104.json"])
        assert hashlib.sha256(amended).hexdigest()=="1463a206dfbf549804d4877cb82e996549ab0ba56990f6e7d7a946749349d979"
        (OUT/"approved-amendment.json").write_bytes(amended)
        pins=[Path(__file__),ROOT/"src/inference/native_error_review_20261104.py",ROOT/"src/inference/native_review_overlays_20261103.py",ROOT/"src/operations/full_training_platform.py"]
        write(OUT/"request.json",dict(plan_sha256=PLAN_SHA,code_pins={str(p):sha(p) for p in pins},seconds=1200,rss_bytes=12*1024**3,threads=1,output_bytes=2*1024**3))
        env=dict(os.environ,OMP_NUM_THREADS="1",MKL_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",NUMEXPR_NUM_THREADS="1",CUDA_VISIBLE_DEVICES="",PYTHONDONTWRITEBYTECODE="1")
        success=False
        with (OUT/"worker.log").open("x") as log:
            p=subprocess.Popen([sys.executable,__file__,"--worker"],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            try:watch_windows(p,seconds=1200,rss_bytes=12*1024**3,tick=gate);success=True
            finally:
                write(OUT/"resources.json",dict(getattr(p,"duration_resources",{}),success=success,exit_code=p.returncode))
                gate();shutil.copytree(OUT,BACK)
                for f in OUT.rglob("*"):
                    if f.is_file():assert sha(f)==sha(BACK/f.relative_to(OUT))
