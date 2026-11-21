"""Bounded acquisition from the exact author-linked STU-Net-B Google Drive file."""
import hashlib
import json
from pathlib import Path
import shutil
import time
import urllib.request

URL = "https://drive.usercontent.google.com/download?id=1BHCp1Ort-OaVFwaZmvsG4qHiKiPeNb4h&export=download&confirm=t"
DESTINATION = Path("/Volumes/PROWL-Data/PROWL/teachers/stunet-b-base-20261106")
MAX_BYTES = 1024**3


def main():
    start = time.monotonic()
    if shutil.disk_usage(DESTINATION).free < 100 * 1024**3:
        raise RuntimeError("External free-space floor failed")
    request = urllib.request.Request(URL, headers={"User-Agent": "PROWL provenance audit"})
    with urllib.request.urlopen(request, timeout=25) as response:
        size = int(response.headers.get("Content-Length", "0"))
        if not 0 < size <= MAX_BYTES:
            raise RuntimeError("Missing or excessive checkpoint length")
        if "base_ep4k.model" not in response.headers.get("Content-Disposition", ""):
            raise RuntimeError("Unexpected author-linked filename")
        if "application/octet-stream" not in response.headers.get("Content-Type", ""):
            raise RuntimeError("Not a checkpoint download")
        h = hashlib.sha256()
        count = 0
        partial = DESTINATION / "base_ep4k.model.partial"
        with partial.open("xb") as stream:
            while block := response.read(1024**2):
                count += len(block)
                if count > size or count > MAX_BYTES or time.monotonic() - start > 600:
                    raise RuntimeError("Download bound exceeded; partial preserved")
                stream.write(block)
                h.update(block)
        if count != size:
            raise RuntimeError("Incomplete download; partial preserved")
    target = DESTINATION / "base_ep4k.model"
    if target.exists():
        raise FileExistsError(target)
    partial.rename(target)
    receipt = dict(source_url=URL, author_repository="https://github.com/uni-medical/STU-Net",
                   author_source_revision="0652eaf5cafda6bc269942238c3695994f2dc4f0",
                   filename=target.name, path=str(target), bytes=count, sha256=h.hexdigest(),
                   elapsed_seconds=time.monotonic() - start, publisher_checksum=None,
                   checksum_assurance="Local SHA256 and author-linked HTTPS origin; no publisher checksum found",
                   automatic_retry=False)
    with (DESTINATION / "download.json").open("x") as stream:
        json.dump(receipt, stream, indent=2)
        stream.write("\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
