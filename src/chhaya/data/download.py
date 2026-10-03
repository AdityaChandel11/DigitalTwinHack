"""Fetch the open datasets. Nothing here is ever committed or redistributed.

Usage: python -m chhaya.data.download shanghai cgmacros
"""
from __future__ import annotations

import hashlib
import sys
import zipfile
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
        "url": "https://physionet.org/files/cgmacros/1.0.0/CGMacros_dateshifted365.zip",
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
        raise ValueError(f"{path.name}: {algo} {got} does not match the published {digest}; delete it and retry")


def fetch(name: str, raw_dir: Path = RAW_DIR) -> Path:
    """Download, check the published checksum, and unpack into raw_dir/name. Safe to re-run."""
    src = SOURCES[name]
    dest = raw_dir / name
    dest.mkdir(parents=True, exist_ok=True)
    archive = dest / src["file"]
    if not archive.exists():
        print(f"downloading {name} ({src['license']})")
        with requests.get(src["url"], stream=True, timeout=60) as resp:
            resp.raise_for_status()
            tmp = archive.with_suffix(".part")
            with tmp.open("wb") as fh:
                for chunk in resp.iter_content(1 << 20):
                    fh.write(chunk)
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
