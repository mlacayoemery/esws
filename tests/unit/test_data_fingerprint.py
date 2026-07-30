"""Unit tests for remote-data fingerprinting (tools/data_fingerprint.py).

Stack-free: the fetch is injected, so the rules that matter -- what counts as a
change and what does not -- are checked directly.
"""
import io
import os
import sys
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "tools"))

import data_fingerprint  # noqa: E402


def shape_zip(members, timestamp=(2026, 1, 1, 0, 0, 0)):
    """A SHAPE-ZIP as GeoServer builds one: every entry stamped with the time."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in members.items():
            info = zipfile.ZipInfo(name, date_time=timestamp)
            archive.writestr(info, content)
    return buffer.getvalue()


def test_identical_bytes_have_the_same_digest():
    assert data_fingerprint.digest(b"abc") == data_fingerprint.digest(b"abc")
    assert data_fingerprint.digest(b"abc") != data_fingerprint.digest(b"abd")


def test_a_zips_entry_timestamps_are_not_a_change():
    """The reason this module exists: GeoServer stamps every SHAPE-ZIP entry with
    the request time, so the same untouched layer has different bytes each
    fetch."""
    members = {"w.shp": b"geometry", "w.dbf": b"attributes", "w.prj": b"crs"}
    early = shape_zip(members, (2026, 1, 1, 0, 0, 0))
    later = shape_zip(members, (2026, 7, 30, 9, 41, 44))

    assert early != later, "the fixture is not reproducing the timestamp problem"
    assert data_fingerprint.digest(early) == data_fingerprint.digest(later)


def test_changed_zip_content_is_a_change():
    before = shape_zip({"w.shp": b"geometry", "w.dbf": b"attributes"})
    after = shape_zip({"w.shp": b"different geometry", "w.dbf": b"attributes"})
    assert data_fingerprint.digest(before) != data_fingerprint.digest(after)


def test_an_added_or_removed_member_is_a_change():
    two = shape_zip({"w.shp": b"g", "w.dbf": b"a"})
    three = shape_zip({"w.shp": b"g", "w.dbf": b"a", "w.prj": b"crs"})
    assert data_fingerprint.digest(two) != data_fingerprint.digest(three)


def test_the_request_member_is_not_part_of_the_fingerprint():
    """wfsrequest.txt describes the request, not the data."""
    data = {"w.shp": b"g"}
    with_request = shape_zip({**data, "wfsrequest.txt": b"http://host/ows?typeName=x"})
    assert data_fingerprint.digest(shape_zip(data)) == data_fingerprint.digest(
        with_request)


def test_a_zip_and_its_members_are_distinguishable_from_raw_bytes():
    """A body that merely starts with PK but is not a zip still fingerprints."""
    assert data_fingerprint.digest(b"PKnot-a-zip") is not None


def stub_fetch(body, headers=None, calls=None):
    def fetch(url, timeout):
        if calls is not None:
            calls.append(url)
        return dict(headers or {}), body
    return fetch


def test_fingerprint_records_the_digest_and_size():
    result = data_fingerprint.fingerprint("http://host/x.csv",
                                          opener=stub_fetch(b"a,b\n1,2\n"))
    assert result["digest"] == data_fingerprint.digest(b"a,b\n1,2\n")
    assert result["size"] == 8


def test_a_failed_fetch_reports_no_digest_rather_than_unchanged():
    def explode(url, timeout):
        raise OSError("connection refused")

    result = data_fingerprint.fingerprint("http://host/gone.csv", opener=explode)
    assert result["digest"] is None


def with_head(headers):
    """Replace the HEAD probe, which would otherwise need a server."""
    original = data_fingerprint._headers
    data_fingerprint._headers = lambda url, timeout: dict(headers)
    return original


def test_a_matching_validator_skips_the_download():
    """A source that offers Last-Modified need not be downloaded again -- which
    matters, since fingerprinting a raster otherwise means pulling megabytes."""
    calls = []
    previous = {"digest": "recorded-earlier", "etag": "",
                "last_modified": "Thu, 11 Jun 2026 19:03:18 GMT", "size": 535}
    original = with_head({"etag": "", "last_modified": previous["last_modified"],
                          "size": 535})
    try:
        result = data_fingerprint.fingerprint(
            "http://host/x.csv", previous=previous,
            opener=stub_fetch(b"x" * 535, calls=calls))
    finally:
        data_fingerprint._headers = original

    assert not calls, "the body was downloaded despite a matching validator"
    assert result["digest"] == "recorded-earlier"


def test_a_changed_validator_forces_the_download():
    calls = []
    previous = {"digest": "recorded-earlier", "etag": "",
                "last_modified": "Thu, 11 Jun 2026 19:03:18 GMT", "size": 535}
    original = with_head({"etag": "", "last_modified": "Fri, 12 Jun 2026 08:00:00 GMT",
                          "size": 540})
    try:
        result = data_fingerprint.fingerprint(
            "http://host/x.csv", previous=previous,
            opener=stub_fetch(b"y" * 540, calls=calls))
    finally:
        data_fingerprint._headers = original

    assert calls, "a changed validator must trigger a fetch"
    assert result["digest"] == data_fingerprint.digest(b"y" * 540)
