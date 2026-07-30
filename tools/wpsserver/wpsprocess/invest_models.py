"""Generalized pywps middleware exposing *every* InVEST model.

Instead of hand-writing one WPS process per model (see invest_wy.py), this module
introspects InVEST's model registry and each model's ``MODEL_SPEC`` to build a
pywps ``Process`` automatically:

  * inputs  <- MODEL_SPEC.inputs   (typed: number/boolean/option/path/...)
  * execute -> module.execute(args)
  * outputs <- MODEL_SPEC.outputs  (rasters/vectors published to GeoServer)

``wpsserver.py`` discovers the module-level ``get_processes()`` factory and
registers the resulting processes alongside the legacy single-model processes.

References (InVEST >= 3.20):
  - natcap.invest.models.model_id_to_pyname -> {model_id: "natcap.invest.pkg.mod"}
  - <model>.MODEL_SPEC                      -> spec.ModelSpec, whose ``inputs`` and
    ``outputs`` are lists of ``spec.Input`` / ``spec.Output`` objects. Each input
    carries its type as a class attribute ('raster', 'csv', 'number', ...); each
    file output carries its workspace-relative ``path``.
"""
import importlib
import logging
import os
import re
import sys
import tempfile

import pywps

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import easyows

import natcap.invest
from natcap.invest import models
from natcap.invest import spec as invest_spec

logger = logging.getLogger("invest_models")

# Args the wrapper sets itself; never exposed as WPS inputs.
_SKIP_ARGS = {"workspace_dir", "n_workers"}

# Model workspaces are created here. In the container this points at a volume
# shared with GeoServer (so GeoServer can read raster outputs by file path).
_WORKSPACE_ROOT = os.environ.get("WPS_WORKSPACE_ROOT", tempfile.gettempdir())


def _literal_input(inp):
    """Map a single MODEL_SPEC input to a pywps LiteralInput.

    Spatial/file inputs (raster, vector, csv, file, workspace) are exposed as
    strings: a local path inside the container or an OWS URL that easyows.Job
    fetches at run time — matching the existing invest_wy.py convention.
    """
    arg_type = getattr(inp, "type", "")
    title = inp.name or inp.id
    abstract = inp.about or ""
    required = inp.required
    # `required` may be a literal bool or a conditional expression string; only a
    # literal True maps to a mandatory WPS input.
    min_occurs = 1 if required is True else 0

    # Path-like inputs all go out as strings, which loses the distinction
    # between a raster, a vector and a table -- exactly what a client needs in
    # order to offer the right data to choose from. Publish the InVEST type in
    # the abstract as a machine-readable trailer so it survives DescribeProcess
    # and any WPS client can act on it, instead of clients guessing from the
    # identifier or importing natcap.invest themselves.
    #
    # It rides in the abstract rather than ows:Metadata because pywps 4.6 drops
    # metadata from LiteralInput when rendering DescribeProcess -- the element
    # simply never appears in the response.
    trailer = []
    if arg_type:
        trailer.append("invest:type=%s" % arg_type)
    if isinstance(required, str):
        trailer.append("invest:required=%s" % required)
    if trailer:
        abstract = ("%s\n\n[%s]" % (abstract, " ".join(trailer))).strip()

    kwargs = dict(
        identifier=inp.id,
        title=title,
        abstract=abstract,
        min_occurs=min_occurs,
        max_occurs=1,
    )

    if arg_type in ("number", "ratio", "percent"):
        return pywps.LiteralInput(data_type="float", **kwargs)
    if arg_type == "integer":
        return pywps.LiteralInput(data_type="integer", **kwargs)
    if arg_type == "boolean":
        return pywps.LiteralInput(data_type="boolean", **kwargs)
    if arg_type == "option_string":
        # options is a list of spec.Option; the key is the value to submit.
        allowed = [str(o.key) for o in (getattr(inp, "options", None) or [])]
        if allowed:
            return pywps.LiteralInput(data_type="string",
                                      allowed_values=allowed, **kwargs)
        return pywps.LiteralInput(data_type="string", **kwargs)
    # string + path-like types (raster/vector/raster_or_vector/csv/file/workspace)
    return pywps.LiteralInput(data_type="string", **kwargs)


# MODEL_SPEC output class -> the mime type to advertise for it.
_OUTPUT_FORMATS = {
    invest_spec.SingleBandRasterOutput: "image/tiff",
    invest_spec.RasterOutput: "image/tiff",
    invest_spec.VectorOutput: "application/zip",   # shapefile + sidecars
    invest_spec.CSVOutput: "text/csv",
}
_DEFAULT_OUTPUT_FORMAT = "application/octet-stream"


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


def anticipated_outputs(spec, args=None):
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
        expected.append(output)
    return expected


def _output_identifier(output):
    """A WPS-safe identifier for a declared output."""
    ident = output.id or os.path.splitext(os.path.basename(output.path))[0]
    return re.sub(r"[^0-9A-Za-z_.-]+", "_", str(ident)).strip("_") or "output"


def _zip_shapefile(shp_path):
    """Zip a shapefile and its sidecars; returns the archive path or None."""
    import zipfile

    stem = os.path.splitext(shp_path)[0]
    members = [stem + ext for ext in (".shp", ".shx", ".dbf", ".prj", ".cpg",
                                      ".sbn", ".sbx", ".qix")]
    members = [m for m in members if os.path.isfile(m)]
    if not members:
        return None

    archive = stem + ".zip"
    try:
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
            for member in members:
                zf.write(member, os.path.basename(member))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not zip %s: %s", shp_path, str(exc)[:200])
        return None
    return archive


def _complex_outputs(spec):
    """One pywps ComplexOutput per file output the model declares."""
    outputs, seen = [], set()
    for output in anticipated_outputs(spec):
        identifier = _output_identifier(output)
        if identifier in seen:
            continue
        seen.add(identifier)

        mime = _DEFAULT_OUTPUT_FORMAT
        for cls, fmt in _OUTPUT_FORMATS.items():
            if isinstance(output, cls):
                mime = fmt
                break

        abstract = (output.about or "").strip()
        # Conditional outputs cannot be expressed in DescribeProcess -- there is
        # no output-side minOccurs -- so say so in the abstract instead.
        condition = getattr(output, "created_if", True)
        if isinstance(condition, str):
            abstract = ("%s\n\n[invest:created_if=%s]" % (abstract, condition)).strip()

        outputs.append(pywps.ComplexOutput(
            identifier,
            output.path,
            abstract=abstract[:4000],
            supported_formats=[pywps.Format(mime)],
            as_reference=True,
        ))
    return outputs


class InvestProcess(pywps.Process):
    """A pywps Process for one InVEST model, derived from its MODEL_SPEC."""

    def __init__(self, model_id, pyname, module):
        # NB: store only picklable strings — pywps does copy.deepcopy(process)
        # before each execution, and a module object cannot be deep-copied.
        self.model_id = model_id
        self.pyname = pyname
        spec = module.MODEL_SPEC

        inputs = []
        for inp in spec.inputs:
            if inp.id in _SKIP_ARGS:
                continue
            try:
                inputs.append(_literal_input(inp))
            except Exception as exc:  # noqa: BLE001 - never let one arg kill the model
                logger.warning("Could not build input %s for %s: %s",
                               inp.id, model_id, exc)

        # `response` is retained for backward compatibility: it carries the
        # published WMS URLs and existing clients read it. The per-output
        # ComplexOutputs are the real declaration -- WPS supports any number of
        # outputs, and until now every model advertised only this one string.
        outputs = [pywps.LiteralOutput("response",
                                       "Published layers or workspace path",
                                       data_type="string")]
        outputs.extend(_complex_outputs(spec))

        abstract = (module.__doc__ or spec.model_title or model_id or "").strip()

        super().__init__(
            self._handler,
            identifier=model_id,
            title=spec.model_title or model_id,
            abstract=abstract[:4000],
            version=natcap.invest.__version__,
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True,
        )

    def _collect_args(self, request, spec):
        args = {}
        for inp in spec.inputs:
            arg_id = inp.id
            if arg_id in _SKIP_ARGS:
                continue
            if arg_id in request.inputs and len(request.inputs[arg_id]):
                value = request.inputs[arg_id][0].data
                if isinstance(value, str):
                    if value == "":
                        continue
                    value = os.path.expanduser(value)
                args[arg_id] = value
        return args

    def _build_uploads(self, ws, workspace_dir, spec, args=None):
        """The raster/vector layers this run is expected to publish.

        Returns {"ws:layer": path}. When ``args`` is given, each output's
        ``created_if`` condition is evaluated against them, so the result is the
        set the run should actually produce rather than every output the model
        could ever emit. Anything still missing on disk afterwards is skipped by
        easyows.Job.run.
        """
        uploads = {}
        for output in anticipated_outputs(spec, args):
            filename = output.path
            lower = filename.lower()
            is_raster = isinstance(output, (invest_spec.SingleBandRasterOutput,
                                            invest_spec.RasterOutput)) \
                or lower.endswith(".tif")
            is_vector = isinstance(output, invest_spec.VectorOutput) \
                or lower.endswith((".shp", ".gpkg"))
            if not (is_raster or is_vector):
                continue
            path = os.path.join(workspace_dir, filename)
            base = os.path.splitext(os.path.basename(filename))[0]
            layer = re.sub(r"[^0-9A-Za-z]+", "_", base).strip("_") or "layer"
            uploads["%s:%s" % (ws, layer)] = path
        return uploads

    def _handler(self, request, response):
        logger.info("BEGIN InVEST WPS model=%s", self.model_id)

        module = importlib.import_module(self.pyname)
        spec = module.MODEL_SPEC

        args = self._collect_args(request, spec)
        workspace_dir = tempfile.mkdtemp(prefix="esws-%s-" % self.model_id,
                                         dir=_WORKSPACE_ROOT)
        os.chmod(workspace_dir, 0o755)
        args["workspace_dir"] = workspace_dir
        args["n_workers"] = -1

        cat = easyows.Catalog.from_env(logger=logger)
        try:
            cat.clean_named_workspace()
        except Exception:  # noqa: BLE001
            raise pywps.exceptions.NoApplicableCode("Could not clean GeoServer workspace(s)")
        ws = cat.make_named_workspace(str(self.uuid))

        uploads = self._build_uploads(ws, args["workspace_dir"], spec, args)

        job = easyows.Job(module.execute, args, uploads,
                          "InVEST %s WPS job %s" % (self.model_id, ws),
                          0, cat, logger)

        published = []
        ran = False
        while job.priority < 3:
            if job.run():
                ran = True
                # Report only layers that actually made it into GeoServer:
                # the file existing is not enough, since publishing it may
                # still have been refused (see easyows.Job.failed_uploads).
                published = [ln for ln, p in uploads.items()
                             if os.path.exists(p)
                             and ln.split(":")[-1] not in job.failed_uploads]
                break

        if not ran:
            # Job.run() returns False when it could not resolve the inputs --
            # typically a remote OWS reference that would not download. Falling
            # out of the loop used to be reported as ProcessSucceeded with no
            # outputs, so a job that never executed looked like a success.
            raise pywps.exceptions.NoApplicableCode(
                "Could not resolve all inputs for %s; the model did not run"
                % self.model_id)

        gs_url = os.environ.get(
            "GEOSERVER_PUBLIC_URL",
            os.environ.get("GEOSERVER_URL", "http://localhost:8080/geoserver"))
        layer_urls = [
            "%s/wms?service=WMS&version=1.1.0&request=GetMap&layers=%s"
            % (gs_url, ln) for ln in published
        ]

        response.outputs["response"].data = (
            " ; ".join(layer_urls) if layer_urls else args["workspace_dir"])
        response.outputs["response"].uom = pywps.UOM("unity")

        # Populate the declared per-output references for whatever this run
        # actually produced. DescribeProcess has to advertise every output the
        # model can emit, since WPS cannot express a conditional output, so the
        # ones whose created_if did not hold are simply left unset.
        expected = anticipated_outputs(spec, args)
        filled = 0
        for output in expected:
            identifier = _output_identifier(output)
            if identifier not in response.outputs:
                continue
            path = os.path.join(args["workspace_dir"], output.path)

            # Must be a regular file. Some declared outputs are directories on
            # disk -- taskgraph_cache/taskgraph.db is declared as a file but
            # taskgraph creates a directory there -- and attaching one fails
            # inside pywps at response-construction time with IsADirectoryError,
            # which aborts the entire ExecuteResponse rather than that output.
            if not os.path.isfile(path):
                continue

            if path.lower().endswith(".shp"):
                # A shapefile is a set of sidecar files; delivering just the
                # .shp would be useless, so ship the set as the advertised zip.
                path = _zip_shapefile(path)
                if path is None:
                    continue

            try:
                response.outputs[identifier].file = path
                filled += 1
            except Exception as exc:  # noqa: BLE001 - one output must not fail the job
                logger.warning("Could not attach output %s: %s",
                               identifier, str(exc)[:200])

        logger.info("END InVEST WPS model=%s anticipated=%d produced=%d published=%d",
                    self.model_id, len(expected), filled, len(published))
        return response


def get_processes():
    """Build one InvestProcess per importable model in the InVEST registry."""
    processes = []
    skipped = []
    for model_id, pyname in models.model_id_to_pyname.items():
        try:
            module = importlib.import_module(pyname)
            if not (hasattr(module, "MODEL_SPEC") and hasattr(module, "execute")):
                skipped.append((model_id, "no MODEL_SPEC/execute"))
                continue
            processes.append(InvestProcess(model_id, pyname, module))
        except Exception as exc:  # noqa: BLE001 - skip + log, never abort startup
            skipped.append((model_id, repr(exc)))

    logger.info("Exposed %d InVEST models via WPS", len(processes))
    for model_id, reason in skipped:
        logger.warning("Skipped InVEST model %s: %s", model_id, reason)
    return processes
