import pytest

from chhaya.data.download import SOURCES, ranges, verify


def test_checksum_mismatch_is_an_error(tmp_path):
    f = tmp_path / "x.zip"
    f.write_bytes(b"abc")
    verify(f, "md5", "900150983cd24fb0d6963f7d28e17f72")
    with pytest.raises(ValueError, match="does not match"):
        verify(f, "md5", "0" * 32)


def test_every_source_states_its_licence_and_checksum():
    for src in SOURCES.values():
        assert src["license"] and len(src["digest"]) in (32, 64) and src["url"].startswith("https://")


def test_ranges_tile_the_file_exactly():
    r = ranges(100, chunk=40)
    assert r == [(0, 39), (40, 79), (80, 99)]
    assert sum(b - a + 1 for a, b in r) == 100
    assert ranges(40, chunk=40) == [(0, 39)]
