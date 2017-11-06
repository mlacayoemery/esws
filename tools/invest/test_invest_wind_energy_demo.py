""""
This is a saved model run from natcap.invest.wind_energy.wind_energy.
Generated: 11/06/17 11:26:56
InVEST version: 3.3.3
"""

import natcap.invest.wind_energy.wind_energy
import os

args = {
        u'aoi_uri': u'~/workspace/data/WindEnergy/input/New_England_US_Aoi.shp',
        u'avg_grid_distance': u'4',
        u'bathymetry_uri': u'~/workspace/data/Base_Data/Marine/DEMs/global_dem.tif',
        u'discount_rate': u'',
        u'foundation_cost': u'',
        u'global_wind_parameters_uri': u'~/workspace/data/WindEnergy/input/global_wind_energy_parameters.csv',
        u'land_polygon_uri': u'~/workspace/data/Base_Data/Marine/Land/global_polygon.shp',
        u'max_depth': u'60',
        u'max_distance': u'200000',
        u'min_depth': u'3',
        u'min_distance': u'0',
        u'number_of_turbines': u'80',
        u'price_table': True,
        u'turbine_parameters_uri': u'~/workspace/data/WindEnergy/input/3_6_turbine.csv',
        u'valuation_container': False,
        u'wind_data_uri': u'~/workspace/data/WindEnergy/input/ECNA_EEZ_WEBPAR_Aug27_2012.csv',
        u'wind_schedule': u'~/workspace/data/WindEnergy/input/price_table_example.csv',
        u'workspace_dir': u'/tmp/wind_energy_workspace',
}

if __name__ == '__main__':
    for k in args.keys():
        try:
            args[k] = os.path.expanduser(args[k])

        except AttributeError:
            continue

    natcap.invest.wind_energy.wind_energy.execute(args)
