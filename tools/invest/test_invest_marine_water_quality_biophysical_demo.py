""""
This is a saved model run from natcap.invest.marine_water_quality.marine_water_quality_biophysical.
Generated: 11/06/17 11:09:52
InVEST version: 3.3.3
"""

import natcap.invest.marine_water_quality.marine_water_quality_biophysical


args = {
        u'adv_uv_points_uri': u'D:\\Martin\\Data\\MarineWaterQuality\\input\\ADVuv_WGS1984_BCAlbers.shp',
        u'aoi_poly_uri': u'D:\\Martin\\Data\\MarineWaterQuality\\input\\AOI_clay_soundwideWQ.shp',
        u'kps': 0.001,
        u'land_poly_uri': u'D:\\Martin\\Data\\MarineWaterQuality\\input\\3005_VI_landPolygon.shp',
        u'layer_depth': 1.0,
        u'pixel_size': 100.0,
        u'source_point_data_uri': u'D:\\Martin\\Data\\MarineWaterQuality\\input\\WQM_PAR.csv',
        u'source_points_uri': u'D:\\Martin\\Data\\MarineWaterQuality\\input\\floathomes_centroids.shx',
        u'tide_e_points_uri': u'D:\\Martin\\Data\\MarineWaterQuality\\input\\TideE_WGS1984_BCAlbers.shp',
        u'workspace_dir': u'C:\\Users\\lacayoem/Documents/marine_water_quality_workspace',
}

if __name__ == '__main__':
    natcap.invest.marine_water_quality.marine_water_quality_biophysical.execute(args)
