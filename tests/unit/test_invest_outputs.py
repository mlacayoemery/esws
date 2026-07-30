"""Unit tests for output anticipation (tools/invest_outputs.py).

Stack-free: the two decisions worth pinning -- whether an output is produced at
all, and whether it is a result rather than a working file -- are pure functions
of a spec object, so they are checked against stand-ins here.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "tools"))

import invest_outputs  # noqa: E402


class Output:
    """Stands in for a MODEL_SPEC output, read by path and created_if."""

    def __init__(self, path, created_if=True, identifier=None):
        self.path = path
        self.created_if = created_if
        self.id = identifier or (path or "").replace("/", "_")


def test_a_bool_condition_is_taken_at_face_value():
    assert invest_outputs.output_is_expected(Output("a.tif", True), {})
    assert not invest_outputs.output_is_expected(Output("a.tif", False), {})


def test_a_condition_naming_an_absent_argument_is_false():
    """The whole point of created_if: an input the caller never supplied is
    falsey, and evaluating it as a NameError would wrongly mark the output as
    expected."""
    condition = Output("sub.shp", "sub_watersheds_path")
    assert not invest_outputs.output_is_expected(condition, {"lulc_path": "x"})
    assert invest_outputs.output_is_expected(condition,
                                             {"sub_watersheds_path": "y"})


def test_a_compound_condition_is_evaluated():
    output = Output("v.tif", "do_valuation and (not price_table)")
    assert invest_outputs.output_is_expected(output, {"do_valuation": "true"})
    assert not invest_outputs.output_is_expected(
        output, {"do_valuation": "true", "price_table": "t.csv"})
    assert not invest_outputs.output_is_expected(output, {})


def test_an_empty_argument_counts_as_absent():
    output = Output("sub.shp", "sub_watersheds_path")
    assert not invest_outputs.output_is_expected(output,
                                                 {"sub_watersheds_path": ""})


def test_an_unparseable_condition_assumes_the_output_is_produced():
    """Better to anticipate an output that never arrives than to miss one."""
    assert invest_outputs.output_is_expected(Output("x.tif", "?? not python"), {})


def test_args_omitted_means_every_conditional_output():
    """DescribeProcess has to advertise them all: WPS cannot say that an output
    only appears under some conditions."""
    assert invest_outputs.output_is_expected(Output("x.tif", "whatever"), None)


def test_a_top_level_output_is_a_result():
    """17 of the 26 models write their results at the top level of the
    workspace, carbon among them, so a filter that kept only output/ would
    discard nearly everything worth publishing."""
    assert invest_outputs.is_primary_output(Output("c_storage.tif"))
    assert invest_outputs.is_primary_output(Output("output/wyield.tif"))
    assert invest_outputs.is_primary_output(Output("output/per_pixel/aet.tif"))
    assert invest_outputs.is_primary_output(Output("visualization_outputs/x.tif"))


def test_working_files_are_not_results():
    for path in ("intermediate/clipped_lulc.tif",
                 "intermediate_outputs/kc_raster.tif",
                 "intermediate_output/x.tif",
                 "intermediate_files/x.tif",
                 "taskgraph_cache/taskgraph.db",
                 "tmp/scratch.tif"):
        assert not invest_outputs.is_primary_output(Output(path)), path


def test_anticipated_outputs_applies_both_filters():
    class Spec:
        outputs = [Output("output/wyield.tif"),
                   Output("intermediate/eto.tif"),
                   Output("output/sub.shp", "sub_watersheds_path"),
                   Output(None)]                      # a scalar, nothing to fetch

    everything = invest_outputs.anticipated_outputs(Spec())
    assert [o.path for o in everything] == ["output/wyield.tif",
                                            "intermediate/eto.tif",
                                            "output/sub.shp"]

    results = invest_outputs.anticipated_outputs(Spec(), {}, primary_only=True)
    assert [o.path for o in results] == ["output/wyield.tif"]
