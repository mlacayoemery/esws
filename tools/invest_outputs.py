"""Working out what an InVEST run will produce, before it runs.

Shared by the WPS wrapper, which needs it to decide what to publish, and by the
dashboard, which needs it to list a job's anticipated outputs while the job is
still queued. Kept free of pywps and easyows so the dashboard can import it
without dragging the server stack in.
"""
import logging
import os

logger = logging.getLogger("invest_outputs")


class _Falsey(dict):
    """Missing names are False, not an error."""

    def __missing__(self, key):
        return False


def output_is_expected(output, args):
    """Whether ``output``'s created_if condition holds for ``args``.

    created_if is either a bool or an expression naming other inputs, e.g.
    "sub_watersheds_path" or "do_valuation and (not price_table)". An input the
    caller never supplied is falsey -- that is the whole point of the condition,
    and evaluating it as a NameError would wrongly mark the output as expected.
    """
    condition = getattr(output, "created_if", True)
    if isinstance(condition, bool):
        return condition
    if args is None:
        return True
    env = _Falsey((key, bool(value)) for key, value in args.items())
    try:
        return bool(eval(condition, {"__builtins__": {}}, env))  # noqa: S307
    except Exception:  # noqa: BLE001 - an unparseable condition is not fatal
        logger.debug("Could not evaluate created_if %r; assuming produced",
                     condition)
        return True


# Top-level directories holding working files rather than results. Matching on
# these rather than keeping only "output/" because most models put their results
# at the top level of the workspace -- 17 of 26, carbon among them -- so an
# allow-list of output/ would discard almost everything worth publishing.
_INTERMEDIATE_DIRS = {"taskgraph_cache", "tmp"}


def is_primary_output(output):
    """Whether this output is a result rather than a working file.

    Publishing every declared output means a single annual_water_yield run puts
    36 layers on a server, most of them clipped inputs and convolution kernels.
    """
    parts = (getattr(output, "path", "") or "").split("/")
    if len(parts) < 2:
        return True  # top level: the model's own results
    head = parts[0]
    return not (head.startswith("intermediate") or head in _INTERMEDIATE_DIRS)


def anticipated_outputs(spec, args=None, primary_only=False):
    """The file outputs a run with ``args`` is expected to produce.

    With args omitted this is every file output the model declares, which is
    what DescribeProcess has to advertise -- WPS has no way to say that an
    output only appears under some conditions.
    """
    expected = []
    for output in spec.outputs:
        # Only file outputs have a workspace-relative path; numeric and string
        # outputs are metadata with nothing to fetch or publish.
        if not getattr(output, "path", None):
            continue
        if not output_is_expected(output, args):
            continue
        if primary_only and not is_primary_output(output):
            continue
        expected.append(output)
    return expected


def resolved_output_paths(spec, workspace_dir, args=None, primary_only=False):
    """[(output, absolute path)] for the outputs a run is expected to produce.

    A list of pairs rather than a dict: spec.Output is a pydantic model carrying
    a set field (VectorOutput.geometry_types), so it is not hashable and cannot
    be a key.

    Paths come from InVEST's own FileRegistry, which is what applies
    results_suffix: a suffixed run writes c_storage_bas_gura.tif, not
    c_storage_bas.tif, so joining ``output.path`` onto the workspace finds
    nothing whenever a suffix is set -- and the sample datastacks nearly all set
    one. Output ids containing a bracketed pattern are substituted per run and
    cannot be resolved generically, so those fall back to the declared path.
    """
    # FileRegistry concatenates path + file_suffix + extension, so the separator
    # has to be part of the suffix: "gura" yields wyieldgura.tif, while InVEST
    # actually writes wyield_gura.tif. Normalise once and use the same value for
    # the manual fallback below.
    suffix = None
    if args:
        raw = args.get("results_suffix") or None
        if raw:
            suffix = raw if str(raw).startswith("_") else "_%s" % raw

    registry = None
    try:
        from natcap.invest.file_registry import FileRegistry
        registry = FileRegistry(spec.outputs, workspace_dir, file_suffix=suffix)
    except Exception as exc:  # noqa: BLE001 - fall back to manual suffixing
        logger.debug("No FileRegistry (%s); suffixing by hand", exc)

    resolved = []
    for output in anticipated_outputs(spec, args, primary_only=primary_only):
        path = None
        if registry is not None and "[" not in (output.id or ""):
            try:
                path = registry[output.id]
            except Exception:  # noqa: BLE001 - not every id indexes cleanly
                path = None
        if not path:
            relative = output.path
            if suffix:
                stem, ext = os.path.splitext(relative)
                relative = "%s%s%s" % (stem, suffix, ext)
            path = os.path.join(workspace_dir, relative)
        resolved.append((output, path))
    return resolved
