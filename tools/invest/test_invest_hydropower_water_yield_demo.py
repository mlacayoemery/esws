""""
This is a saved model run from natcap.invest.hydropower.hydropower_water_yield.
Generated: 11/06/17 11:20:40
InVEST version: 3.3.3
"""

import natcap.invest.hydropower.hydropower_water_yield


args = {
        u'biophysical_table_uri': u'D:\\Martin\\Data\\Hydropower\\input\\biophysical_table.csv',
        u'demand_table_uri': u'D:\\Martin\\Data\\Hydropower\\input\\water_demand_table.csv',
        u'depth_to_root_rest_layer_uri': u'D:\\Martin\\Data\\Base_Data\\Freshwater\\depth_to_root_rest_layer',
        u'eto_uri': u'D:\\Martin\\Data\\Base_Data\\Freshwater\\eto',
        u'lulc_uri': u'D:\\Martin\\Data\\Base_Data\\Freshwater\\landuse_90',
        u'pawc_uri': u'D:\\Martin\\Data\\Base_Data\\Freshwater\\pawc',
        u'precipitation_uri': u'D:\\Martin\\Data\\Base_Data\\Freshwater\\precip',
        u'results_suffix': u'',
        u'seasonality_constant': u'5',
        u'sub_watersheds_uri': u'D:\\Martin\\Data\\Base_Data\\Freshwater\\subwatersheds.shp',
        u'valuation_container': True,
        u'valuation_table_uri': u'D:\\Martin\\Data\\Hydropower\\input\\hydropower_valuation_table.csv',
        u'water_scarcity_container': True,
        u'watersheds_uri': u'D:\\Martin\\Data\\Base_Data\\Freshwater\\watersheds.shp',
        u'workspace_dir': u'C:\\Users\\lacayoem/Documents/water_yield_workspace',
}

if __name__ == '__main__':
    natcap.invest.hydropower.hydropower_water_yield.execute(args)
