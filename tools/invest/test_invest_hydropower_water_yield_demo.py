""""
This is a saved model run from natcap.invest.hydropower.hydropower_water_yield.
Generated: 11/06/17 11:20:40
InVEST version: 3.3.3
"""

import natcap.invest.hydropower.hydropower_water_yield
import os

args = {
        u'biophysical_table_uri': u'~/workspace/data/Hydropower/input/biophysical_table.csv',
        u'demand_table_uri': u'~/workspace/data/Hydropower/input/water_demand_table.csv',
        u'depth_to_root_rest_layer_uri': u'~/workspace/data/Base_Data/Freshwater/depth_to_root_rest_layer.tif',
        u'eto_uri': u'~/workspace/data/Base_Data/Freshwater/eto.tif',
        u'lulc_uri': u'~/workspace/data/Base_Data/Freshwater/landuse_90.tif',
        u'pawc_uri': u'~/workspace/data/Base_Data/Freshwater/pawc.tif',
        u'precipitation_uri': u'~/workspace/data/Base_Data/Freshwater/precip.tif',
        u'results_suffix': u'',
        u'seasonality_constant': u'5',
        u'sub_watersheds_uri': u'~/workspace/data/Base_Data/Freshwater/subwatersheds.shp',
        u'valuation_container': True,
        u'valuation_table_uri': u'~/workspace/data/Hydropower/input/hydropower_valuation_table.csv',
        u'water_scarcity_container': True,
        u'watersheds_uri': u'~/workspace/data/Base_Data/Freshwater/watersheds.shp',
        u'workspace_dir': u'/tmp/water_yield_workspace',
}

if __name__ == '__main__':
    for k in args.keys():
        try:
            args[k] = os.path.expanduser(args[k])

        except AttributeError:
            continue

    natcap.invest.hydropower.hydropower_water_yield.execute(args)
