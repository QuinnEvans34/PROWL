"""Read saved records; hash outputs/backups. Never load images or run a model."""
import datetime, hashlib, json, statistics
from pathlib import Path
OUT=Path("E:/PROWL/artifacts/week05-autonomous70-20261103-a03")
PREP=Path("E:/PROWL/readiness/week05-full-baseline-preparation-20261103-a03")
BACK=Path("C:/Users/quinn/PROWL-Backups")/OUT.name
DEST=Path("docs/capstone/operations/WEEK-05-AUTONOMOUS70-CLOSEOUT-20261104.json")
def read(p): return json.loads(p.read_text())
cache={}
def sha(p):
    p=Path(p).resolve()
    if p not in cache:
        h=hashlib.sha256()
        with p.open("rb") as f:
            for b in iter(lambda:f.read(8*1024*1024),b""): h.update(b)
        cache[p]=h.hexdigest()
    return cache[p]
def main():
    assert not DEST.exists(), "Refuse overwrite"
    c=read(OUT/"completion.json"); req=read(OUT/"request.json")
    ids=[x["case_id"] for x in req["cases"]]
    assert ids==c["denominator"] and len(set(ids))==70
    assert len(c["cases"])==63 and len(c["failed"])==7
    assert set(c["cases"]).isdisjoint(c["failed"]) and set(ids)==set(c["cases"]+c["failed"])
    journal=[json.loads(x) for x in (OUT/"progress.jsonl").read_text().splitlines()]
    assert [x["case_id"] for x in journal]==ids
    files=sorted(x for x in OUT.rglob("*") if x.is_file())
    for n,f in enumerate(files):
        b=BACK/f.relative_to(OUT)
        assert b.stat().st_size==f.stat().st_size and sha(f)==sha(b), str(f)
        if n%100==0: print("backup verified",n,"/",len(files),flush=True)
    assert {str(x.relative_to(OUT)) for x in files}=={str(x.relative_to(BACK)) for x in BACK.rglob("*") if x.is_file()}
    repo=Path.cwd().resolve(); pins=0
    for name,digest in req["pins"].items():
        p=Path(name).resolve()
        if p.is_relative_to(repo):
            assert sha(p)==digest,str(p);pins+=1
    rows=[]
    for i in ids:
        root=OUT/i/"autonomous"
        if i in c["failed"]:
            f=read(root/"failure.json")
            assert f["dice"] is None and not f["excluded"] and f["optimizer_updates"]==f["model_forwards"]==0
            rows.append({"case_id":i,"disposition":f["status"],"excluded":False,"metrics":None,"dice":None,"source_report_sha256":{"failure":sha(root/"failure.json")},"reason":f["detail"].get("reason",f["status"]),"optimizer_updates":0,"model_forwards":0})
            continue
        s=read(root/"score.json"); r=read(root/"result.json"); a=read(root/"input-access.json")
        assert s["case_id"]==r["case_id"]==i and s["optimizer_updates"]==r["optimizer_updates"]==0
        assert not a["pancreas_reference_loaded"] and not a["lesion_reference_loaded"]
        for name,digest in r["artifacts"].items(): assert sha(root/name)==digest
        assert s["file_sha256"]["prediction"]==sha(root/"prediction.nii.gz")
        reused=(root/"reuse.json").exists()
        if reused:
            re=read(root/"reuse.json");assert re["original_result_sha256"]==sha(root/"result.json") and re["baseline_request_sha256"]==sha(OUT/"request.json")
        else: assert r["request_sha256"]==sha(OUT/"request.json")
        row={"case_id":i,"disposition":"COMPLETED","excluded":False,"reused":reused,"source_report_sha256":{k:sha(root/(k+".json")) for k in ["score","result","input-access"]}}
        for k in ["metrics","lesion_reference_state","empty_reference_policy","reference_units","unknown_reference_units_assumed_mm","role","model_quality_acceptance","lesion_components","lesion_contour","pancreas_contour","localization","measurements"]: row[k]=s[k]
        if s["metrics"]["lesion"]["reference_voxels"]==0: assert s["metrics"]["lesion"]["dice"] is None
        rows.append(row)
    resources=[read(p) for p in OUT.glob("*.resources.json")]
    assert len(resources)==121
    assert all(r["success"] and r["exit_code"]==0 and r["workers_reaped"] for r in resources)
    hr=read(PREP/"handoff-evaluate.resources.json")
    assert hr["success"] and hr["exit_code"]==0 and hr["workers_reaped"]
    prep_back=BACK.parent/PREP.name
    prep_pairs=0
    for f in PREP.rglob("*"):
        if f.is_file() and not f.name.startswith("handoff-console"):
            assert sha(f)==sha(prep_back/f.relative_to(PREP)),str(f);prep_pairs+=1
    ok=[x for x in rows if x["disposition"]=="COMPLETED"]
    pos=[x for x in ok if x["metrics"]["lesion"]["reference_voxels"]>0]; neg=[x for x in ok if x not in pos]
    aggregate={"requested":70,"completed":63,"failed":7,"excluded":0,"reused":sum(x["reused"] for x in ok),"new_predictions":58,"positive_reference_n":len(pos),"empty_reference_n":len(neg),"positive_macro_lesion_dice":statistics.mean(x["metrics"]["lesion"]["dice"] for x in pos),"positive_any_overlap_n":sum(x["metrics"]["lesion"]["true_positive"]>0 for x in pos),"empty_reference_alarm_n":sum(x["metrics"]["lesion"]["predicted_voxels"]>0 for x in neg),"reference_components_n":sum(x["lesion_components"]["reference_count"] for x in ok),"reference_components_hit_n":sum(x["lesion_components"]["reference_hit_count"] for x in ok),"false_positive_components_n":sum(x["lesion_components"]["false_positive_components"] for x in ok)}
    report={"schema":"prowl.autonomous70.saved-closeout.v1","created_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"identities":{k+"_sha256":sha(OUT/(k+".json")) for k in ["request","ready","completion"]},"scope":{"role":"exposed_development","probability_equivalence":"UNQUALIFIED","numerical_exception":"Human-approved scoped exception; original probability comparison failure retained","training":False,"model_quality_acceptance":False,"hypothesis_verdict":"NOT_TESTED","failed_cases_not_imputed":True},"ordered_cases":rows,"aggregate":aggregate,"verification":{"output_backup_pairs":len(files),"output_bytes":sum(f.stat().st_size for f in files),"preparation_backup_pairs":prep_pairs,"repository_pins_matched":pins,"source_data_pins":"Inherited source-admission evidence; no source CT/mask reread for this report","successful_reaped_worker_resources":len(resources),"evaluation_supervisor":hr,"saved_completion_seconds":c["seconds"],"handoff_sha256":sha(PREP/"handoff.jsonl")}}
    DEST.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(aggregate,indent=2));print("REPORT",sha(DEST),flush=True)
if __name__=="__main__": main()
