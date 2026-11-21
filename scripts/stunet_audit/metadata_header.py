"""Decode only the header of the pinned mixed-partition PanTS workbook."""
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

P = Path("/Volumes/PROWL-Data/PROWL/sources/pants/acquisition-3b1cd6110811/metadata.xlsx")
SHA = "4bcbf14a31b1ca9441af051a104702e7a832391f47d3af5f493048ec813283e3"
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def main():
    assert P.stat().st_size == 1334813
    assert hashlib.sha256(P.read_bytes()).hexdigest() == SHA
    with ZipFile(P) as z:
        assert len(z.namelist()) == len(set(z.namelist()))
        assert all(i.file_size <= 32*1024**2 for i in z.infolist())
        with z.open("xl/worksheets/sheet1.xml") as f:
            row = next(e for event,e in ET.iterparse(f, events=("end",)) if e.tag == NS+"row")
            assert row.attrib["r"] == "1"
            cells = list(row)
            assert all(c.tag == NS+"c" and c.get("t") == "s" for c in cells)
            wanted = {int(c.find(NS+"v").text) for c in cells}
        strings = {}
        with z.open("xl/sharedStrings.xml") as f:
            index = 0
            for event,e in ET.iterparse(f, events=("end",)):
                if e.tag != NS+"si":
                    continue
                if index in wanted:
                    strings[index] = "".join(x.text or "" for x in e.iter(NS+"t"))
                if index == max(wanted):
                    break
                index += 1
        assert wanted == set(strings)
        headers = [strings[int(c.find(NS+"v").text)] for c in cells]
    result = dict(path=str(P), sha256=SHA, headers=headers, decoded_header_rows=1,
                  decoded_study_rows=0, source_patient_crosswalk_columns=[h for h in headers
                  if any(k in h.lower() for k in ("patient", "subject", "series", "original", "source", "dataset", "institution"))])
    with Path("docs/stunet_audit/pants_metadata_schema.json").open("x") as f:
        json.dump(result,f,indent=2);f.write("\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
