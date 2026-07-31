import base64
import logging
import os

import geoserver.catalog

# Namespace URIs for workspaces this code creates. A WFS response carries the
# URI, so making it meaningful is what puts provenance in the data.
NAMESPACE_BASE = os.environ.get("ESWS_NAMESPACE_BASE", "http://esws.unige.ch")
# Column a series table carries its run time in.
TIME_COLUMN = "esws_run_time"
from crs_identify import (describe_crs, drop_unresolvable_authority,
                          identify_epsg)
import uuid

import urllib

import sys
if sys.version_info.major == 2:
    import urllib
    urlretrieve = urllib.URLopener().retrieve
    unquote = urllib.unquote

else:
    from urllib.request import urlretrieve
    from urllib.parse import unquote

import re
import tempfile
import zipfile

#import ogr

class MissingResource(Exception):
    pass


class _GeoServer3Catalog(geoserver.catalog.Catalog):
    """geoserver-restconfig with the trailing slashes GeoServer 3 rejects.

    The client (2.0.16, the latest release) builds some REST paths with a
    trailing slash -- ``create_workspace`` posts to ``/rest/namespaces/``.
    GeoServer 2.x tolerated that; 3.0 routes strictly and answers::

        404 {"detail":"No endpoint POST /geoserver/rest/namespaces/."}

    while the identical request to ``/rest/namespaces`` returns 201. Normalising
    the path here fixes every call site at once rather than only the workspace
    creation that happens to fail first. Harmless against GeoServer 2.x, which
    accepts the path either way.
    """

    def http_request(self, url, data=None, method='get', headers=None):
        head, sep, query = url.partition('?')
        if head.endswith('/'):
            url = head.rstrip('/') + sep + query
        return super().http_request(url, data=data, method=method,
                                    headers=headers or {})

class Catalog:
    def __init__(self,
                 gs_url = "http://localhost:8080/geoserver",
                 username = "admin",
                 password = "geoserver",
                 ws_prefix = "user-",
                 logger = logging.getLogger('easyows')):

        self.logger = logger
        self.gs_url = gs_url
        self.username = username
        self.password = password
        self.gs_cat = self.get_cat(self.gs_url + "/rest")
        self.ws_prefix = ws_prefix

        self.ows_cache = {}

        # Layers published but left unservable because their CRS could not be
        # identified. Kept so a bulk load can report the shortfall rather than
        # claiming every layer it created is usable.
        self.unservable = []

    @classmethod
    def from_env(cls, logger=logging.getLogger('easyows')):
        "Builds a Catalog from GEOSERVER_* environment variables (container config)"
        return cls(
            gs_url=os.environ.get("GEOSERVER_URL", "http://localhost:8080/geoserver"),
            username=os.environ.get("GEOSERVER_USER", "admin"),
            password=os.environ.get("GEOSERVER_PASS", "geoserver"),
            ws_prefix=os.environ.get("WPS_WORKSPACE_PREFIX", "esws-"),
            logger=logger,
        )

    def get_cat(self, rest_url):
        "Creates connection to catalog"
        self.logger.debug("Connecting to catalog %s" % rest_url)
        
        return _GeoServer3Catalog(rest_url,
                                  username = self.username,
                                  password = self.password)

    def make_named_workspace(self, ws_uuid=None):
        "Creates workspace with UUID and returns name"

        if ws_uuid is None:
            workspace_name = self.ws_prefix + str(uuid.uuid1())
        else:
            workspace_name = self.ws_prefix + ws_uuid

        self.logger.debug("Attempting to create workspace %s" % workspace_name)

        try:
            return self.gs_cat.create_workspace(workspace_name).name

        except TypeError:
            #gsconfig 2.0.1
            return self.gs_cat.create_workspace(workspace_name, workspace_name).name

    def clean_named_workspace(self,
                              f = None):

        if f is None:
            def f(s):
                return s[:5] == self.ws_prefix

        self.logger.debug("Cleaning workspace")

        for ws in self.gs_cat.get_workspaces():
            if f(ws.name):
                self.logger.debug("%s" % ws.name)
                self.gs_cat.delete(ws, recurse=True)
        
    
    def publish_shp(self,
                    shp_path,
                    shp_name = None,
                    gs_workspace = None,
                    overwrite = False):
        """Publishes a Shapefile to a workspace

        overwrite replaces a store of the same name; without it GeoServer
        rejects the request outright ("There is already a store named ..."), so
        publishing the same layer twice -- a model re-run, a reloaded demo --
        silently produces nothing.
        """

        if gs_workspace is None:
            gs_workspace = self.make_named_workspace()

        data_store_path, _ = os.path.splitext(shp_path)
        if shp_name is None:
            shp_name = os.path.basename(data_store_path)

        shapefile_plus_sidecars = {}
        for key in ["shp", "shx", "prj", "dbf"]:
            shapefile_plus_sidecars[key] = ".".join([data_store_path, key])

##        driver = ogr.GetDriverByName("ESRI Shapefile")
##        data = driver.Open(shp_path, 1)
##        layer = data.GetLayer()
##        for feature in layer:
##            feature.GetGeomRef().GetEnvelope()

        created = self.gs_cat.create_featurestore(shp_name,
                                                  workspace = gs_workspace,
                                                  data = shapefile_plus_sidecars,
                                                  overwrite = overwrite)
        self.ensure_srs(shp_name, gs_workspace, shp_path)
        return created


    def publish_tif(self,
                    tif_path,
                    tif_name = None,
                    gs_workspace = None,
                    overwrite = False):
        "Publishes a GeoTIFF to a workspace. See publish_shp for overwrite."

        if gs_workspace is None:
            gs_workspace = self.make_named_workspace()

        data_store_path, _ = os.path.splitext(tif_path)
        if tif_name is None:
            tif_name = os.path.basename(data_store_path)

        tiffdata = { 'tiff' : tif_path }

        # upload_data=True uploads the GeoTIFF to GeoServer over REST, so the
        # (separate) GeoServer container does not need filesystem access to the
        # WPS workspace.
        created = self.gs_cat.create_coveragestore(name = tif_name,
                                                   path = tif_path,
                                                   workspace = self.gs_cat.get_workspace(gs_workspace),
                                                   layer_name = tif_name,
                                                   upload_data = True,
                                                   overwrite = overwrite)
        self.ensure_srs(tif_name, gs_workspace, tif_path)
        return created

    def publish_gpkg(self,
                     gpkg_path,
                     gpkg_name = None,
                     gs_workspace = None,
                     overwrite = False):
        "Publishes a GeoPackage by translating it to a Shapefile with GDAL first"

        from osgeo import gdal

        if gpkg_name is None:
            gpkg_name = os.path.splitext(os.path.basename(gpkg_path))[0]

        tmp_dir = tempfile.mkdtemp(prefix="esws-gpkg-")
        shp_path = os.path.join(tmp_dir, gpkg_name + ".shp")

        self.logger.debug("Translating %s to %s" % (gpkg_path, shp_path))
        gdal.VectorTranslate(shp_path, gpkg_path, format="ESRI Shapefile")

        return self.publish_shp(shp_path, gpkg_name, gs_workspace, overwrite)

    def layer_url(self,layer_name):
        template = self.gs_url + "/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=%s&outputFormat=SHAPE-ZIP"

        return template % layer_name

    def layer_name_from_url(self,layer_url):
        if not layer_url[:4].lower() == "http":
            raise ValueError("Not a vaild URL")

        if layer_url[4] == "%":
            self.logger.debug("Found quoted URL")
            return re.search("typeName=(.+)&", unquote(layer_url)).group(1)
        else:
            return re.search("typeName=(.+)&", layer_url).group(1)

    def cover_url(self,layer_name):
        template = self.gs_url + "/ows?service=WCS&version=2.0.0&request=GetCoverage&coverageId=%s&format=image%%2Fgeotiff"

        return template % layer_name

    def cover_name_from_url(self, cover_url):
        if not cover_url[:4].lower() == "http":
            raise ValueError("Not a vaild URL")

        if cover_url[4] == "%":
            self.logger.debug("Found quoted URL")
            return re.search("coverageId=(.+)&", unquote(cover_url)).group(1)
        else:
            return re.search("coverageId=(.+)&", cover_url).group(1)

    def ensure_srs(self, name, workspace, path):
        """Declare a layer's CRS if GeoServer could not work it out itself.

        A layer GeoServer publishes without an SRS is left disabled and answers
        every request with "Could not locate coverage" / "defaultCRS should not be
        null", so publishing appears to succeed and the layer is unusable. Returns
        True if the layer is servable afterwards.
        """
        try:
            resources = self.gs_cat.get_resources(stores=[name],
                                                  workspaces=[workspace])
        except Exception as exc:  # noqa: BLE001
            self.logger.debug("Could not inspect %s: %s" % (name, exc))
            return True

        ok = True
        for resource in resources or []:
            if getattr(resource, "projection", None):
                continue
            epsg = identify_epsg(path, min_confidence=_CRS_MIN_CONFIDENCE,
                                 logger=self.logger)
            if not epsg:
                self.logger.warning(
                    "%s:%s cannot be served: %s, which resolves to no CRS code"
                    % (workspace, resource.name, describe_crs(path, self.logger)))
                self.unservable.append("%s:%s" % (workspace, resource.name))
                ok = False
                continue
            resource.projection = epsg
            # The file's own definition is the right one; FORCE_DECLARED just
            # names it in terms GeoServer can use, without reprojecting.
            resource.projection_policy = "FORCE_DECLARED"
            resource.enabled = True
            self.gs_cat.save(resource)
            self.logger.info("Declared %s for %s:%s (CRS match threshold %d%%)"
                             % (epsg, workspace, resource.name,
                                _CRS_MIN_CONFIDENCE))
        return ok

    # --- PostGIS -----------------------------------------------------------
    #
    # The PostGIS data store ships with GeoServer; the JDBC driver does not, and
    # is added in docker/Dockerfile.geoserver. On this side, GDAL needs its
    # PostgreSQL driver (conda's libgdal-pg) or OGR can only write .sql dumps.

    def postgis_params(self):
        """Connection settings for the PostGIS both ends share."""
        return {
            "host": os.environ.get("POSTGIS_HOST", "postgis"),
            "port": os.environ.get("POSTGIS_PORT", "5432"),
            "database": os.environ.get("POSTGIS_DB", "esws"),
            "user": os.environ.get("POSTGIS_USER", "esws"),
            "passwd": os.environ.get("POSTGIS_PASS", "esws"),
            "schema": os.environ.get("POSTGIS_SCHEMA", "public"),
            "dbtype": "postgis",
        }

    def postgis_uri(self):
        """The same settings as an OGR connection string."""
        p = self.postgis_params()
        return ("PG:host=%(host)s port=%(port)s dbname=%(database)s "
                "user=%(user)s password=%(passwd)s" % p)

    def load_into_postgis(self, vector_path, table, append=False,
                          extra_fields=None):
        """Copy a vector file into a PostGIS table, returning the table name.

        ``append`` adds to an existing table rather than replacing it, which is
        what a series does run after run. ``extra_fields`` are constant values
        written onto every feature -- the run time, for a series.
        """
        from osgeo import gdal, ogr

        source = gdal.OpenEx(vector_path)
        if source is None or not source.GetLayerCount():
            raise ValueError("%s has no layers to publish" % vector_path)

        # PROMOTE_TO_MULTI because a shapefile mixes single and multi geometries
        # in one layer where PostGIS wants one type per column.
        options = ["-nln", table, "-lco", "GEOMETRY_NAME=geom",
                   "-lco", "FID=fid", "-nlt", "PROMOTE_TO_MULTI"]
        options += ["-append"] if append else ["-overwrite"]

        self.logger.debug("Loading %s into PostGIS table %s" % (vector_path, table))
        result = gdal.VectorTranslate(self.postgis_uri(), source,
                                      options=options)
        if result is None:
            raise RuntimeError("could not load %s into PostGIS" % vector_path)
        result = None  # flush

        if extra_fields:
            self._stamp_rows(table, extra_fields)
        return table

    def _stamp_rows(self, table, values):
        """Write constant values onto the rows that have none yet.

        Used for the run time on a series table: OGR copies the file's own
        fields, and this is how the rows learn which run they came from.
        """
        from osgeo import ogr

        connection = ogr.Open(self.postgis_uri(), 1)
        if connection is None:
            raise RuntimeError("could not connect to PostGIS to stamp %s" % table)
        for column, value in values.items():
            connection.ExecuteSQL(
                'ALTER TABLE "%s" ADD COLUMN IF NOT EXISTS "%s" timestamptz'
                % (table, column))
            connection.ExecuteSQL(
                'UPDATE "%s" SET "%s" = %s WHERE "%s" IS NULL'
                % (table, column, "'%s'" % value, column))
        connection = None

    def ensure_postgis_store(self, workspace, store="esws_pg"):
        """A PostGIS store in ``workspace``, created if it is not there."""
        try:
            existing = self.gs_cat.get_store(store, workspace)
        except Exception:  # noqa: BLE001 - absent stores raise rather than return
            existing = None
        if existing is not None:
            return existing
        self.logger.debug("Creating PostGIS store %s in %s" % (store, workspace))
        return self._create_postgis_store_rest(workspace, store)

    def _create_postgis_store_rest(self, workspace, store):
        """Create the store over REST.

        geoserver-restconfig's create_datastore builds an empty shell and expects
        the caller to fill in connection parameters one at a time; posting the
        whole thing is one call and fails loudly if the connection is wrong.
        """
        import json as _json
        import urllib.request

        body = {"dataStore": {"name": store, "connectionParameters": {
            "entry": [{"@key": key, "$": str(value)}
                      for key, value in self.postgis_params().items()]}}}
        request = urllib.request.Request(
            "%s/rest/workspaces/%s/datastores" % (self.gs_url, workspace),
            data=_json.dumps(body).encode(), method="POST")
        request.add_header("Content-Type", "application/json")
        request.add_header("Authorization", "Basic " + base64.b64encode(
            ("%s:%s" % (self.username, self.password)).encode()).decode())
        with urllib.request.urlopen(request, timeout=120) as response:
            if response.status not in (200, 201):
                raise RuntimeError("could not create PostGIS store: %s"
                                   % response.status)
        # restconfig caches the catalog it has already read, so a store created
        # behind its back is invisible to the same session until the cache is
        # dropped -- publishing then fails on a store that plainly exists.
        self.gs_cat.reset()
        return self.gs_cat.get_store(store, workspace)

    def publish_postgis(self, vector_path, layer_name, gs_workspace,
                        store="esws_pg", append=False, time_value=None,
                        overwrite=False):
        """Publish a vector through PostGIS rather than as a shapefile.

        The table is named for the layer, so a series appends run after run into
        one table and one layer, while a per-run workspace gets a table of its
        own.
        """
        self.make_workspace(gs_workspace)
        self.ensure_postgis_store(gs_workspace, store)

        # The table is named for the layer, so a series appends into one table
        # run after run while a per-run workspace gets a table of its own.
        extra = {TIME_COLUMN: time_value} if time_value else None
        self.load_into_postgis(vector_path, layer_name, append=append,
                               extra_fields=extra)

        try:
            published = self.gs_cat.get_layer("%s:%s" % (gs_workspace, layer_name))
        except Exception:  # noqa: BLE001
            published = None
        if published is not None:
            # Already published: the table now holds this run's rows too.
            return published

        # GeoServer will not publish a feature type without a CRS, and PostGIS
        # gives it only an SRID. The same identification the file publishing path
        # uses answers it, including for the definitions GeoServer cannot name
        # itself -- see crs_identify.
        native_crs = identify_epsg(vector_path, logger=self.logger)
        if not native_crs:
            raise RuntimeError(
                "%s has no CRS that can be declared, so PostGIS cannot publish it"
                % os.path.basename(vector_path))

        store_object = self.gs_cat.get_store(store, gs_workspace)
        return self.gs_cat.publish_featuretype(layer_name, store_object,
                                               native_crs=native_crs,
                                               srs=native_crs)

    # --- raster series (ImageMosaic) ---------------------------------------

    def publish_mosaic_granule(self, tif_path, layer_name, gs_workspace,
                               time_value):
        """Add one run's raster to a time series, creating the series if new.

        An ImageMosaic is a directory of files plus an index; GeoServer reads the
        time of each granule out of its filename, so the run time is written
        there rather than kept in a sidecar. The directory lives on a volume both
        containers see, since GeoServer opens the granules itself.
        """
        import shutil

        root = os.environ.get("ESWS_MOSAIC_ROOT", "/mosaics")
        directory = os.path.join(root, gs_workspace, layer_name)
        os.makedirs(directory, exist_ok=True)

        stamp = re.sub(r"[^0-9TZ]", "", str(time_value).replace("-", "")
                       .replace(":", ""))
        granule = os.path.join(directory, "%s_%s.tif" % (layer_name, stamp))
        shutil.copyfile(tif_path, granule)

        first = not os.path.exists(os.path.join(directory, "indexer.properties"))
        if first:
            self._write_mosaic_config(directory, layer_name)

        self.make_workspace(gs_workspace)
        if first:
            return self._create_mosaic_store(gs_workspace, layer_name, directory)
        return self._harvest_granule(gs_workspace, layer_name, granule)

    def _write_mosaic_config(self, directory, layer_name):
        """indexer and timeregex, which are how a mosaic learns to be a series.

        Without TimeAttribute the directory is just a mosaic of tiles laid out in
        space; with it, granules that cover the same ground are separate points in
        time rather than overlapping neighbours.
        """
        with open(os.path.join(directory, "indexer.properties"), "w") as handle:
            handle.write(
                "TimeAttribute=time\n"
                "Schema=*the_geom:Polygon,location:String,time:java.util.Date\n"
                "PropertyCollectors=TimestampFileNameExtractorSPI[timeregex](time)\n"
                "Name=%s\n"
                "AbsolutePath=true\n" % layer_name)
        with open(os.path.join(directory, "timeregex.properties"), "w") as handle:
            # 20260731T093000Z, as written by publish_mosaic_granule.
            handle.write("regex=[0-9]{8}T[0-9]{6}Z,format=yyyyMMdd'T'HHmmss'Z'\n")

    def _rest(self, path, method="GET", data=None, ctype="application/json"):
        import urllib.request

        request = urllib.request.Request("%s/rest/%s" % (self.gs_url, path),
                                         data=data, method=method)
        request.add_header("Content-Type", ctype)
        request.add_header("Authorization", "Basic " + base64.b64encode(
            ("%s:%s" % (self.username, self.password)).encode()).decode())
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as error:
            # GeoServer explains itself in the body; a bare status turns a fixable
            # mistake into a guess.
            detail = error.read().decode("utf-8", "replace")[:400]
            raise RuntimeError("GeoServer %s on %s: %s"
                               % (error.code, path, detail.strip())) from None

    def _create_mosaic_store(self, workspace, layer_name, directory):
        """Register the directory as an ImageMosaic coverage store."""
        status, _body = self._rest(
            "workspaces/%s/coveragestores/%s/external.imagemosaic"
            % (workspace, layer_name),
            method="PUT", data=("file://" + directory).encode(),
            ctype="text/plain")
        self.gs_cat.reset()
        # The mosaic serves one coverage; make sure its time dimension is on.
        self.enable_coverage_time(workspace, layer_name)
        return status in (200, 201, 202)

    def _harvest_granule(self, workspace, layer_name, granule):
        """Tell an existing mosaic to pick up a newly written file."""
        status, _body = self._rest(
            "workspaces/%s/coveragestores/%s/remote.imagemosaic"
            % (workspace, layer_name),
            method="POST", data=("file://" + granule).encode(),
            ctype="text/plain")
        return status in (200, 201, 202)

    def enable_coverage_time(self, workspace, layer_name):
        """Turn on the time dimension of a mosaic's coverage."""
        import json as _json

        body = {"coverage": {"enabled": True, "metadata": {"entry": [{
            "@key": "time",
            "dimensionInfo": {"enabled": True, "presentation": "LIST",
                              "units": "ISO8601",
                              "defaultValue": {"strategy": "MAXIMUM"}}}]}}}
        try:
            status, _ = self._rest(
                "workspaces/%s/coveragestores/%s/coverages/%s.json"
                % (workspace, layer_name, layer_name),
                method="PUT", data=_json.dumps(body).encode())
            return status in (200, 201)
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("Could not enable time on %s:%s: %s"
                                % (workspace, layer_name, str(exc)[:160]))
            return False

    def enable_time_dimension(self, workspace, layer, attribute=TIME_COLUMN,
                              store="esws_pg"):
        """Expose a feature type's run-time column as its time dimension.

        This is what makes a series addressable: with it, a client asks for
        `&time=...` to get one run, or omits it and GeoServer serves the most
        recent -- which is exactly what a downstream job wanting "whatever was
        produced last" needs, with no resolution logic anywhere.
        """
        import json as _json
        import urllib.request

        body = {"featureType": {"enabled": True, "metadata": {"entry": [{
            "@key": "time",
            "dimensionInfo": {"enabled": True, "attribute": attribute,
                              "presentation": "LIST",
                              "units": "ISO8601",
                              "defaultValue": {"strategy": "MAXIMUM"}}}]}}}
        url = ("%s/rest/workspaces/%s/datastores/%s/featuretypes/%s.json"
               % (self.gs_url, workspace, store, layer))
        request = urllib.request.Request(url, data=_json.dumps(body).encode(),
                                         method="PUT")
        request.add_header("Content-Type", "application/json")
        request.add_header("Authorization", "Basic " + base64.b64encode(
            ("%s:%s" % (self.username, self.password)).encode()).decode())
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.status in (200, 201)

    def make_workspace(self, name, uri=None):
        """A workspace, created if absent, with a namespace URI that says whose
        it is -- a WFS response carries that URI, so it is where provenance ends
        up being readable from the data itself."""
        try:
            if self.gs_cat.get_workspace(name) is not None:
                return name
        except Exception:  # noqa: BLE001
            pass
        self.gs_cat.create_workspace(name, uri or (NAMESPACE_BASE + "/" + name))
        self.gs_cat.reset()
        return name

    def store_exists(self, name, workspace):
        return len(self.gs_cat.get_stores(names=name, workspaces=workspace)) > 0


# How sure the CRS match has to be before a layer's SRS is declared for it.
# Lowering this makes more sample data servable at the cost of accepting a guess:
# two of the InVEST sample rasters carry an unnamed projection whose best matches
# are three different UTM 21S datums at 70% apiece, and declaring one of them
# would place the data tens of metres from where it belongs.
_CRS_MIN_CONFIDENCE = int(os.environ.get("EASYOWS_CRS_MIN_CONFIDENCE", "90"))


class Job:
    def __init__(self,
                 process,
                 args,
                 uploads,
                 msg,
                 priority=0,                 
                 catalog = Catalog(),                 
                 logger = logging.getLogger('easyows'),
                 on_localised = None):
        """on_localised(args, sources) runs once remote arguments are downloaded.

        sources maps each argument to the URL it arrived as, which is what a
        downloaded file's own internal references are relative to. Optional, and
        errors in it are logged rather than raised.
        """

        self.logger = logger
        self.on_localised = on_localised

        logger.debug("Construting job with args %s" % str(args))
        
        self.catalog = catalog
        self.priority = priority
        self.process = process
        self.args = args
        self.uploads = uploads
        self.msg = msg
        # {layer_name: reason} for outputs the model produced but GeoServer
        # would not accept; reported rather than raised, see run().
        self.failed_uploads = {}


    def are_local_parameters(self):
        "Boolean of whether all the arguments to the process are local"

        for key, value in self.args.items():
            if isinstance(value, str):
                self.logger.debug("Checking locality of %s" % value)

                if value[:4].lower() == "http":
                    return False

        return True

    def get_remote_parameters(self,
                              ows_cache = None,
                              prefix = "esws-"):
        "Get any remote parameters with option cache"

        if ows_cache is None:
            self.logger.debug("Trying catalog cache %i" % id(self.catalog.ows_cache))
            ows_cache=self.catalog.ows_cache
        else:
            self.logger.debug("Checking given OWS cache")

        failure = False
        failure_list = []
        for key, value in self.args.items():
            try:
                if isinstance(value, str):
                    if value[:4].lower() == "http":
                        self.logger.debug("Found remote parameter %s" % value)
                        if value[4] == "%":
                            self.logger.debug("Found quoted URL")
                            value = unquote(value)
                        #print value
                        if "service=WFS" in value:
                            self.logger.debug("Detected WFS service")
                            if value in ows_cache:
                                self.args[key] = ows_cache[value]
                                self.logger.debug("Assigned %s cached %s" % (key, self.args[key]))

                            else:
                                workspace, name = self.catalog.layer_name_from_url(value).split(":")
                                self.logger.debug("Checking for %s in %s" % (name,workspace))
                                if self.catalog.store_exists(name, workspace):
                                    self.logger.debug("Remote resource exists")
                                else:
                                    self.logger.debug("Remote resource does not exist")
                                    raise MissingResource("Missing resource")
                                
                                try:
                                    _, tmp_path = tempfile.mkstemp(suffix=".zip", prefix=prefix)
                                    urlretrieve(value, tmp_path)

                                    tmp_dir = tempfile.mkdtemp(prefix=prefix)
                                    zipfile.ZipFile(tmp_path, 'r').extractall(tmp_dir)
                                    drop_unresolvable_authority(tmp_dir,
                                                                self.logger)

                                    for wfs_file in os.listdir(tmp_dir):
                                        if wfs_file.endswith(".shp"):
                                            self.args[key] = os.path.join(tmp_dir,wfs_file)
                                            self.logger.debug("Assigned %s %s" % (key, self.args[key]))
                                            ows_cache[value] = self.args[key]
                                            
                                except zipfile.BadZipfile:
                                    self.logger.error("Missing %s" % value)
                                    raise MissingResource("Missing resource")

                        elif "service=WCS" in value:
                            self.logger.debug("Detected WCS service")
                            if value in ows_cache:
                                self.args[key] = ows_cache[value]
                                self.logger.debug("Assigned %s cached %s" % (key, self.args[key]))

                            else:
                                workspace, name = self.catalog.cover_name_from_url(value).split(":")
                                self.logger.debug("Checking for %s in %s" % (name,workspace))                            
                                if self.catalog.store_exists(name, workspace):
                                    self.logger.debug("Remote resource exists")
                                else:
                                    self.logger.debug("Remote resource does not exist")
                                    raise MissingResource("Missing resource")
                                
                                _, tmp_path = tempfile.mkstemp(suffix=".tif", prefix=prefix)
                                urlretrieve(value, tmp_path)
                                self.args[key] = tmp_path
                                self.logger.debug("Assigned %s %s" % (key, self.args[key]))
                                ows_cache[value] = self.args[key]

                        else:
                            #self.logger.error("Unknown protocol for %s" % value)
                            #raise ValueError("Unknown protocol for %s" % value)

                            self.logger.debug("Trying simple HTTP get")
                            if value in ows_cache:
                                self.args[key] = ows_cache[value]
                                self.logger.debug("Assigned %s cached %s" % (key, self.args[key]))

                            else:                               
                                _, tmp_path = tempfile.mkstemp(suffix=".csv", prefix=prefix)
                                urlretrieve(value, tmp_path)
                                self.args[key] = tmp_path
                                self.logger.debug("Assigned %s %s" % (key, self.args[key]))
                                ows_cache[value] = self.args[key]                            
                            
            except MissingResource:
                self.logger.debug("Continuing after missing resource detected")
                failure = True
                failure_list.append("%s:%s" % (workspace, name))
                
        if failure:
            self.logger.debug("Missing resources(s) %s" % str(failure_list))
            raise MissingResource("Missing resource")
        
    def run(self, increment=1):
        self.logger.debug("Trying %s" % self.msg)
        
        self.priority += increment
        self.logger.debug("Job priority %i" % self.priority)        

        if self.are_local_parameters():
            self.logger.debug("Local parameters detected")
            self.process(self.args)

            for layer_name, layer_path in self.uploads.items():
                if not os.path.exists(layer_path):
                    self.logger.warning("Skipping missing output %s" % layer_path)
                    continue
                self.logger.debug("Uploading %s" % layer_name)
                ws, layer_name = layer_name.split(":")
                try:
                    if layer_path.lower().endswith(".shp"):
                        self.catalog.publish_shp(layer_path, layer_name, ws)

                    elif layer_path.lower().endswith(".tif"):
                        self.catalog.publish_tif(layer_path, layer_name, ws)

                    elif layer_path.lower().endswith(".gpkg"):
                        self.catalog.publish_gpkg(layer_path, layer_name, ws)

                    else:
                        self.logger.warning("Skipping unsupported output type %s"
                                            % layer_path)
                except Exception as exc:  # noqa: BLE001
                    # One unpublishable output must not fail a model run that
                    # otherwise succeeded. Several models emit convolution
                    # kernels (search_kernel, area_kernel, gaussian_kernel) as
                    # intermediate rasters; they carry no CRS, so GeoServer
                    # answers 500 when asked to make a coverage of them.
                    self.failed_uploads[layer_name] = str(exc)
                    self.logger.warning("Could not publish %s: %s",
                                        layer_name, str(exc)[:200])
            return True

        else:
            self.logger.debug("Downloading remote parameters")
            # get_remote_parameters replaces each URL with the local path it was
            # downloaded to, so the URLs have to be kept first: a downloaded file
            # may need to know where it came from -- an InVEST table's references
            # are relative to the table's own directory on the remote server.
            sources = {key: value for key, value in self.args.items()
                       if isinstance(value, str) and value[:4].lower() == "http"}
            try:
                self.get_remote_parameters()

            except MissingResource:
                self.logger.debug("Could not download all remote parameters")

            except IOError:
                self.logger.debug("Could not download all remote parameters")

            else:
                if self.on_localised is not None:
                    try:
                        self.on_localised(self.args, sources)
                    except Exception as exc:  # noqa: BLE001 - advisory only
                        self.logger.warning("Post-download hook failed: %s", exc)


        return False
