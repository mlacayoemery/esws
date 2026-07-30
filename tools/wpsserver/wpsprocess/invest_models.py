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
import shutil
import sys
import tempfile

import pywps
from pywps.app.Common import Metadata
from pywps.inout.basic import UOM
from pywps.inout.literaltypes import ALLOWEDVALUETYPE, AllowedValue

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import easyows
from invest_outputs import (anticipated_outputs, output_is_expected,
                            resolved_output_paths)

import natcap.invest
from natcap.invest import models
from natcap.invest import spec as invest_spec

logger = logging.getLogger("invest_models")

# Args the wrapper sets itself; never exposed as WPS inputs.
_SKIP_ARGS = {"workspace_dir", "n_workers"}

# Inputs this wrapper adds on top of the model's own. They control where results
# are published and must never reach the model's execute().
UPLOAD_FLAG = "upload_results"
DESTINATION_INPUTS = {
    "raster": "destination_wcs",
    "vector": "destination_wfs",
    "table": "destination_http",
}
_WRAPPER_ARGS = {UPLOAD_FLAG} | set(DESTINATION_INPUTS.values())

# Workspace results are published into on a destination server. Stable rather
# than per-job so registered layer names are predictable; results_suffix is what
# keeps successive runs apart.
_RESULTS_WORKSPACE = os.environ.get("WPS_RESULTS_WORKSPACE", "results")

# Where table outputs are uploaded to. A plain file server has no upload
# protocol, so "uploading" a CSV means writing it into a directory that server
# already publishes -- a volume shared between this container and the file
# server. Unset means no writable share is configured, in which case tables are
# reported where the WPS itself serves them from.
_TABLE_UPLOAD_DIR = os.environ.get("WPS_TABLE_UPLOAD_DIR", "")
# Path under the destination server that _TABLE_UPLOAD_DIR appears at, used to
# build the identifier handed back to the client. Matches how the demo registers
# CSV elements: a server-root-relative path, not an absolute URL.
_TABLE_UPLOAD_PATH = os.environ.get("WPS_TABLE_UPLOAD_PATH",
                                    _RESULTS_WORKSPACE)


def _upload_table(path):
    """Copy a table output into the shared directory the file server publishes.

    Returns the destination-relative identifier, or None if no writable share is
    configured or the copy fails -- the caller then falls back to reporting the
    table where the WPS serves it.
    """
    if not _TABLE_UPLOAD_DIR:
        return None
    name = os.path.basename(path)
    try:
        os.makedirs(_TABLE_UPLOAD_DIR, exist_ok=True)
        shutil.copyfile(path, os.path.join(_TABLE_UPLOAD_DIR, name))
    except OSError as exc:
        logger.warning("Could not upload table %s: %s", name, exc)
        return None
    return "%s/%s" % (_TABLE_UPLOAD_PATH.strip("/"), name)


# Licensing. A process runs someone else's model through this wrapper, so both
# licences apply and a client cannot infer either from the response: the wrapper
# is MIT (see LICENSE), the models are InVEST's Apache-2.0.
_LICENSES = (
    ("MIT (ESWS WPS wrapper)",
     "https://github.com/mlacayoemery/esws/blob/master/LICENSE"),
    ("Apache-2.0 (InVEST model implementation)",
     "https://github.com/natcap/invest/blob/main/LICENSE.txt"),
)
# The user guide is published per-language under /latest/ only -- there is no
# version-pinned path, so a 3.20.0 process still documents itself from latest.
_USERGUIDE_BASE = os.environ.get(
    "INVEST_USERGUIDE_BASE",
    "https://storage.googleapis.com/releases.naturalcapitalproject.org"
    "/invest-userguide/latest/en")


def _process_metadata(spec):
    """ows:Metadata for a process: what it may be used under, and its manual.

    WPS 1.0 has no licence field, and ows:Metadata is the only place in a
    ProcessDescription for a typed external reference, so licences are carried as
    links with role set to the OGC licence URN.
    """
    metadata = [Metadata(title, href=href,
                               role="urn:ogc:def:role:OGC:1.0:license")
                for title, href in _LICENSES]
    userguide = getattr(spec, "userguide", None)
    if userguide:
        metadata.append(Metadata(
            "User guide", href="%s/%s" % (_USERGUIDE_BASE, userguide),
            role="urn:ogc:def:role:OGC:1.0:documentation"))
    return metadata


def _upload_inputs():
    """The wrapper's own inputs: whether to upload results, and where to.

    anyURI rather than string -- these are endpoints, and it is the standard
    xmlschema type for one, so a client can treat them as URLs. The values are
    supplied by the client from whatever servers it knows about; the WPS does not
    keep a list of permitted destinations.
    """
    inputs = [pywps.LiteralInput(
        identifier=UPLOAD_FLAG,
        title="Upload model results",
        abstract="Publish this run's outputs to the destination servers below "
                 "in addition to returning them.\n\n[esws:wrapper=1]",
        data_type="boolean",
        min_occurs=0,
        max_occurs=1,
    )]
    for kind, identifier in sorted(DESTINATION_INPUTS.items()):
        inputs.append(pywps.LiteralInput(
            identifier=identifier,
            title="Destination for %s outputs" % kind,
            abstract="Base URL of the server %s outputs are published to when "
                     "%s is set.\n\n[esws:wrapper=1 esws:destination=%s]"
                     % (kind, UPLOAD_FLAG, kind),
            data_type="anyURI",
            min_occurs=0,
            max_occurs=1,
        ))
    return inputs

# Model workspaces are created here. In the container this points at a volume
# shared with GeoServer (so GeoServer can read raster outputs by file path).
_WORKSPACE_ROOT = os.environ.get("WPS_WORKSPACE_ROOT", tempfile.gettempdir())


# A numeric constraint in MODEL_SPEC is a Python expression over `value`, e.g.
# "value > 0" or "2012 <= value <= 2017". These cover every form InVEST 3.20 uses
# except "float(value).is_integer()", which is a kind rather than a bound.
_BOUND = re.compile(r"""^\s*(?:
      value \s* (?P<vop>[<>]=?) \s* (?P<vnum>-?\d+(?:\.\d+)?)
    | (?P<nnum>-?\d+(?:\.\d+)?) \s* (?P<nop>[<>]=?) \s* value
    )\s*$""", re.X)
_CHAIN = re.compile(r"""^\s* (?P<lo>-?\d+(?:\.\d+)?) \s* (?P<lop><=?) \s*
                        value \s* (?P<uop><=?) \s* (?P<hi>-?\d+(?:\.\d+)?) \s*$""",
                    re.X)
# Ratio and percent carry their bounds in the type rather than an expression.
_IMPLICIT_RANGES = {"ratio": (0.0, 1.0), "percent": (0.0, 100.0)}


def _numeric_range(inp, arg_type):
    """(minval, maxval, closure) for a numeric input, or None if unbounded.

    closure is the WPS rangeClosure: whether each end is inclusive. InVEST writes
    strict and non-strict comparisons both ("value > 0" vs "value >= 0"), and the
    difference matters -- a seasonality constant of 0 is rejected by the model.
    """
    low = high = None
    low_open = high_open = False

    expression = getattr(inp, "expression", None) or ""
    chained = _CHAIN.match(expression)
    if chained:
        low, high = float(chained.group("lo")), float(chained.group("hi"))
        low_open = chained.group("lop") == "<"
        high_open = chained.group("uop") == "<"
    elif expression:
        for clause in expression.split(" and "):
            bound = _BOUND.match(clause)
            if not bound:
                continue
            if bound.group("vop"):
                op, number = bound.group("vop"), float(bound.group("vnum"))
            else:
                # "0 <= value" bounds value from below, so the operator flips.
                op = {"<": ">", "<=": ">=", ">": "<", ">=": "<="}[bound.group("nop")]
                number = float(bound.group("nnum"))
            if op.startswith(">"):
                low, low_open = number, op == ">"
            else:
                high, high_open = number, op == "<"

    if low is None and high is None:
        implicit = _IMPLICIT_RANGES.get(arg_type)
        if not implicit:
            return None
        low, high = implicit

    if arg_type == "integer":
        # An integer input's bound is an integer: 2012, not 2012.0.
        low = None if low is None else int(low)
        high = None if high is None else int(high)

    if low is None or high is None:
        # Only one end is bounded, so the closure describes just that end:
        # "value > 0" is an open lower bound with no upper bound at all.
        closure = "open" if (low_open or high_open) else "closed"
    else:
        closure = {(False, False): "closed", (True, True): "open",
                   (True, False): "open-closed",
                   (False, True): "closed-open"}[(low_open, high_open)]
    return low, high, closure


def _numeric_kwargs(inp, arg_type):
    """allowed_values and uoms for a numeric input, as far as MODEL_SPEC says.

    A range lets a client validate before submitting instead of discovering the
    bound in a model traceback, and the unit says what the number means -- "24
    meter" and "24 hectare" are not the same input.
    """
    kwargs = {}
    bounds = _numeric_range(inp, arg_type)
    # Both ends or nothing: pywps 4.6 renders ows:MaximumValue unconditionally, so
    # a half-open range comes out as <ows:MaximumValue>None</ows:MaximumValue>.
    # One-sided bounds travel in the abstract trailer instead (see _literal_input),
    # which is where this wrapper already puts what pywps cannot express.
    if bounds and bounds[0] is not None and bounds[1] is not None:
        low, high, closure = bounds
        kwargs["allowed_values"] = [AllowedValue(
            allowed_type=ALLOWEDVALUETYPE.RANGE,
            minval=low, maxval=high, range_closure=closure)]
    units = getattr(inp, "units", None)
    # "none" is InVEST's dimensionless marker, not a unit worth advertising.
    if units is not None and str(units) not in ("none", ""):
        kwargs["uoms"] = [UOM(str(units))]
    return kwargs


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
    # Numeric bounds go here as well as in ows:AllowedValues, because a half-open
    # range cannot be expressed there (see _numeric_kwargs). A client gets every
    # bound from the trailer, and standards-only clients get the two-sided ones
    # from AllowedValues.
    bounds = _numeric_range(inp, arg_type)
    if bounds:
        low, high, closure = bounds
        if low is not None:
            trailer.append("invest:min=%s" % low)
        if high is not None:
            trailer.append("invest:max=%s" % high)
        if closure != "closed":
            trailer.append("invest:exclusive=%s" % closure)
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
        return pywps.LiteralInput(data_type="float",
                                  **_numeric_kwargs(inp, arg_type), **kwargs)
    if arg_type == "integer":
        return pywps.LiteralInput(data_type="integer",
                                  **_numeric_kwargs(inp, arg_type), **kwargs)
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
        inputs.extend(_upload_inputs())

        outputs = [pywps.LiteralOutput("response",
                                       "Published layers or workspace path",
                                       data_type="string")]
        outputs.append(pywps.LiteralOutput(
            "uploaded",
            "Layers published to the destination servers",
            abstract="Semicolon-separated <kind>:<identifier> entries for what "
                     "was published when upload_results was set. Empty "
                     "otherwise. A client uses it to turn anticipated outputs "
                     "into registered ones.",
            data_type="string"))
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
            metadata=_process_metadata(spec),
            store_supported=True,
            status_supported=True,
        )

    def _collect_args(self, request, spec):
        args = {}
        for inp in spec.inputs:
            arg_id = inp.id
            if arg_id in _SKIP_ARGS or arg_id in _WRAPPER_ARGS:
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
        for output, path in resolved_output_paths(spec, workspace_dir, args,
                                                  primary_only=True):
            filename = output.path
            lower = filename.lower()
            is_raster = isinstance(output, (invest_spec.SingleBandRasterOutput,
                                            invest_spec.RasterOutput)) \
                or lower.endswith(".tif")
            is_vector = isinstance(output, invest_spec.VectorOutput) \
                or lower.endswith((".shp", ".gpkg"))
            if not (is_raster or is_vector):
                continue
            base = os.path.splitext(os.path.basename(path))[0]
            layer = re.sub(r"[^0-9A-Za-z]+", "_", base).strip("_") or "layer"
            uploads["%s:%s" % (ws, layer)] = path
        return uploads

    def _wrapper_arg(self, request, identifier):
        """One of this wrapper's own inputs, or None if it was not supplied.

        pywps parses an anyURI input into a urllib ParseResult rather than a
        string, so it is put back together here -- otherwise it reaches easyows
        as an object and string concatenation fails.
        """
        values = request.inputs.get(identifier) or []
        if not values:
            return None
        value = values[0].data
        if hasattr(value, "geturl"):
            value = value.geturl()
        return value if value not in ("", None) else None

    def _upload_to_destinations(self, request, spec, args):
        """Publish this run's outputs to the client-chosen servers.

        Returns ["<kind>:<identifier>", ...] describing what landed where, which
        goes back in the `uploaded` output. The client reconciles from that
        rather than the WPS calling into it -- nothing here knows or needs to
        know that a dashboard exists.

        Deliberately separate from the per-job publish easyows.Job already does:
        that one exists so a run's results are viewable at all, whereas this is
        the user asking for them to be kept somewhere of their choosing.
        """
        flag = self._wrapper_arg(request, UPLOAD_FLAG)
        if not (flag is True or str(flag).lower() in ("true", "1", "yes")):
            return []

        destinations = {kind: self._wrapper_arg(request, identifier)
                        for kind, identifier in DESTINATION_INPUTS.items()}
        if not any(destinations.values()):
            logger.warning("%s set but no destination given", UPLOAD_FLAG)
            return []

        # One catalog per distinct GeoServer base, so rasters and vectors can go
        # to different servers if the client chose differently.
        catalogs, uploaded = {}, []

        def catalog_for(base):
            if base not in catalogs:
                catalogs[base] = easyows.Catalog(
                    gs_url=base,
                    username=os.environ.get("GEOSERVER_USER", "admin"),
                    password=os.environ.get("GEOSERVER_PASS", "geoserver"),
                    logger=logger)
                try:
                    existing = {w.name for w in catalogs[base].gs_cat.get_workspaces()}
                    if _RESULTS_WORKSPACE not in existing:
                        catalogs[base].gs_cat.create_workspace(
                            _RESULTS_WORKSPACE, "http://esws/%s" % _RESULTS_WORKSPACE)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Could not prepare workspace on %s: %s",
                                   base, str(exc)[:200])
            return catalogs[base]

        for output, path in resolved_output_paths(spec, args["workspace_dir"], args,
                                                  primary_only=True):
            if not os.path.isfile(path):
                continue
            lower = path.lower()
            if lower.endswith((".tif", ".tiff")):
                kind = "raster"
            elif lower.endswith((".shp", ".gpkg")):
                kind = "vector"
            elif lower.endswith(".csv"):
                kind = "table"
            else:
                continue

            base = destinations.get(kind)
            if not base:
                continue

            name = re.sub(r"[^0-9A-Za-z]+", "_",
                          os.path.splitext(os.path.basename(path))[0]).strip("_")
            if kind == "table":
                # A file server has no upload protocol, so the table is copied
                # into a directory it already publishes. Without that share it is
                # offered where it already is: the WPS serves its own outputs.
                uploaded.append("table:%s" % (_upload_table(path)
                                              or os.path.basename(path)))
                continue

            try:
                cat = catalog_for(base)
                # overwrite: the results workspace is stable and layer names come
                # from the output filename, so re-running a model publishes the
                # same names again. Without it GeoServer refuses the store and the
                # run's results never reach the destination.
                if kind == "raster":
                    cat.publish_tif(path, name, _RESULTS_WORKSPACE,
                                    overwrite=True)
                elif lower.endswith(".gpkg"):
                    cat.publish_gpkg(path, name, _RESULTS_WORKSPACE,
                                     overwrite=True)
                else:
                    cat.publish_shp(path, name, _RESULTS_WORKSPACE,
                                    overwrite=True)
            except Exception as exc:  # noqa: BLE001 - report the rest regardless
                logger.warning("Could not publish %s to %s: %s",
                               name, base, str(exc)[:200])
                continue
            uploaded.append("%s:%s:%s" % (kind, _RESULTS_WORKSPACE, name))

        logger.info("Uploaded %d outputs to client destinations", len(uploaded))
        return uploaded

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

        uploaded = self._upload_to_destinations(request, spec, args)
        response.outputs["uploaded"].data = ";".join(uploaded)
        response.outputs["uploaded"].uom = pywps.UOM("unity")

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
        expected = resolved_output_paths(spec, args["workspace_dir"], args)
        filled = 0
        for output, path in expected:
            identifier = _output_identifier(output)
            if identifier not in response.outputs:
                continue

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
