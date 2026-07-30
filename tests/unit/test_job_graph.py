"""Unit tests for the job pipeline graph (tools/job_graph.py).

Stack-free: the graph is built from plain data, so the derivation and both
renderings are checked directly. The BPMN is validated against OMG's own schema,
which is vendored in tests/data -- an exporter that emits BPMN-shaped XML nobody
can open is worse than no exporter.
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import job_graph  # noqa: E402


class Job:
    def __init__(self, pk, identifier, status="Succeeded"):
        self.pk, self.identifier, self.status = pk, identifier, status


def sample():
    jobs = [Job(1, "annual_water_yield"), Job(2, "sdr"), Job(3, "ndr", "Run")]
    produced = {"results:wyield": 1, "results:watersheds": 1, "results:sed_export": 2}
    consumed = {2: ["results:wyield", "invest:dem"],
                3: ["results:sed_export", "results:watersheds"]}
    return job_graph.build(jobs, produced, consumed)


def test_an_edge_is_derived_from_what_a_job_consumes():
    nodes, edges = sample()
    assert len(nodes) == 3
    assert edges == [(1, 2, "results:wyield"),
                     (1, 3, "results:watersheds"),
                     (2, 3, "results:sed_export")]


def test_an_input_nobody_produced_is_not_an_edge():
    """Demo data a job consumes came from the loader, not from another job."""
    _nodes, edges = job_graph.build([Job(1, "carbon")], {}, {1: ["invest:lulc"]})
    assert edges == []


def test_a_job_consuming_its_own_output_is_not_a_dependency():
    """That is a re-run, and drawing it as a self-edge would suggest a cycle."""
    _nodes, edges = job_graph.build([Job(1, "carbon")], {"results:c": 1},
                                    {1: ["results:c"]})
    assert edges == []


def test_status_becomes_a_style():
    nodes, _edges = sample()
    assert nodes[1]["css"] == "done"
    assert nodes[3]["css"] == "pending"
    failed, _ = job_graph.build([Job(9, "sdr", "Failed")], {}, {})
    assert failed[9]["css"] == "failed"


def test_mermaid_carries_the_nodes_and_the_labelled_edges():
    diagram = job_graph.to_mermaid(*sample())
    assert diagram.startswith("flowchart LR")
    assert 'job1["annual_water_yield' in diagram
    assert "job2 -->|results:sed_export| job3" in diagram


def test_mermaid_says_so_when_nothing_is_chained():
    diagram = job_graph.to_mermaid(*job_graph.build([Job(1, "carbon")], {}, {}))
    assert "no job consumes another job" in diagram


def test_mermaid_labels_cannot_break_out_of_a_node():
    """An element identifier holding a bracket would end the node early and
    produce a diagram that renders as an error box."""
    nodes, edges = job_graph.build(
        [Job(1, 'we"ird["'), Job(2, "sdr")], {'a"b[c]': 1}, {2: ['a"b[c]']})
    diagram = job_graph.to_mermaid(nodes, edges)
    for line in diagram.splitlines():
        if line.strip().startswith("job1["):
            assert line.count("[") == 1 and line.count("]") == 1, line


def test_bpmn_validates_against_the_omg_schema():
    etree = pytest.importorskip("lxml.etree")
    xsd = os.path.join(ROOT, "tests", "data", "BPMN20.xsd")
    if not os.path.exists(xsd):
        pytest.skip("OMG BPMN schema not vendored")

    xml = job_graph.to_bpmn(*sample())
    schema = etree.XMLSchema(etree.parse(xsd))
    document = etree.fromstring(xml.encode("utf-8"))
    assert schema.validate(document), schema.error_log


def test_bpmn_carries_the_ordering_and_the_reason():
    etree = pytest.importorskip("lxml.etree")
    ns = {"b": job_graph.BPMN_NS}
    document = etree.fromstring(job_graph.to_bpmn(*sample()).encode("utf-8"))

    # Ordering: a job that consumes another's output runs after it.
    flows = {(f.get("sourceRef"), f.get("targetRef"))
             for f in document.iterfind(".//b:sequenceFlow", ns)}
    assert ("job_1", "job_2") in flows
    assert ("job_2", "job_3") in flows

    # Reason: the element that passed between them, as a data object, with an
    # association at each end. Sequence flows alone would say B follows A without
    # saying why.
    assert {d.get("name") for d in document.iterfind(".//b:dataObject", ns)} == {
        "results:wyield", "results:watersheds", "results:sed_export"}
    assert document.find(".//b:dataOutputAssociation", ns) is not None
    assert document.find(".//b:dataInputAssociation", ns) is not None


def test_bpmn_ids_are_ncnames():
    """Element identifiers hold colons; BPMN ids may not."""
    etree = pytest.importorskip("lxml.etree")
    document = etree.fromstring(job_graph.to_bpmn(*sample()).encode("utf-8"))
    for element in document.iter():
        identifier = element.get("id")
        if identifier:
            assert ":" not in identifier, identifier
            assert not identifier[0].isdigit(), identifier
