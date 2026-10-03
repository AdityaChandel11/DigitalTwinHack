"""Fetch the open datasets. Nothing here is ever committed or redistributed.

Usage: python -m chhaya.data.download shanghai cgmacros
"""

from __future__ import annotations

import hashlib
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

from chhaya.config import RAW_DIR

SOURCES = {
    "shanghai": {
        "url": "https://ndownloader.figshare.com/files/42966622",
        "file": "diabetes_datasets.zip",
        "algo": "md5",
        "digest": "4bfb61cfa506b48155fd9e841ee48e21",
        "license": "CC BY 4.0 (Zhao et al., Sci Data 2023, doi:10.6084/m9.figshare.c.6310860)",
    },
    "cgmacros": {
        # PhysioNet S3 mirror of the same file: the checksum below still verifies it, and it is far faster.
        "url": "https://physionet-open.s3.amazonaws.com/cgmacros/1.0.0/CGMacros_dateshifted365.zip",
        "file": "CGMacros_dateshifted365.zip",
        "algo": "sha256",
        "digest": "05c8b0e6f1a2757050aced55ce4bf6ab2ac9b30f2fd8ca193056812d9c621d4d",
        "license": "CC BY-NC-SA 4.0 (Das et al., PhysioNet, doi:10.13026/3z8q-x658)",
    },
}


def file_digest(path: Path, algo: str) -> str:
    h = hashlib.new(algo)
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(path: Path, algo: str, digest: str) -> None:
    got = file_digest(path, algo)
    if got != digest:
        raise ValueError(
            f"{path.name}: {algo} {got} does not match the published {digest}; delete it and retry"
        )


CHUNK = 16 * 1024 * 1024
WORKERS = 8


def ranges(total: int, chunk: int = CHUNK) -> list[tuple[int, int]]:
    """Inclusive (start, end) byte ranges that tile [0, total)."""
    return [(a, min(a + chunk, total) - 1) for a in range(0, total, chunk)]


def _get_range(url: str, dest: Path, start: int, end: int, tries: int = 4) -> None:
    for attempt in range(tries):
        try:
            with requests.get(
                url, headers={"Range": f"bytes={start}-{end}"}, stream=True, timeout=60
            ) as resp:
                resp.raise_for_status()
                if resp.status_code != 206:
                    raise OSError(f"server ignored the range request (HTTP {resp.status_code})")
                with dest.open("r+b") as fh:
                    fh.seek(start)
                    for block in resp.iter_content(1 << 16):
                        fh.write(block)
            return
        except (requests.RequestException, OSError):
            if attempt == tries - 1:
                raise


def download_parallel(url: str, dest: Path, workers: int = WORKERS) -> None:
    """Fetch url into dest with several ranged requests at once; one stream is often throttled."""
    head = requests.get(url, headers={"Range": "bytes=0-0"}, timeout=60)
    head.raise_for_status()
    if head.status_code != 206:
        raise OSError(f"{url} does not support range requests")
    total = int(head.headers["Content-Range"].rsplit("/", 1)[1])
    with dest.open("wb") as fh:
        fh.truncate(total)
    done = 0
    with ThreadPoolExecutor(workers) as pool:
        futures = [pool.submit(_get_range, url, dest, a, b) for a, b in ranges(total)]
        for fut in futures:
            fut.result()
            done += 1
            print(f"  {done}/{len(futures)} chunks", flush=True)


def fetch(name: str, raw_dir: Path = RAW_DIR) -> Path:
    """Download, check the published checksum, and unpack into raw_dir/name. Safe to re-run."""
    src = SOURCES[name]
    dest = raw_dir / name
    dest.mkdir(parents=True, exist_ok=True)
    archive = dest / src["file"]
    if not archive.exists():
        print(f"downloading {name} ({src['license']})")
        tmp = archive.with_suffix(".part")
        download_parallel(src["url"], tmp)
        tmp.replace(archive)
    verify(archive, src["algo"], src["digest"])
    if not (dest / ".unpacked").exists():
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(dest)
        for inner in dest.rglob("*.zip"):
            if inner != archive:
                with zipfile.ZipFile(inner) as zf:
                    zf.extractall(inner.parent)
        (dest / ".unpacked").touch()
    return dest


if __name__ == "__main__":
    for arg in sys.argv[1:] or list(SOURCES):
        print(fetch(arg))
