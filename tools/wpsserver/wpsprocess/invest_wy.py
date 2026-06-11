"""Legacy GeoServer-integrated Annual Water Yield WPS process.

This is the original bespoke water-yield process (it returns a ready-to-use
GeoServer WMS GetMap URL and is what the Django dashboard targets). It is kept
for backward compatibility; every InVEST model — including a generic
``annual_water_yield`` — is also exposed by ``invest_models.py``.

Ported to Python 3 / InVEST 3.14.3: the model module
``natcap.invest.hydropower.hydropower_water_yield`` was renamed to
``natcap.invest.annual_water_yield``. The WPS identifier is left at the old
string so existing dashboard requests keep resolving.
"""
import logging
import os.path
import sys
import tempfile

import pywps

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import easyows

import natcap.invest
import natcap.invest.annual_water_yield

LEGACY_IDENTIFIER = 'natcap.invest.hydropower.hydropower_water_yield'


class WebProcess(pywps.Process):
    def __init__(self):
        inputs = [pywps.LiteralInput('workspace_dir',
                                     'GeoServer workspace',
                                     data_type='string'),

                  pywps.LiteralInput('precipitation_path',
                                     'Precipitation',
                                     data_type='string'),

                  pywps.LiteralInput('eto_path',
                                     'Evapotranspiration',
                                     data_type='string'),

                  pywps.LiteralInput('depth_to_root_rest_layer_path',
                                     'Root depth',
                                     data_type='string'),

                  pywps.LiteralInput('pawc_path',
                                     'Plant available water content',
                                     data_type='string'),

                  pywps.LiteralInput('lulc_path',
                                     'Land use land cover',
                                     data_type='string'),

                  pywps.LiteralInput('watersheds_path',
                                     'Watersheds',
                                     data_type='string'),

                  pywps.LiteralInput('biophysical_table_path',
                                     'Biophysical table',
                                     data_type='string'),

                  pywps.LiteralInput('seasonality_constant',
                                     'Seasonality constant',
                                     data_type='float')]

        outputs = [pywps.LiteralOutput('response',
                                       'Output response',
                                       data_type='string')]

        super(WebProcess, self).__init__(
            self._handler,
            identifier=LEGACY_IDENTIFIER,
            title='Water Yield',
            abstract=natcap.invest.annual_water_yield.__doc__,
            version=natcap.invest.__version__,
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):
        logger = logging.getLogger("wps_invest_wy")

        file_logging = False
        for h in logger.handlers:
            if isinstance(h, logging.FileHandler):
                file_logging = True

        if not file_logging:
            fh = logging.FileHandler('/tmp/esws.log')
            logger.addHandler(fh)

        logger.setLevel(logging.DEBUG)

        logger.info("BEGIN CALL TO WPS INVEST_WY")
        logger.debug("DEBUG MODE")

        workspace_uuid = request.inputs["workspace_dir"][0].data

        args = {}
        args_list = ['precipitation_path',
                     'eto_path',
                     'depth_to_root_rest_layer_path',
                     'pawc_path',
                     'lulc_path',
                     'watersheds_path',
                     'biophysical_table_path',
                     'seasonality_constant']

        for a in args_list:
            args[a] = request.inputs[a][0].data

        args["workspace_dir"] = tempfile.mkdtemp(
            prefix="esws-%s-" % str(self.uuid),
            dir=os.environ.get("WPS_WORKSPACE_ROOT", tempfile.gettempdir()))
        os.chmod(args["workspace_dir"], 0o755)
        args["n_workers"] = -1

        for k in args.keys():
            try:
                args[k] = os.path.expanduser(args[k])

            except (AttributeError, TypeError):
                continue

        cat = easyows.Catalog.from_env(logger=logger)

        logger.info("Removing workspace(s)")
        try:
            cat.clean_named_workspace()

        except Exception:
            raise pywps.exceptions.NoApplicableCode("Could not clean workspace(s)")

        logger.info("Making output workspace")
        ws = cat.make_named_workspace(workspace_uuid)

        layer_name = ":".join([ws, "wy"])

        logger.info("Constructing upload template")
        uploads = {
            layer_name: os.path.join(args[u'workspace_dir'], "output", u'watershed_results_wyield.shp')
        }

        logger.info("Constructing WPS job")
        j = easyows.Job(natcap.invest.annual_water_yield.execute,
                        args,
                        uploads,
                        "Call to InVEST WY WPS %s" % ws,
                        0,
                        cat,
                        logger)

        gs_url = os.environ.get("GEOSERVER_PUBLIC_URL",
                                os.environ.get("GEOSERVER_URL",
                                               "http://localhost:8080/geoserver"))
        result_layers = ",".join([cat.cover_name_from_url(args["lulc_path"]), layer_name])
        bbox = "453436.69380764756,4918220.405289317,468316.69380764384,4952570.405289317"
        width = "332"
        height = "768"
        srs = "EPSG:26910"
        result_template = "%s/wms?service=WMS&version=1.1.0&request=GetMap&layers=%s&styles=&bbox=%s&width=%s&height=%s&srs=%s&format=application/openlayers"
        result_url = result_template % (gs_url, result_layers, bbox, width, height, srs)

        logger.info("Running job")
        while j.priority < 3:
            if j.run():
                response.outputs['response'].data = result_url
                response.outputs['response'].uom = pywps.UOM('unity')

                logger.info("END CALL TO WPS INVEST_WY")

                return response

        raise IOError("Job timed out, perhaps some remote data cannot be retrieved.")
