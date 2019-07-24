import logging
import pywps

import sys
import os.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import easyows
import tempfile

import natcap.invest.hydropower.hydropower_water_yield

class WebProcess(pywps.Process):
    def __init__(self):
        inputs = [pywps.LiteralInput('workspace_dir',
                                     'GeoServer workspace',
                                     data_type='string'),

                  pywps.LiteralInput('precipitation_uri',
                                     'Precipitation',
                                     data_type='string'),

                  pywps.LiteralInput('eto_uri',
                                     'Evapotranspiration',
                                     data_type='string'),

                  pywps.LiteralInput('depth_to_root_rest_layer_uri',
                                     'Root depth',
                                     data_type='string'),

                  pywps.LiteralInput('pawc_uri',
                                     'Plant available water content',
                                     data_type='string'),

                  pywps.LiteralInput('lulc_uri',
                                     'Land use land cover',
                                     data_type='string'),

                  pywps.LiteralInput('watersheds_uri',
                                     'Watersheds',
                                     data_type='string'),
                  
                  pywps.LiteralInput('biophysical_table_uri',
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
            identifier='natcap.invest.hydropower.hydropower_water_yield',
            title='Water Yield',
            abstract= natcap.invest.hydropower.hydropower_water_yield.__doc__,
            version= natcap.invest.__version__,
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):
        logger = logging.getLogger("wps_invest_wy")
        fh = logging.FileHandler('/tmp/esws.log')
        logger.addHandler(fh)
        logger.setLevel(logging.DEBUG)
        
        logger.info("BEGIN CALL TO WPS INVEST_WY")
        logger.debug("DEBUG MODE")

        workspace_uuid = request.inputs["workspace_dir"][0].data

        args = {}
        args_list = ['precipitation_uri',
                     'eto_uri',
                     'depth_to_root_rest_layer_uri',
                     'pawc_uri',
                     'lulc_uri',
                     'watersheds_uri',
                     'biophysical_table_uri',
                     'seasonality_constant']        

        for a in args_list:
            args[a] = request.inputs[a][0].data

        args["workspace_dir"] = tempfile.mkdtemp(prefix="esws-%s-" % str(self.uuid))


        for k in args.keys():
            try:
                args[k] = os.path.expanduser(args[k])

            except AttributeError:
                continue

        cat = easyows.Catalog(gs_url = "http://localhost:8080/geoserver",
                              username = "admin",
                              password = "geoserver",
                              ws_prefix = "esws-",
                              logger = logger)

        logger.info("Removing workspace(s)")
        try:
            cat.clean_named_workspace()

        except:
            raise pywps.exceptions.NoApplicableCode("Could not clean workspace(s)")

        logger.info("Making output workspace")
        ws = cat.make_named_workspace(workspace_uuid)

        layer_name = ":".join([ws, "wy"])
        
        logger.info("Constructing upload template")
        uploads = {
            layer_name : os.path.join(args[u'workspace_dir'], "output", u'watershed_results_wyield.shp')
        }

        logger.info("Constructing WPS job")
        j = easyows.Job(natcap.invest.hydropower.hydropower_water_yield.execute,
                        args,
                        uploads,
                        "Call to InVEST WY WPS %s" % ws,
                        0,
                        cat,
                        logger)

##        response.outputs['response'].data = str(args)
##        response.outputs['response'].uom = pywps.UOM('unity')
##
##        return response


        gs_url = "http://127.0.0.1:8080/geoserver"
        result_layers = ",".join([cat.cover_name_from_url(args["lulc_uri"]),layer_name])
        bbox = "453436.69380764756,4918220.405289317,468316.69380764384,4952570.405289317"
        width = "332"
        height = "768"
        srs = "EPSG:26910"
        result_template="%s/wms?service=WMS&version=1.1.0&request=GetMap&layers=%s&styles=&bbox=%s&width=%s&height=%s&srs=%s&format=application/openlayers"
        result_url = result_template % (gs_url, result_layers, bbox, width, height, srs)

        logger.info("Running job")
        while j.priority < 3:
            if j.run():
                response.outputs['response'].data = result_url
                response.outputs['response'].uom = pywps.UOM('unity')

                logger.info("END CALL TO WPS INVEST_WY")
                       
                return response

        raise IOError, "Job timed out."
