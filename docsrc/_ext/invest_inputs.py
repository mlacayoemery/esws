"""Sphinx directive that diagrams an InVEST model's inputs.

Usage in .rst::

    .. invest-inputs:: annual_water_yield

It reads the model's ``MODEL_SPEC["args"]`` and renders every input as a node,
colour-coded by requirement:

* **green**  -- required (``required`` is ``True`` / the default)
* **amber**  -- conditional (``required`` is an expression string)
* **grey**   -- optional (``required`` is ``False``)

Two layouts are available via the ``:style:`` option:

``tree`` (default)
    A dependency tree: the model is the root and an edge runs from each
    parameter to the parameter that gates it, so "turn on valuation" visibly
    branches to the inputs it enables.

``boxes``
    A single model box with gated inputs nested as sub-boxes. This mirrors the
    InVEST desktop UI's collapsible containers, but mermaid allots a full rank
    to each invisible (``~~~``) stacking link, so the diagram grows very tall --
    ~8700px for wind_energy's 20 inputs, against ~2500px for the same model as a
    tree. It is kept for single-model embeds, not for the 25-model catalog.

When a parameter's ``required`` expression names several other parameters, the
node hangs off the first one; the full condition is always printed on the node.

The runner-only args ``workspace_dir``, ``n_workers`` and ``results_suffix`` are
omitted. Inputs are read from the installed natcap.invest package at build time,
so the docs must be built in an InVEST-enabled environment.

Output is a lightweight Mermaid ``flowchart`` (rendered client-side by
sphinxcontrib.mermaid), so it works on a static GitHub Pages site.
"""
import importlib
import os
import re

# docutils/sphinx are only needed inside a Sphinx build; import lazily so the
# rendering helpers stay usable on a bare interpreter (previews).
try:
    from docutils import nodes
    from docutils.parsers.rst import Directive, directives
except Exception:  # pragma: no cover
    nodes = None
    Directive = object
    directives = None

INFRA_ARGS = {"workspace_dir", "n_workers", "results_suffix"}

_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

# requirement class -> (fill, stroke). These names land verbatim as CSS classes on
# the rendered SVG nodes, so they are namespaced: Sphinx's own basic.css styles a
# bare `.optional` at font-size 1.3em (it marks optional arguments in signatures),
# which silently rendered every grey node 30% larger than its neighbours.
_COLORS = {
    "inputRequired": ("#e8f5e9", "#2e7d32"),
    "inputConditional": ("#fff3e0", "#ef6c00"),
    "inputOptional": ("#eceff1", "#546e7a"),
}


# --------------------------------------------------------------------------- #
# spec resolution
# --------------------------------------------------------------------------- #
def _normalize_inputs(inputs):
    """MODEL_SPEC.inputs -> [{id, name, type, required}] (required: True|False|str).

    ``inputs`` is a list of ``natcap.invest.spec.Input`` objects. The concrete
    subclass carries the type as a ``type`` class attribute ('raster', 'vector',
    'csv', 'number', ...), which is what the diagrams label nodes with.
    """
    out = []
    for inp in inputs:
        req = inp.required  # bool, or an expression string for conditional inputs
        req = req if isinstance(req, str) else bool(req)
        out.append({
            "id": inp.id,
            "name": str(inp.name or inp.id),
            "type": str(getattr(inp, "type", "") or ""),
            "required": req,
        })
    return out


def _load_model(model_id):
    """Return (model_title, [arg, ...]) from the installed natcap.invest package."""
    from natcap.invest import models
    spec = models.model_id_to_spec[model_id]
    return str(spec.model_title or model_id), _normalize_inputs(spec.inputs)


# --------------------------------------------------------------------------- #
# mermaid rendering
# --------------------------------------------------------------------------- #
def _mm_text(s):
    """Escape a string for a quoted mermaid label/title."""
    return (str(s).replace("\\", "").replace('"', "'")
            .replace("|", "/").replace("\n", " ").strip())


def _class_of(arg):
    req = arg["required"]
    if isinstance(req, str):
        return "inputConditional"
    return "inputRequired" if req else "inputOptional"


def _controllers(arg, arg_ids):
    """Arg ids referenced by this arg's `required` expression (its gating params)."""
    req = arg["required"]
    if not isinstance(req, str):
        return []
    out = []
    for tok in _IDENT.findall(req):
        if tok in arg_ids and tok != arg["id"] and tok not in out:
            out.append(tok)
    return out


def _leaf_label(arg):
    lines = [_mm_text(arg["name"] or arg["id"])]
    lines.append(_mm_text(arg["id"] + (" &middot; " + arg["type"] if arg["type"] else "")))
    if isinstance(arg["required"], str):
        lines.append("only if: " + _mm_text(arg["required"]))
    return "<br/>".join(lines)


def _box_title(arg):
    # keep short: long subgraph titles clip in some mermaid renderers. The
    # parameter's id/type/condition is shown on its node inside the box.
    return _mm_text(arg["name"] or arg["id"])


def _self_label(arg):
    """Label for a gating parameter's own node (the box title already has its name)."""
    label = _mm_text(arg["id"] + (" &middot; " + arg["type"] if arg["type"] else ""))
    if isinstance(arg["required"], str):
        label += "<br/>only if: " + _mm_text(arg["required"])
    return label


def build_mermaid(model_name, model_id, args):
    args = [a for a in args if a["id"] not in INFRA_ARGS]
    by_id = {a["id"]: a for a in args}
    ids = set(by_id)

    # nest each input under the first parameter that gates it (a forest)
    children = {aid: [] for aid in by_id}
    top = []
    for a in args:
        ctrls = [c for c in _controllers(a, ids) if c in by_id]
        if ctrls:
            children[ctrls[0]].append(a["id"])
        else:
            top.append(a["id"])

    lines = ["flowchart TB"]
    for cls, (fill, stroke) in _COLORS.items():
        lines.append("  classDef %s fill:%s,stroke:%s,color:#222;" % (cls, fill, stroke))
    styles = []
    counter = [0]

    def emit(aid, indent):
        arg = by_id[aid]
        cls = _class_of(arg)
        pad = "  " * indent
        if children[aid]:
            sid = "s%d" % counter[0]
            counter[0] += 1
            lines.append('%ssubgraph %s["%s"]' % (pad, sid, _box_title(arg)))
            lines.append("%s  direction TB" % pad)
            selfid = "n%d" % counter[0]  # the gating parameter itself, shown first
            counter[0] += 1
            lines.append('%s  %s["%s"]:::%s' % (pad, selfid, _self_label(arg), cls))
            child_ids = [selfid] + [emit(c, indent + 1) for c in children[aid]]
            if len(child_ids) > 1:  # invisible chain stacks the box's contents
                lines.append("%s  %s" % (pad, " ~~~ ".join(child_ids)))
            lines.append("%send" % pad)
            fill, stroke = _COLORS[cls]
            styles.append("style %s fill:%s,stroke:%s" % (sid, fill, stroke))
            return sid
        nid = "n%d" % counter[0]
        counter[0] += 1
        lines.append('%s%s["%s"]:::%s' % (pad, nid, _leaf_label(arg), cls))
        return nid

    lines.append('  subgraph MODEL["%s"]' % _mm_text(model_id))
    lines.append("    direction TB")
    lines.append('    hdr["%s"]' % _mm_text(model_name))  # header carries the name
    ordered = ["hdr"] + [emit(aid, 2) for aid in top]
    if len(ordered) > 1:
        lines.append("    " + " ~~~ ".join(ordered))
    lines.append("  end")
    styles.append("style hdr fill:#1565c0,stroke:#0d47a1,color:#ffffff")
    lines.append("  style MODEL fill:#ffffff,stroke:#1565c0,stroke-width:2px,color:#0d47a1")
    lines.extend("  " + s for s in styles)
    return "\n".join(lines)


def build_mermaid_tree(model_name, model_id, args):
    """Dependency-tree style: root = model name; an edge runs from each parameter
    to the parameter (or the root) that enables it. Required / optional params are
    colour-distinguished; conditionally-enabled params hang off their toggle."""
    args = [a for a in args if a["id"] not in INFRA_ARGS]
    by_id = {a["id"]: a for a in args}
    ids = set(by_id)

    lines = ["flowchart LR"]
    for cls, (fill, stroke) in _COLORS.items():
        lines.append("  classDef %s fill:%s,stroke:%s,color:#222;" % (cls, fill, stroke))

    lines.append('  root(["%s"])' % _mm_text(model_name))
    lines.append("  style root fill:#1565c0,stroke:#0d47a1,color:#ffffff")

    nid = {a["id"]: "n%d" % i for i, a in enumerate(args)}
    for a in args:
        lines.append('  %s["%s"]:::%s' % (nid[a["id"]], _leaf_label(a), _class_of(a)))
    for a in args:
        ctrls = [c for c in _controllers(a, ids) if c in by_id]
        parent = nid[ctrls[0]] if ctrls else "root"
        lines.append("  %s --> %s" % (parent, nid[a["id"]]))
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# directive
# --------------------------------------------------------------------------- #
class InvestInputsDirective(Directive):
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = ({"title": directives.unchanged, "style": directives.unchanged}
                   if directives else {})
    has_content = False

    def run(self):
        model_id = self.arguments[0].strip()
        try:
            model_name, args = _load_model(model_id)
        except Exception as exc:  # noqa: BLE001 - visible placeholder
            box = nodes.error()
            box += nodes.paragraph(
                text="invest-inputs: could not resolve model %r (%s)" % (model_id, exc))
            return [box]

        style = (self.options.get("style") or "tree").strip().lower()
        builder = build_mermaid if style == "boxes" else build_mermaid_tree
        code = builder(self.options.get("title") or model_name, model_id, args)
        try:
            from sphinxcontrib.mermaid import mermaid as mermaid_node
            node = mermaid_node()
            node["code"] = code
            node["options"] = {}
            return [node]
        except Exception:  # pragma: no cover
            return [nodes.raw("", '<pre class="mermaid">\n%s\n</pre>' % code,
                              format="html")]


def setup(app):
    app.add_directive("invest-inputs", InvestInputsDirective)
    return {"version": "0.5", "parallel_read_safe": True, "parallel_write_safe": True}
