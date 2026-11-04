"""Bounded metadata recovery from saved masks/headers; no CT voxel reads/render calls."""
import sys,os,json,time,subprocess,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.qualify_matched_physical_cascade_20261102 import sha,write,tree_bytes
from src.operations.full_training_platform import watch_windows,require_ac
OLD=Path("E:/PROWL/readiness/week05-seven-visual-review-20261104-a01")
OUT=Path("E:/PROWL/readiness/week05-seven-visual-metadata-20261104-a01")
BACK=Path("C:/Users/quinn/PROWL-Backups")/OUT.name
BASE=Path("E:/PROWL/artifacts/week05-autonomous70-20261103-a03")

def gate():
    require_ac()
    assert all(shutil.disk_usage(d).free>=100*1024**3 for d in ["C:/","E:/"])
    assert tree_bytes(OLD)+tree_bytes(OUT)<2*1024**3

def worker():
    import numpy as np
    import nibabel as nib
    from src.inference.native_error_review_20261104 import canonical,plane_choices,plane,crop_bounds,selected_component
    from src.inference.native_error_review_serializable_20261104 import native_json
    start=time.monotonic();r=json.loads((OLD/"recovered-manifest.json").read_text());req=json.loads((BASE/"request.json").read_text());receipt=json.loads((OUT/"request.json").read_text())
    assert sha(OLD/"recovered-manifest.json")==receipt["parent_sha256"]
    for path,h in receipt["code_pins"].items():assert sha(path)==h
    for c in r["cases"]:
        case=next(x for x in req["cases"] if x["case_id"]==c["case_id"])
        paths={"lesion":Path(case["files"]["lesion"]),"prediction":BASE/c["case_id"]/"autonomous/prediction.nii.gz"}
        arrays={}
        original=np.asarray(c["native_affine"]);aff=np.asarray(c["ras_affine"]);spacing=np.linalg.norm(aff[:3,:3],axis=0)
        for k,p in paths.items():
            assert sha(p)==c["source_sha256"][k]
            n=nib.load(p);assert list(n.shape)==c["native_shape"] and np.allclose(n.affine,original,atol=1e-5,rtol=0)
            arrays[k]=np.asarray(n.dataobj,dtype=np.uint8)
        for im in [x for x in r["images"] if x["case_id"]==c["case_id"]]:
            assert sha(OLD/im["file"])==im["sha256"]
            mask=arrays["lesion"]>0 if im["kind"]=="miss" else arrays["prediction"]==2
            selected,new_aff,_=canonical(selected_component(mask,im["component"]),original)
            assert np.allclose(new_aff,aff,atol=1e-5,rtol=0)
            rows=plane_choices(selected,aff)
            for row in rows:
                row["zoom_pixel_box_xy_half_open"]=list(crop_bounds(plane(selected,row),[spacing[row["x_axis"]],spacing[row["y_axis"]]]))
                point=np.array(row["centroid_ras_voxel"]);point[row["axis"]]=row["index"]
                row["original_native_voxel_at_target"]=(np.linalg.inv(original)@aff@np.r_[point,1])[:3].tolist()
            im["planes"]=native_json(rows)
            del selected,mask
        del arrays
        print("recovered planes",c["case_id"],flush=True);gate()
    r["schema"]="prowl.seven-native-error-review.full-metadata.v1"
    r["metadata_recovery"]=dict(parent_sha256=receipt["parent_sha256"],seconds=time.monotonic()-start,ct_voxel_reads=0,mask_geometry_reads_only=True,images_regenerated=False,method="same frozen selection/orientation/crop functions, exact source mask hashes and component checks; additive native scalar serialization",prior_worker_seconds=296.406,first_metadata_recovery_conservative_charge_seconds=30)
    r["limitations"]=[x for x in r["limitations"] if not x.startswith("Complete cases/source hashes")]
    r["limitations"].append("Full-precision plane metadata recovered separately from bound masks; original partial manifest and failed worker unchanged.")
    write(OUT/"full-manifest.json",r)

if __name__=="__main__":
    if "--worker" in sys.argv:worker()
    else:
        if OUT.exists() or BACK.exists():raise FileExistsError("Already started; no retry")
        gate();OUT.mkdir()
        pins=[Path(__file__),ROOT/"src/inference/native_error_review_20261104.py",ROOT/"src/inference/native_review_overlays_20261103.py",ROOT/"src/inference/native_error_review_serializable_20261104.py"]
        write(OUT/"request.json",dict(parent_sha256=sha(OLD/"recovered-manifest.json"),code_pins={str(p):sha(p) for p in pins},seconds=800,rss_bytes=12*1024**3,cumulative_budget_seconds=1200,prior_charge_seconds=326.406,ct_reads=0))
        env=dict(os.environ,OMP_NUM_THREADS="1",MKL_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",NUMEXPR_NUM_THREADS="1",CUDA_VISIBLE_DEVICES="",PYTHONDONTWRITEBYTECODE="1")
        success=False
        with (OUT/"worker.log").open("x") as f:
            p=subprocess.Popen([sys.executable,__file__,"--worker"],cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            try:watch_windows(p,seconds=800,rss_bytes=12*1024**3,tick=gate);success=True
            finally:
                write(OUT/"resources.json",dict(getattr(p,"duration_resources",{}),success=success,exit_code=p.returncode))
                shutil.copytree(OUT,BACK)
                for f in OUT.iterdir():
                    if f.is_file():assert sha(f)==sha(BACK/f.name)
