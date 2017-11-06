""""
This is a saved model run from natcap.invest.seasonal_water_yield.seasonal_water_yield.
Generated: 11/06/17 11:19:07
InVEST version: 3.3.3
"""

import natcap.invest.seasonal_water_yield.seasonal_water_yield
import os

args = {
        u'aoi_path': u'~/workspace/data/seasonal_water_yield/watershed.shp',
        u'beta_i': u'1.0',
        u'biophysical_table_path': u'~/workspace/data/seasonal_water_yield/biophysical_table.csv',
        u'climate_zone_raster_path': u'~/workspace/data/seasonal_water_yield/climate_zones.tif',
        u'climate_zone_table_path': u'~/workspace/data/seasonal_water_yield/climate_zone_events.csv',
        u'dem_raster_path': u'~/workspace/data/seasonal_water_yield/dem.tif',
        u'et0_dir': u'~/workspace/data/seasonal_water_yield/eto_dir',
        u'gamma': u'1.0',
        u'lulc_raster_path': u'~/workspace/data/seasonal_water_yield/lulc.tif',
        u'monthly_alpha': True,
        u'monthly_alpha_path': u'~/workspace/data/seasonal_water_yield/monthly_alpha.csv',
        u'precip_dir': u'~/workspace/data/seasonal_water_yield/precip_dir',
        u'rain_events_table_path': u'~/workspace/data/seasonal_water_yield/rain_events_table.csv',
        u'soil_group_path': u'~/workspace/data/seasonal_water_yield/soil_group.tif',
        u'threshold_flow_accumulation': u'1000',
        u'user_defined_climate_zones': False,
        u'user_defined_local_recharge': False,
        u'workspace_dir': u'/tmp/seasonal_water_yield_workspace',
}

if __name__ == '__main__':
    for k in args.keys():
        try:
            args[k] = os.path.expanduser(args[k])

        except AttributeError:
            continue

    natcap.invest.seasonal_water_yield.seasonal_water_yield.execute(args)
