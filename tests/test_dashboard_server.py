"""The dashboard's server: it serves the page and the bundle, on this machine, and nothing else."""

import json
import threading
import urllib.error
import urllib.request

import pytest

from chhaya.dashboard.__main__ import DEMO, export, make_server, pick_bundle


@pytest.fixture(scope="module")
def base():
    server = make_server(DEMO)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def _get(url: str):
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.status, r.headers.get("Content-Type"), r.read()


def test_it_serves_the_page_the_bundle_and_a_font(base):
    status, kind, body = _get(base + "/")
    assert status == 200 and "text/html" in kind and b"Chhaya" in body
    status, kind, body = _get(base + "/data/index.json")
    assert status == 200 and json.loads(body)["bundle"] == "demo"
    assert _get(base + "/app.js")[0] == 200 and _get(base + "/data/patients/mrs-r.json")[0] == 200


@pytest.mark.parametrize(
    "path", ["/data/../__main__.py", "/data/%2e%2e/__main__.py", "/../build.py", "/data/nope.json"]
)
def test_nothing_outside_the_page_and_the_bundle_is_served(base, path):
    with pytest.raises(urllib.error.HTTPError) as err:
        _get(base + path)
    assert err.value.code == 404


def test_it_listens_on_this_machine_only():
    server = make_server(DEMO)
    assert server.server_address[0] == "127.0.0.1"
    server.server_close()


def test_a_missing_bundle_names_the_command_that_builds_one(tmp_path):
    with pytest.raises(SystemExit, match="chhaya.build"):
        pick_bundle(tmp_path)


def test_the_export_is_the_page_with_the_demo_bundle_only(tmp_path):
    out = tmp_path / "site"
    export(out)
    index = json.loads((out / "data" / "index.json").read_text(encoding="utf-8"))
    assert (out / "index.html").exists() and [p["id"] for p in index["patients"]] == ["mrs-r"]
    with pytest.raises(SystemExit, match="exists"):
        export(out)
