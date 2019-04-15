import pywps

import sys
import os.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import easyows

class WebProcess(pywps.Process):
    def __init__(self):
        inputs = [pywps.LiteralInput('precipitation_uri',
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
            abstract='InVEST water balance model',
            version='3.6.0',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):


        
        response.outputs['response'].data = "Request recieved"
        response.outputs['response'].uom = pywps.UOM('unity')
        return response
