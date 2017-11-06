""""
This is a saved model run from natcap.invest.scenario_gen_proximity.
Generated: 11/06/17 11:17:00
InVEST version: 3.3.3
"""

import natcap.invest.scenario_gen_proximity


args = {
        u'aoi_path': u'D:/Martin/Data/scenario_proximity/scenario_proximity_aoi.shp',
        u'area_to_convert': u'20000.0',
        u'base_lulc_path': u'D:/Martin/Data/scenario_proximity/scenario_proximity_lulc.tif',
        u'convert_farthest_from_edge': True,
        u'convert_nearest_to_edge': True,
        u'convertible_landcover_codes': u'1 2 3 4 5',
        u'focal_landcover_codes': u'1 2 3 4 5',
        u'n_fragmentation_steps': u'1',
        u'replacment_lucode': u'12',
        u'workspace_dir': u'C:\\Users\\lacayoem/Documents/scenario_proximity_workspace',
}

if __name__ == '__main__':
    natcap.invest.scenario_gen_proximity.execute(args)
