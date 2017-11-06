""""
This is a saved model run from natcap.invest.wind_energy.wind_energy.
Generated: 11/06/17 11:26:56
InVEST version: 3.3.3
"""

import natcap.invest.wind_energy.wind_energy


args = {
        u'aoi_uri': u'D:\\Martin\\Data\\WindEnergy\\input\\New_England_US_Aoi.shp',
        u'avg_grid_distance': u'4',
        u'bathymetry_uri': u'D:/Martin/Data/Base_Data/Marine/DEMs/global_dem.tif',
        u'discount_rate': u'',
        u'foundation_cost': u'',
        u'global_wind_parameters_uri': u'D:\\Martin\\Data\\WindEnergy\\input\\global_wind_energy_parameters.csv',
        u'land_polygon_uri': u'D:\\Martin\\Data\\Base_Data\\Marine\\Land\\global_polygon.shp',
        u'max_depth': u'60',
        u'max_distance': u'200000',
        u'min_depth': u'3',
        u'min_distance': u'0',
        u'number_of_turbines': u'80',
        u'price_table': True,
        u'turbine_parameters_uri': u'D:\\Martin\\Data\\WindEnergy\\input\\3_6_turbine.csv',
        u'valuation_container': False,
        u'wind_data_uri': u'D:\\Martin\\Data\\WindEnergy\\input\\ECNA_EEZ_WEBPAR_Aug27_2012.csv',
        u'wind_schedule': u'D:\\Martin\\Data\\WindEnergy\\input\\price_table_example.csv',
        u'workspace_dir': u'C:\\Users\\lacayoem/Documents/wind_energy_workspace',
}

if __name__ == '__main__':
    natcap.invest.wind_energy.wind_energy.execute(args)
