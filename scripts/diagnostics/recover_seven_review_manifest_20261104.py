"""Metadata-only closeout of the preserved final-manifest serialization failure."""
import json,hashlib,datetime,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path("E:/PROWL/readiness/week05-seven-visual-review-20261104-a01")
BACK=Path("C:/Users/quinn/PROWL-Backups")/OUT.name

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def complete_field(raw,key):
    prefix='"'+key+'":'
    start=raw.index(prefix)+len(prefix)
    return json.JSONDecoder().raw_decode(raw[start:].lstrip())[0]
def recover():
    target=OUT/"recovered-manifest.json"
    if target.exists():raise FileExistsError("Recovery already completed")
    resources=json.loads((OUT/"resources.json").read_text())
    assert not resources["success"] and resources["exit_code"]==1 and resources["workers_reaped"]
    assert resources["seconds"]<1200 and resources["peak_owned_rss_bytes"]<12*1024**3
    assert "TypeError: Object of type int64 is not JSON serializable" in (OUT/"worker.log").read_text()
    # Verify all original output/failed manifest backups before reading salvaged metadata.
    original=[p for p in OUT.iterdir() if p.is_file() and p.name!="observations.json"]
    for p in original:assert sha(p)==sha(BACK/p.name),p.name
    raw=(OUT/"manifest.json").read_text();cases=complete_field(raw,"cases")
    plan=json.loads((OUT/"plan.json").read_text());amend=json.loads((OUT/"approved-amendment.json").read_text());obs=json.loads((OUT/"observations.json").read_text())
    assert [x["case_id"] for x in cases]==[x["case_id"] for x in plan["cases"]]
    expected={}
    for c in plan["cases"]:
        fp=c["top_false_positive_components"]
        if c["case_id"]==amend["case_id"]:fp=fp[:2]+[amend["component"]]
        for kind,components in [("miss",c["missed_reference_components"]),("fp",fp)]:
            for row in components:
                k="spillover" if kind=="fp" and row["any_overlap"] else kind
                name=f"{c['case_id']}-{k}-{row['component_id']:02d}.png"
                expected[name]=dict(case_id=c["case_id"],kind=k,component=row)
    assert len(expected)==26 and set(expected)==set(obs)=={p.name for p in OUT.glob("*.png")}
    logged=[line.split("rendered ",1)[1] for line in (OUT/"worker.log").read_text().splitlines() if line.startswith("rendered ")]
    assert len(logged)==26 and set(logged)==set(expected)
    req=json.loads((OUT/"request.json").read_text())
    for path,h in req["code_pins"].items():assert sha(Path(path))==h
    images=[dict(file=n,sha256=sha(OUT/n),bytes=(OUT/n).stat().st_size,**v,actually_opened_with_image_tool=True,observation=obs[n]) for n,v in expected.items()]
    report=dict(schema="prowl.seven-native-error-review.recovered.v1",created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status="VISUAL_REVIEW_COMPLETED_FROM_SAVED_PNGS_WITH_PRESERVED_RENDER_MANIFEST_FAILURE",plan_sha256=sha(OUT/"plan.json"),amendment_sha256=sha(OUT/"approved-amendment.json"),scope=plan["scope"],cases=cases,images=images,render_resources=resources,original_backup_pairs_verified=len(original),all_code_pins_match=True,render_retried=False,images_regenerated=False,source_arrays_reread_for_recovery=False,model_forwards=0,scoring_calls=0,limitations=["Original renderer exited1 only during JSON serialization after26images; original failure/partial manifest preserved.","Complete cases/source hashes/native geometry recovered from fully serialized cases field. Per-image full-precision plane records were not completed; actual zero-based indices, native target coordinates and RASmm are displayed in each PNG caption.","Two2235first-slice tiny FP targets are visible axially; orange ROI border obscures their orthogonal overlay pixels. No rerender performed.","Reference unit assumptions preserved; no annotation or clinical adjudication; representative views only.","6755 and2889 show striking visual similarity; shared identity not established, no duplicate audit or exclusion."],display=dict(window_hu=[-100,250],zoom_margin_mm=20,orientation="axis-aligned lossless RAS; obliquity rejected",rows=["context overlay","zoom CT only","zoom overlay"]),evidence_sha256={n:sha(OUT/n) for n in ["request.json","manifest.json","resources.json","worker.log","selection-amendment.json","observations.json"]})
    target.write_bytes((json.dumps(report,indent=2,allow_nan=False)+"\n").encode())
    for p in [OUT/"observations.json",target]:
        dest=BACK/p.name
        if dest.exists():raise FileExistsError(dest)
        shutil.copyfile(p,dest);assert sha(p)==sha(dest)
    pub=ROOT/"docs/capstone/operations/WEEK-05-SEVEN-VISUAL-REVIEW-20261104.json"
    if pub.exists():raise FileExistsError(pub)
    pub.write_bytes(target.read_bytes())
    print("report",sha(pub),"images",len(images),"image_bytes",sum(x["bytes"] for x in images),"original_backup_pairs",len(original))
if __name__=="__main__":recover()
