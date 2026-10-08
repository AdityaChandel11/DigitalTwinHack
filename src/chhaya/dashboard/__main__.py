"""Serve the dashboard on this machine: python -m chhaya.dashboard [--bundle DIR] [--port N] [--no-open]

A static page and a folder of JSON, on the loopback address only. Nothing is fitted and nothing leaves the
machine. The local bundle (`artifacts/`, with held-out patients) is used when it exists; otherwise the demo
bundle that ships with the code (the synthetic patient and the Evidence data).

`--export DIR` writes the page and the demo bundle into one folder of plain files, for a static host. Only the
demo bundle is ever exported: per-reading data of real patients is not published (rule 6).
"""

from __future__ import annotations

import argparse
import shutil
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

STATIC = Path(__file__).parent / "static"
DEMO = Path(__file__).parent / "demo"
LOCAL = Path(__file__).resolve().parents[3] / "artifacts"


class Handler(SimpleHTTPRequestHandler):
    """`/data/...` comes from the bundle, everything else from the static folder; nothing outside either."""

    def __init__(self, *args, bundle: Path, **kwargs):
        self.bundle = bundle
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def translate_path(self, path: str) -> str:
        clean = path.split("?", 1)[0].split("#", 1)[0]
        if clean.startswith("/data/"):
            root, rest = self.bundle, clean[len("/data/") :]
        else:
            root, rest = STATIC, clean.lstrip("/")
        target = (root / rest).resolve()
        if root.resolve() not in (target, *target.parents):
            return str(root / "__outside__")  # does not exist: a 404
        return str(target)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args) -> None:  # quiet: the terminal shows the address and nothing else
        pass


def pick_bundle(bundle: Path | None) -> Path:
    chosen = bundle or (LOCAL if (LOCAL / "index.json").exists() else DEMO)
    if not (chosen / "index.json").exists():
        raise SystemExit(f"no bundle at {chosen}: build one with `python -m chhaya.build`")
    return chosen


def make_server(bundle: Path, port: int = 0) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, bundle=bundle))


def export(out: Path) -> None:
    """The page and the demo bundle as plain files in one folder."""
    if out.exists():
        raise SystemExit(f"{out} exists: choose a new folder")
    shutil.copytree(STATIC, out)
    shutil.copytree(DEMO, out / "data")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", type=Path, default=None)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-open", action="store_true")
    ap.add_argument(
        "--export", type=Path, default=None, help="write the page and the demo bundle to a folder"
    )
    args = ap.parse_args()
    if args.export:
        export(args.export)
        print(f"static site written to {args.export} (demo bundle only)")
        return
    bundle = pick_bundle(args.bundle)
    server = make_server(bundle, args.port)
    url = f"http://127.0.0.1:{server.server_address[1]}"
    print(f"Chhaya dashboard at {url}  (bundle: {bundle})  Ctrl+C to stop")
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
