import pywps

import sys
import os.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import easyows

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

        #natcap.invest.hydropower.hydropower_water_yield.execute(args)
        
        response.outputs['response'].data = "Running Water Yield model on %s" % str(args)
        response.outputs['response'].uom = pywps.UOM('unity')
        return response
