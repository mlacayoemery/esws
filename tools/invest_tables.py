"""Bringing along the data an InVEST table points at.

An InVEST table routinely names other files: a threats table lists a raster per
threat, a snapshot table a raster per year, a wave table a vector per point set.
Those names are paths relative to the table's own directory.

When a job supplies such a table as an OWS/HTTP URL, the wrapper downloads the
table alone, into a temporary file. Its references then resolve against that
temporary directory and the model stops with

    Error in column "cur_path", value "/tmp/crops_c.tif": File not found

MODEL_SPEC says which columns hold paths, so this module fetches what those
columns name -- relative to the URL the table itself came from -- and rewrites the
table to point at the local copies.

Some tables carry references the spec cannot describe: habitat risk assessment's
criteria table holds either a number or a raster in the same cell, depending on
the criterion. Cells that name a spatial file are therefore tried too, in any
column; a value that is not a reference simply fails to fetch and is left alone.

Kept free of pywps and natcap.invest so it can be exercised on its own; column
specs are inspected through their ``type`` string rather than their class.
"""
import csv
import hashlib
import logging
import os
import urllib.parse
import urllib.request

logger = logging.getLogger("invest_tables")

# Column types whose values name a file. "csv" is here too: a table may point at
# further tables, which may themselves point at data (crop production does).
PATH_COLUMN_TYPES = {"raster", "vector", "raster_or_vector", "file", "csv"}

# Formats that are several files with a shared stem. Fetching only the .shp gives
# GDAL a shapefile it cannot open, which reads as a missing file rather than an
# incomplete one, so the companions are fetched too -- best effort, since which
# ones exist varies.
_SIDECARS = {
    ".shp": (".shx", ".dbf", ".prj", ".cpg", ".qpj", ".sbn", ".sbx", ".shp.xml"),
    # Raster attribute tables and world files sit beside the raster and are
    # additive: a categorical raster keeps its categories in a .vat.dbf.
    ".tif": (".tfw", ".tif.aux.xml", ".tif.vat.dbf", ".tif.vat.cpg", ".tif.ovr"),
}
_SIDECARS[".tiff"] = _SIDECARS[".tif"]

# How deep to follow table-referencing-table. Two levels covers crop production
# (a table of climate bins pointing at per-crop tables); the limit is a guard
# against a cycle rather than a real constraint.
_MAX_DEPTH = 3

# Extensions worth trying in a column the spec does not type as a path. Narrow on
# purpose: this is a guess, and a value that is not a reference must simply fail
# to fetch rather than corrupt the table.
_SPATIAL_EXTENSIONS = (".tif", ".tiff", ".shp", ".gpkg", ".vrt", ".img", ".asc")


def _fetch(url, destination):
    """Download url to destination, returning True on success."""
    try:
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        urllib.request.urlretrieve(url, destination)
        return True
    except Exception as exc:  # noqa: BLE001 - a missing companion is not fatal
        logger.debug("Could not fetch %s: %s", url, exc)
        return False


def _local_name(workdir, url):
    """Where a referenced file goes locally.

    One directory per referenced URL, named from a hash of it, with the file
    keeping its own basename. A reference may be "../Base_Data/dem.tif" or may
    collide with another column's file of the same name, and hashing sidesteps
    both without having to reconstruct the remote directory tree. Companions land
    in the same directory, so a shapefile's stem still resolves.
    """
    digest = hashlib.md5(url.encode("utf-8")).hexdigest()[:8]
    return os.path.join(workdir, digest, os.path.basename(
        urllib.parse.urlparse(url).path))


def path_columns(column_specs):
    """{lowercased column id: type} for the columns of a table that name files."""
    columns = {}
    for column in column_specs or []:
        column_type = getattr(column, "type", "")
        if column_type in PATH_COLUMN_TYPES and getattr(column, "id", None):
            columns[column.id.lower()] = column_type
    return columns


def _column_spec(column_specs, column_id):
    for column in column_specs or []:
        if (getattr(column, "id", "") or "").lower() == column_id:
            return column
    return None


def localise_table(local_path, source_url, column_specs, workdir,
                   depth=0, fetch=_fetch):
    """Fetch what a downloaded table references and repoint it at the copies.

    ``local_path`` is the already-downloaded table, ``source_url`` the URL it came
    from -- references resolve against that, not against the temporary file.
    Rewrites ``local_path`` in place. Returns the number of files fetched.

    A reference that cannot be fetched is left as it was: the model's own error
    then names the value that is actually missing, which is more use than a path
    into a temporary directory.
    """
    columns = path_columns(column_specs)
    if depth >= _MAX_DEPTH:
        return 0

    try:
        with open(local_path, newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.reader(handle))
    except (OSError, UnicodeDecodeError) as exc:
        logger.warning("Could not read table %s: %s", local_path, exc)
        return 0
    if not rows:
        return 0

    header = rows[0]
    # InVEST matches column names case-insensitively; the sample tables are
    # upper case while the spec ids are lower.
    targets = {index: columns[name.strip().lower()]
               for index, name in enumerate(header)
               if name.strip().lower() in columns}

    fetched = 0
    resolved = {}
    for row in rows[1:]:
        for index in range(len(row)):
            column_type = targets.get(index)
            reference = (row[index] or "").strip()
            if not reference:
                continue
            if column_type is None:
                # Not a column the spec types as a path, but some tables carry
                # references the spec cannot describe: habitat risk assessment's
                # criteria table holds either a number or a raster per cell. Only
                # values that name a spatial file are tried, and a value that is
                # not one simply fails to fetch and is left alone.
                if not reference.lower().endswith(_SPATIAL_EXTENSIONS):
                    continue
                column_type = "file"

            url = urllib.parse.urljoin(source_url, reference.replace("\\", "/"))
            if url in resolved:
                row[index] = resolved[url]
                continue

            destination = _local_name(workdir, url)
            if not fetch(url, destination):
                declared = index in targets
                report = logger.warning if declared else logger.debug
                report("Table %s references %s, which could not be fetched "
                       "from %s", os.path.basename(local_path), reference, url)
                continue
            fetched += 1

            # Companions are named from the stem, so the table lists ".tif.vat.dbf"
            # rather than ".vat.dbf" and both forms build by simple concatenation.
            stem, extension = os.path.splitext(urllib.parse.urlparse(url).path)
            base = url[:len(url) - len(extension)]
            for suffix in _SIDECARS.get(extension.lower(), ()):
                companion = base + suffix
                fetch(companion, os.path.join(os.path.dirname(destination),
                                              os.path.basename(stem) + suffix))

            if column_type == "csv" and index in targets:
                # A referenced table may reference data of its own.
                nested = _column_spec(column_specs, header[index].strip().lower())
                fetched += localise_table(
                    destination, url, getattr(nested, "columns", None),
                    workdir, depth=depth + 1, fetch=fetch)

            resolved[url] = destination
            row[index] = destination

    if not fetched:
        return 0

    with open(local_path, "w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows(rows)
    logger.info("Localised %d file(s) referenced by %s", fetched,
                os.path.basename(local_path))
    return fetched


def localise_tables(spec, args, sources, workdir, fetch=_fetch):
    """Localise every table argument that came from a URL.

    ``sources`` maps argument id to the URL it was originally given as, which is
    what the table's own references are relative to.
    """
    total = 0
    for inp in spec.inputs:
        source_url = sources.get(inp.id)
        local_path = args.get(inp.id)
        if not source_url or not local_path:
            continue
        if not str(local_path).lower().endswith(".csv"):
            continue
        total += localise_table(local_path, source_url,
                               getattr(inp, "columns", None), workdir,
                               fetch=fetch)
    return total
