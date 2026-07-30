"""Unit tests for the table-reference transport (tools/invest_tables.py).

No stack and no InVEST needed: column specs are duck-typed and the download is
injected, so the rewriting rules can be checked directly.
"""
import csv
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "tools"))

import invest_tables  # noqa: E402


class Column:
    """Stands in for a MODEL_SPEC column, which is inspected by id and type."""

    def __init__(self, identifier, column_type, columns=None):
        self.id = identifier
        self.type = column_type
        self.columns = columns


def recording_fetch(available):
    """A fetch that succeeds for the given URLs, recording what was asked for."""
    asked = []

    def fetch(url, destination):
        asked.append(url)
        if url not in available:
            return False
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        with open(destination, "w") as handle:
            handle.write(available[url])
        return True

    fetch.asked = asked
    return fetch


def write_csv(path, rows):
    with open(path, "w", newline="") as handle:
        csv.writer(handle).writerows(rows)


def read_csv(path):
    with open(path, newline="") as handle:
        return list(csv.reader(handle))


def test_declared_column_is_fetched_and_rewritten(tmp_path):
    table = tmp_path / "threats.csv"
    write_csv(table, [["THREAT", "CUR_PATH"],
                      ["crops", "crops_c.tif"],
                      ["urban", "urban_c.tif"]])
    base = "http://fileserver:8001/invest/HabitatQuality/threats.csv"
    fetch = recording_fetch({
        "http://fileserver:8001/invest/HabitatQuality/crops_c.tif": "raster",
        "http://fileserver:8001/invest/HabitatQuality/urban_c.tif": "raster"})

    count = invest_tables.localise_table(
        str(table), base, [Column("cur_path", "raster")],
        str(tmp_path / "refs"), fetch=fetch)

    assert count == 2
    rows = read_csv(table)
    # The header is untouched and each value now points at a file that exists.
    assert rows[0] == ["THREAT", "CUR_PATH"]
    for row in rows[1:]:
        assert os.path.isfile(row[1]), row


def test_blank_cells_and_unknown_columns_are_left_alone(tmp_path):
    table = tmp_path / "threats.csv"
    write_csv(table, [["THREAT", "BASE_PATH", "CUR_PATH", "WEIGHT"],
                      ["crops", "", "crops_c.tif", "0.7"]])
    base = "http://host/data/threats.csv"
    fetch = recording_fetch({"http://host/data/crops_c.tif": "raster"})

    invest_tables.localise_table(str(table), base,
                                 [Column("base_path", "raster"),
                                  Column("cur_path", "raster")],
                                 str(tmp_path / "refs"), fetch=fetch)

    rows = read_csv(table)
    assert rows[1][1] == "", rows          # blank stays blank
    assert rows[1][3] == "0.7", rows       # a number is not a path
    assert "http://host/data/" not in rows[1][3]


def test_a_reference_that_cannot_be_fetched_keeps_its_original_value(tmp_path):
    """The model's own error should name the value that is really missing."""
    table = tmp_path / "threats.csv"
    write_csv(table, [["CUR_PATH"], ["missing.tif"], ["present.tif"]])
    base = "http://host/data/threats.csv"
    fetch = recording_fetch({"http://host/data/present.tif": "raster"})

    invest_tables.localise_table(str(table), base, [Column("cur_path", "raster")],
                                 str(tmp_path / "refs"), fetch=fetch)

    rows = read_csv(table)
    assert rows[1][0] == "missing.tif", rows
    assert os.path.isfile(rows[2][0]), rows


def test_references_resolve_against_the_tables_own_url(tmp_path):
    """A "../" reference is relative to the table on the server, not to /tmp."""
    table = tmp_path / "biophysical.csv"
    write_csv(table, [["PATH"], ["../Base_Data/dem.tif"]])
    base = "http://host/invest/Model/biophysical.csv"
    fetch = recording_fetch({"http://host/invest/Base_Data/dem.tif": "raster"})

    count = invest_tables.localise_table(
        str(table), base, [Column("path", "raster")], str(tmp_path / "refs"),
        fetch=fetch)

    assert count == 1, fetch.asked
    assert os.path.isfile(read_csv(table)[1][0])


def test_shapefile_companions_come_along(tmp_path):
    table = tmp_path / "wave.csv"
    write_csv(table, [["POINT_VECTOR"], ["points.shp"]])
    base = "http://host/data/wave.csv"
    fetch = recording_fetch({"http://host/data/points.shp": "shp",
                             "http://host/data/points.shx": "shx",
                             "http://host/data/points.dbf": "dbf",
                             "http://host/data/points.prj": "prj"})

    invest_tables.localise_table(str(table), base,
                                 [Column("point_vector", "vector")],
                                 str(tmp_path / "refs"), fetch=fetch)

    local = read_csv(table)[1][0]
    stem = os.path.splitext(local)[0]
    for suffix in (".shp", ".shx", ".dbf", ".prj"):
        assert os.path.isfile(stem + suffix), suffix


def test_a_referenced_table_is_followed(tmp_path):
    """crop production points at tables that point at rasters."""
    inner = "CLIMATE_BIN,PATH\r\n1,yield.tif\r\n"
    table = tmp_path / "outer.csv"
    write_csv(table, [["CROP", "PATH"], ["abaca", "abaca.csv"]])
    base = "http://host/data/outer.csv"
    fetch = recording_fetch({"http://host/data/abaca.csv": inner,
                             "http://host/data/yield.tif": "raster"})

    count = invest_tables.localise_table(
        str(table), base,
        [Column("path", "csv", columns=[Column("path", "raster")])],
        str(tmp_path / "refs"), fetch=fetch)

    assert count == 2, fetch.asked
    nested = read_csv(table)[1][1]
    assert os.path.isfile(nested)
    assert os.path.isfile(read_csv(nested)[1][1])


def test_an_undeclared_cell_naming_a_raster_is_still_fetched(tmp_path):
    """habitat risk assessment's criteria table: a number or a raster per cell."""
    table = tmp_path / "criteria.csv"
    write_csv(table, [["HABITAT", "eelgrass"],
                      ["recruitment rate", "2"],
                      ["connectivity rate", "layers/eelgrass_conn.tif"]])
    base = "http://host/data/criteria.csv"
    fetch = recording_fetch(
        {"http://host/data/layers/eelgrass_conn.tif": "raster"})

    count = invest_tables.localise_table(str(table), base, [],
                                         str(tmp_path / "refs"), fetch=fetch)

    assert count == 1, fetch.asked
    rows = read_csv(table)
    assert rows[1][1] == "2", rows
    assert os.path.isfile(rows[2][1]), rows


def test_localise_tables_only_touches_arguments_that_came_from_a_url(tmp_path):
    class Spec:
        inputs = [Column("from_url", "csv", columns=[Column("path", "raster")]),
                  Column("local", "csv", columns=[Column("path", "raster")])]

    remote = tmp_path / "remote.csv"
    local = tmp_path / "local.csv"
    for path in (remote, local):
        write_csv(path, [["PATH"], ["data.tif"]])

    fetch = recording_fetch({"http://host/data/data.tif": "raster"})
    count = invest_tables.localise_tables(
        Spec(), {"from_url": str(remote), "local": str(local)},
        {"from_url": "http://host/data/remote.csv"}, str(tmp_path / "refs"),
        fetch=fetch)

    assert count == 1, fetch.asked
    assert read_csv(local)[1][0] == "data.tif", "a local argument was rewritten"
