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

        workspace = request.inputs["workspace_dir"][0].data

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
        cat.clean_named_workspace()

    
        ws = cat.make_named_workspace(str(self.uuid))

        layer_name = ":".join([ws, "wy"])

        uploads = {
            layer_name : os.path.join(args[u'workspace_dir'], "output", u'watershed_results_wyield.shp')
        }

        j = easyows.Job(natcap.invest.hydropower.hydropower_water_yield.execute,
                        args,
                        uploads,
                        "Call to InVEST WY WPS %s" % ws,
                        0,
                        cat,
                        logger)

        j.run()
        
        response.outputs['response'].data = "Success in running Water Yield model %s" % ws
        response.outputs['response'].uom = pywps.UOM('unity')

        logger.info("END CALL TO WPS INVEST_WY")
        
        return response
