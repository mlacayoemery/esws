"""Drawing the pipeline that ESWS jobs already form.

Nothing in the dashboard asks anyone to draw a workflow, and yet one exists: a
job publishes its outputs, they are registered as elements, and any later job can
select them as inputs. Point a job at another job's output and you have a
pipeline -- one that re-runs itself, since a reactive job checks whether its
inputs changed since it last ran.

So the graph is *derived*, never declared. This module turns a list of jobs and
their input/output elements into nodes and edges, and renders them two ways:

  * Mermaid, for the dashboard, because the docs already render Mermaid.
  * BPMN 2.0, for interchange with a modeller such as bpmn.io or Camunda.

The BPMN needs a word of explanation. This graph is a dataflow -- an edge means
"B consumes what A produced" -- while BPMN is first a control-flow notation,
where a sequence flow means "B happens after A". Those are not the same claim.
They coincide here, because a job that consumes another's output genuinely must
run after it, so a sequence flow is true as far as it goes. It is just not the
whole truth, so each edge also carries a DataObject with the element's name and
the associations that produced and consumed it. Readers that ignore data
associations still see a correct ordering; readers that do not, see why.

Kept free of Django so the shapes can be exercised on their own.
"""
import re
import xml.etree.ElementTree as ET

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
BPMNDI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
DC_NS = "http://www.omg.org/spec/DD/20100524/DC"
DI_NS = "http://www.omg.org/spec/DD/20100524/DI"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

# Statuses a job can be in, and the Mermaid class each gets. Kept here rather
# than in CSS so the same names can be used by any renderer.
_STATUS_CLASS = {
    "Succeeded": "done",
    "Failed": "failed",
    "Accepted": "running",
    "Started": "running",
    "Run": "pending",
    "Pending": "pending",
    "Validate": "pending",
}


def build(jobs, produced_by, inputs_of):
    """Nodes and edges for a set of jobs.

    ``jobs`` is an iterable of objects with ``pk``, ``identifier`` and
    ``status``. ``produced_by`` maps an element key to the pk of the job that
    published it. ``inputs_of`` maps a job pk to the element keys it consumes.

    Returns ({pk: node}, [edge]) where an edge is
    (producer pk, consumer pk, element key).
    """
    nodes = {}
    for job in jobs:
        nodes[job.pk] = {
            "pk": job.pk,
            "identifier": job.identifier,
            "status": job.status,
            "css": _STATUS_CLASS.get(job.status, "pending"),
        }

    edges = []
    for pk in sorted(nodes):
        for key in inputs_of.get(pk, ()):
            producer = produced_by.get(key)
            # A job consuming its own output is a re-run, not a dependency.
            if producer is None or producer == pk or producer not in nodes:
                continue
            edges.append((producer, pk, key))
    # Stable order so the rendering does not churn between requests.
    return nodes, sorted(set(edges))


def _label(text):
    """Mermaid node text: quotes and brackets end a node early."""
    return re.sub(r'[\["\]{}|]', " ", str(text)).strip()


def to_mermaid(nodes, edges):
    """The graph as a Mermaid flowchart."""
    lines = ["flowchart LR"]
    for pk in sorted(nodes):
        node = nodes[pk]
        lines.append('    job%d["%s<br/><small>job %d &middot; %s</small>"]:::%s'
                     % (pk, _label(node["identifier"]), pk,
                        _label(node["status"]), node["css"]))
    for producer, consumer, key in edges:
        lines.append("    job%d -->|%s| job%d"
                     % (producer, _label(key), consumer))
    if not edges:
        lines.append("    %% no job consumes another job's output yet")

    lines += [
        "    classDef done fill:#d7ecd9,stroke:#4a7a52,color:#1f3a25;",
        "    classDef failed fill:#f2d7d7,stroke:#a35050,color:#4a1f1f;",
        "    classDef running fill:#fdf0d0,stroke:#a3853f,color:#463714;",
        "    classDef pending fill:#e6e6e6,stroke:#7a7a7a,color:#2b2b2b;",
    ]
    return "\n".join(lines)


def _ident(prefix, value):
    """An NCName-safe id: BPMN ids may not start with a digit or hold colons."""
    return "%s_%s" % (prefix, re.sub(r"[^0-9A-Za-z_]", "_", str(value)))


def to_bpmn(nodes, edges, process_id="esws-pipeline",
            name="ESWS job pipeline"):
    """The graph as BPMN 2.0 XML.

    Each job is a serviceTask -- it is work a service performs, not a human. Each
    dependency is a sequenceFlow, which carries the ordering, plus a dataObject
    for the element and the associations that wrote and read it, which carry the
    reason.
    """
    ET.register_namespace("bpmn", BPMN_NS)
    ET.register_namespace("bpmndi", BPMNDI_NS)
    ET.register_namespace("dc", DC_NS)
    ET.register_namespace("di", DI_NS)
    ET.register_namespace("xsi", XSI_NS)

    definitions = ET.Element(
        "{%s}definitions" % BPMN_NS,
        {"id": _ident("defs", process_id),
         "targetNamespace": "http://esws.unige.ch/bpmn",
         "exporter": "ESWS", "exporterVersion": "1"})
    process = ET.SubElement(definitions, "{%s}process" % BPMN_NS,
                            {"id": _ident("proc", process_id),
                             "name": name, "isExecutable": "false"})

    task_ids = {}
    for pk in sorted(nodes):
        node = nodes[pk]
        task_id = _ident("job", pk)
        task_ids[pk] = task_id
        ET.SubElement(process, "{%s}serviceTask" % BPMN_NS,
                      {"id": task_id,
                       "name": "%s (job %d, %s)" % (node["identifier"], pk,
                                                    node["status"])})

    # One data object per element, even if several jobs read it.
    for index, key in enumerate(sorted({key for _p, _c, key in edges})):
        ET.SubElement(process, "{%s}dataObject" % BPMN_NS,
                      {"id": _ident("data", index), "name": str(key)})
    data_ids = {key: _ident("data", index) for index, key
                in enumerate(sorted({key for _p, _c, key in edges}))}

    for index, (producer, consumer, key) in enumerate(edges):
        ET.SubElement(process, "{%s}sequenceFlow" % BPMN_NS,
                      {"id": _ident("flow", index),
                       "sourceRef": task_ids[producer],
                       "targetRef": task_ids[consumer],
                       "name": str(key)})

    # Associations live on the tasks: the consumer reads the data object into one
    # of its inputs, the producer writes one of its outputs to it. Both ends are
    # required -- a dataInputAssociation without a targetRef is not BPMN, it just
    # looks like it -- so each task declares an ioSpecification naming the inputs
    # and outputs the associations refer to.
    #
    # Collected per task first because a task is usually both a producer and a
    # consumer, and tActivity orders its children: ioSpecification, then every
    # dataInputAssociation, then every dataOutputAssociation.
    reads, writes = {}, {}
    for index, (producer, consumer, key) in enumerate(edges):
        writes.setdefault(producer, []).append((index, key))
        reads.setdefault(consumer, []).append((index, key))

    for pk in sorted(nodes):
        if pk not in reads and pk not in writes:
            continue  # nothing flows through it; leave the task bare
        task = process.find(
            "{%s}serviceTask[@id='%s']" % (BPMN_NS, task_ids[pk]))

        spec = ET.SubElement(task, "{%s}ioSpecification" % BPMN_NS,
                             {"id": _ident("io", pk)})
        for index, key in reads.get(pk, []):
            ET.SubElement(spec, "{%s}dataInput" % BPMN_NS,
                          {"id": _ident("in", index), "name": str(key)})
        for index, key in writes.get(pk, []):
            ET.SubElement(spec, "{%s}dataOutput" % BPMN_NS,
                          {"id": _ident("out", index), "name": str(key)})
        # Both sets are required even when empty.
        input_set = ET.SubElement(spec, "{%s}inputSet" % BPMN_NS,
                                  {"id": _ident("inset", pk)})
        for index, _key in reads.get(pk, []):
            ET.SubElement(input_set,
                          "{%s}dataInputRefs" % BPMN_NS).text = _ident("in", index)
        output_set = ET.SubElement(spec, "{%s}outputSet" % BPMN_NS,
                                   {"id": _ident("outset", pk)})
        for index, _key in writes.get(pk, []):
            ET.SubElement(output_set,
                          "{%s}dataOutputRefs" % BPMN_NS).text = _ident("out", index)

        for index, key in reads.get(pk, []):
            received = ET.SubElement(task,
                                     "{%s}dataInputAssociation" % BPMN_NS,
                                     {"id": _ident("inassoc", index)})
            ET.SubElement(received,
                          "{%s}sourceRef" % BPMN_NS).text = data_ids[key]
            ET.SubElement(received,
                          "{%s}targetRef" % BPMN_NS).text = _ident("in", index)
        for index, key in writes.get(pk, []):
            produced = ET.SubElement(task,
                                     "{%s}dataOutputAssociation" % BPMN_NS,
                                     {"id": _ident("outassoc", index)})
            ET.SubElement(produced,
                          "{%s}sourceRef" % BPMN_NS).text = _ident("out", index)
            ET.SubElement(produced,
                          "{%s}targetRef" % BPMN_NS).text = data_ids[key]

    return ET.tostring(definitions, encoding="unicode", xml_declaration=True)
