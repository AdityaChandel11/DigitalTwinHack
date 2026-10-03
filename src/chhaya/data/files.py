"""Locate dataset files, ignoring the macOS archive debris that ships inside some zips."""

from __future__ import annotations

from pathlib import Path


def is_junk(path: Path) -> bool:
    """True for __MACOSX resource forks, AppleDouble `._*` files and .DS_Store."""
    return "__MACOSX" in path.parts or path.name.startswith("._") or path.name == ".DS_Store"


def find(root: Path, pattern: str) -> list[Path]:
    """Sorted recursive match under root, with junk removed."""
    return sorted(p for p in root.rglob(pattern) if not is_junk(p))
