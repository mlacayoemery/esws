""""
This is a saved model run from natcap.invest.forest_carbon_edge_effect.
Generated: 11/06/17 11:03:10
InVEST version: 3.3.3
"""

import natcap.invest.forest_carbon_edge_effect


args = {
        u'aoi_uri': u'D:/Martin/Data/forest_carbon_edge_effect/forest_carbon_edge_demo_aoi.shp',
        u'biomass_to_carbon_conversion_factor': u'0.47',
        u'biophysical_table_uri': u'D:/Martin/Data/forest_carbon_edge_effect/forest_edge_carbon_lu_table.csv',
        u'compute_forest_edge_effects': True,
        u'lulc_uri': u'D:/Martin/Data/forest_carbon_edge_effect/forest_carbon_edge_lulc_demo.tif',
        u'n_nearest_model_points': u'10',
        u'pools_to_calculate': u'all',
        u'tropical_forest_edge_carbon_model_shape_uri': u'D:/Martin/Data/forest_carbon_edge_effect/core_data/forest_carbon_edge_regression_model_parameters.shp',
        u'workspace_dir': u'C:/Users/lacayoem/Documents/forest_carbon_edge_workspace',
}

if __name__ == '__main__':
    natcap.invest.forest_carbon_edge_effect.execute(args)
