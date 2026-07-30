"""Recognising when remote data has changed.

A registered element points at data on someone else's server, and nothing tells
us when that data is replaced. Fingerprinting it makes the change visible: record
what a fetch looked like, and compare the next one against it.

The fingerprint has to ignore variation that is not a change to the data. That is
the whole difficulty here, and it is not hypothetical: GeoServer stamps every
entry of a SHAPE-ZIP with the *request* time, so the same untouched layer fetched
twice three seconds apart has different bytes. Hashing those bytes would report a
change on every check, which is the same as reporting nothing.

Kept free of Django so it can be exercised on its own.
"""
import hashlib
import io
import logging
import urllib.request
import zipfile

logger = logging.getLogger("data_fingerprint")

# Members that describe the request rather than the data. wfsrequest.txt holds the
# URL that produced the archive, which is constant for an element -- but it is a
# property of the request, so it stays out of the fingerprint on principle.
_REQUEST_MEMBERS = {"wfsrequest.txt"}


def digest(body):
    """A fingerprint of a response body, ignoring incidental variation.

    A zip is hashed by its members -- names and contents, sorted -- rather than by
    its bytes, so the entry timestamps GeoServer writes do not register as a
    change. Anything else is hashed directly.
    """
    archive = None
    if body[:2] == b"PK":
        try:
            archive = zipfile.ZipFile(io.BytesIO(body))
        except zipfile.BadZipFile:
            archive = None

    if archive is None:
        return hashlib.sha256(body).hexdigest()

    hasher = hashlib.sha256()
    for name in sorted(archive.namelist()):
        if name in _REQUEST_MEMBERS:
            continue
        hasher.update(name.encode("utf-8"))
        try:
            hasher.update(archive.read(name))
        except Exception as exc:  # noqa: BLE001 - an unreadable member is data too
            logger.debug("Could not read %s from archive: %s", name, exc)
            hasher.update(b"\0unreadable")
    return hasher.hexdigest()


def _headers(url, timeout):
    """ETag/Last-Modified/Content-Length, or {} if HEAD is not answered.

    GeoServer generates OWS responses per request and offers none of these; the
    file server offers Last-Modified and Content-Length. So this is an
    optimisation that applies to some sources, never something to rely on.
    """
    try:
        request = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            headers = response.headers
    except Exception as exc:  # noqa: BLE001 - HEAD is optional
        logger.debug("HEAD %s failed: %s", url, exc)
        return {}
    return {"etag": headers.get("ETag") or "",
            "last_modified": headers.get("Last-Modified") or "",
            "size": int(headers["Content-Length"])
            if (headers.get("Content-Length") or "").isdigit() else None}


def fingerprint(url, previous=None, timeout=180, opener=None):
    """What ``url`` looks like now, as {digest, etag, last_modified, size}.

    ``previous`` is the last fingerprint of the same URL, used to skip the
    download: if the server offers a validator and it still matches, the data has
    not changed and the recorded digest is carried forward. ``digest`` is None when
    the fetch failed, which is not the same as "unchanged".
    """
    result = {"digest": None, "etag": "", "last_modified": "", "size": None}
    result.update(_headers(url, timeout))

    if previous:
        validator = result["etag"] or result["last_modified"]
        matched = (validator
                   and result["etag"] == (previous.get("etag") or "")
                   and result["last_modified"] == (previous.get("last_modified") or "")
                   and result["size"] == previous.get("size"))
        if matched and previous.get("digest"):
            result["digest"] = previous["digest"]
            return result

    fetch = opener or _fetch
    try:
        headers, body = fetch(url, timeout)
    except Exception as exc:  # noqa: BLE001 - an unreachable source is reported
        logger.warning("Could not fetch %s: %s", url, str(exc)[:200])
        return result

    result["etag"] = result["etag"] or (headers.get("ETag") or "")
    result["last_modified"] = (result["last_modified"]
                               or (headers.get("Last-Modified") or ""))
    result["size"] = len(body)
    result["digest"] = digest(body)
    return result


def _fetch(url, timeout):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return dict(response.headers), response.read()
