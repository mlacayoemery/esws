"""Unit tests for results layout naming (tools/results_layout.py)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import results_layout as rl  # noqa: E402


def test_the_default_is_a_workspace_per_run():
    assert rl.layout(None if "ESWS_RESULTS_LAYOUT" not in os.environ else "run") \
        in (rl.LAYOUT_RUN, rl.LAYOUT_SERIES)
    assert rl.layout("run") == rl.LAYOUT_RUN
    assert rl.layout("series") == rl.LAYOUT_SERIES
    assert rl.layout("nonsense") == rl.LAYOUT_RUN, "an unknown layout must not"


def test_run_layout_keeps_the_model_s_own_layer_name():
    """Uniqueness is the workspace's job, so the name needs no mangling."""
    ws, layer = rl.target("raster", "sdr", "sed_export_gura", "a1b2c3d4", "run")
    assert ws == "run_a1b2c3d4"
    assert layer == "sed_export_gura"


def test_series_layout_is_stable_across_runs():
    first = rl.target("raster", "sdr", "sed_export", "a1b2", "series")
    second = rl.target("raster", "sdr", "sed_export", "e5f6", "series")
    assert first == second, "a series must not move when the run changes"
    assert first[1] == "sdr_sed_export"


def test_names_are_ncnames():
    """Workspace names become XML namespace prefixes; layer names go in URLs."""
    assert rl.safe("a:b/c d") == "a_b_c_d"
    assert not rl.safe("2026run")[0].isdigit()
    assert rl.safe("!!!") == "unnamed"


def test_the_results_suffix_is_stripped_when_matching_a_series():
    """Two runs labelled differently are still the same output."""
    assert rl.unsuffixed("wyield_gura", "gura") == "wyield"
    assert rl.unsuffixed("wyield_gura", "_gura") == "wyield"
    assert rl.unsuffixed("wyield", "") == "wyield"
    assert rl.unsuffixed("wyield_other", "gura") == "wyield_other"


def test_a_vector_series_needs_postgis():
    """A shapefile cannot be appended to, so a series of them is not possible."""
    assert rl.requires_postgis("vector", "series", "files")
    assert not rl.requires_postgis("vector", "series", "postgis")
    assert not rl.requires_postgis("vector", "run", "files")
    # Rasters are fine either way: a mosaic is a directory of files.
    assert not rl.requires_postgis("raster", "series", "files")
