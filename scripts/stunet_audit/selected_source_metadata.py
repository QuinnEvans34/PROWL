"""Read source-site fields for exactly the 1,408 admitted train/dev aliases.

Never decodes sex, age, tumor flags, structured reports or non-allowlisted study fields.
"""
import csv
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
COHORT_SHA = "0e63126be7df03072b0064e9740c9fe6ca7efec766f2324e79a49ddde278d8e2"
METADATA_SHA = "4bcbf14a31b1ca9441af051a104702e7a832391f47d3af5f493048ec813283e3"


def strings(z, wanted=None, aliases=None):
    found = {}
    with z.open("xl/sharedStrings.xml") as f:
        index = 0
        for event,e in ET.iterparse(f, events=("end",)):
            if e.tag != NS+"si":
                continue
            if aliases is not None:
                # Only plain, exact permitted IDs are materialized as identity records.
                t = e.find(NS+"t")
                if t is not None and t.text in aliases:
                    found[index] = t.text
            elif index in wanted:
                found[index] = "".join(t.text or "" for t in e.iter(NS+"t"))
            e.clear()
            index += 1
    return found


def main():
    cohort = Path("outputs/prowl/portable-cohort-20261012/cohort.json")
    assert hashlib.sha256(cohort.read_bytes()).hexdigest() == COHORT_SHA
    members = json.loads(cohort.read_bytes())["members"]
    allowed = {m["case_id"]:m for m in members}
    assert len(allowed) == 1408 and {m["role"] for m in members} == {"train","validation"}
    path = Path("/Volumes/PROWL-Data/PROWL/sources/pants/acquisition-3b1cd6110811/metadata.xlsx")
    assert hashlib.sha256(path.read_bytes()).hexdigest() == METADATA_SHA
    # Header is already pinned/decoded separately. A=ID, J=site,K=detail,L=nationality,M=year.
    columns = {"J":"site", "K":"site_detail", "L":"site_nationality", "M":"study_year"}
    retained = []
    refs = set()
    with ZipFile(path) as z:
        assert all(i.file_size<=32*1024**2 for i in z.infolist())
        id_indexes = strings(z, aliases=set(allowed))
        assert set(id_indexes.values()) == set(allowed)
        with z.open("xl/worksheets/sheet1.xml") as f:
            for event,row in ET.iterparse(f, events=("end",)):
                if row.tag != NS+"row":
                    continue
                if row.get("r") == "1":
                    row.clear(); continue
                id_cell = next((c for c in row if c.get("r", "").startswith("A") and
                                c.get("r", "")[1:].isdigit()), None)
                if id_cell is None or id_cell.get("t") != "s":
                    row.clear(); continue
                ident = id_indexes.get(int(id_cell.find(NS+"v").text))
                if ident is None:
                    row.clear(); continue
                values = {"case_id":ident, "role":allowed[ident]["role"], "workbook_row":row.get("r")}
                for cell in row:
                    col = "".join(c for c in cell.get("r", "") if c.isalpha())
                    if col not in columns:
                        continue
                    assert cell.find(NS+"f") is None
                    v = cell.find(NS+"v")
                    if v is None:
                        continue
                    if cell.get("t") == "s":
                        refs.add(int(v.text)); values[columns[col]] = {"string_index":int(v.text)}
                    else:
                        assert cell.get("t", "n") in ("n","str")
                        values[columns[col]] = v.text
                retained.append(values)
                row.clear()
        mapping = strings(z, wanted=refs)
        for values in retained:
            for col in columns.values():
                v = values.get(col)
                values[col] = mapping[v["string_index"]] if isinstance(v,dict) else v
    assert len(retained) == len({r["case_id"] for r in retained}) == 1408
    p = Path("docs/stunet_audit/source_provenance.csv")
    with p.open("x") as f:
        w=csv.DictWriter(f,fieldnames=["case_id","role","workbook_row",*columns.values()]);w.writeheader()
        w.writerows(sorted(retained,key=lambda r:r["case_id"]))
    summary = dict(cohort_sha256=COHORT_SHA, metadata_sha256=METADATA_SHA,
                   matched_permitted_rows=len(retained), study_fields=list(columns.values()),
                   nonallowlisted_study_fields_decoded=0, clinical_or_tumor_fields_decoded=0,
                   source_values={k:sorted({str(r[k]) for r in retained}) for k in ("site","site_detail","site_nationality")})
    with Path("docs/stunet_audit/selected_source_metadata.json").open("x") as f:
        json.dump(summary,f,indent=2);f.write("\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
