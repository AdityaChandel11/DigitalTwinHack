from test_shanghai import root  # noqa: F401  (fixture: a small Shanghai tree)

from chhaya.data.files import find, is_junk
from chhaya.data.shanghai import load_all


def test_macos_archive_debris_is_junk(tmp_path):
    assert is_junk(tmp_path / "__MACOSX" / "Shanghai_T2DM" / "a.xlsx")
    assert is_junk(tmp_path / "x" / "._a.xlsx")
    assert is_junk(tmp_path / ".DS_Store")
    assert not is_junk(tmp_path / "Shanghai_T2DM" / "a.xlsx")


def test_find_skips_junk_and_is_sorted(tmp_path):
    (tmp_path / "b.csv").write_text("x")
    (tmp_path / "a.csv").write_text("x")
    (tmp_path / "__MACOSX").mkdir()
    (tmp_path / "__MACOSX" / "a.csv").write_text("junk")
    (tmp_path / "._b.csv").write_text("junk")
    assert [p.name for p in find(tmp_path, "*.csv")] == ["a.csv", "b.csv"]


def test_shanghai_loader_ignores_a_macos_decoy_folder_that_sorts_first(root):  # noqa: F811
    decoy = root / "__MACOSX" / "Shanghai_T2DM"
    decoy.mkdir(parents=True)
    (decoy / "._2001_0_20210701.xlsx").write_bytes(b"\x00\x05\x16\x07 AppleDouble junk")
    (root / "__MACOSX" / "._Shanghai_T2DM_Summary.xlsx").write_bytes(b"\x00\x05\x16\x07")
    assert [r.rec_id for r in load_all(root)] == ["shanghai-2001_0_20210701"]
