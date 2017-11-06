""""
This is a saved model run from natcap.invest.habitat_quality.
Generated: 11/06/17 11:07:35
InVEST version: 3.3.3
"""

import natcap.invest.habitat_quality


args = {
        u'access_uri': u'D:/Martin/Data/HabitatQuality/access_samp.shp',
        u'half_saturation_constant': u'0.5',
        u'landuse_cur_uri': u'D:/Martin/Data/HabitatQuality/lc_samp_cur_b.tif',
        u'sensitivity_uri': u'D:/Martin/Data/HabitatQuality/sensitivity_samp.csv',
        u'threat_raster_folder': u'D:/Martin/Data/HabitatQuality',
        u'threats_uri': u'D:/Martin/Data/HabitatQuality/threats_samp.csv',
        u'workspace_dir': u'C:/Users/lacayoem/Documents/habitat_quality_workspace',
}

if __name__ == '__main__':
    natcap.invest.habitat_quality.execute(args)
