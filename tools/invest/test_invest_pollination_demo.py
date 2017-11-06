""""
This is a saved model run from natcap.invest.pollination.pollination.
Generated: 11/06/17 11:13:30
InVEST version: 3.3.3
"""

import natcap.invest.pollination.pollination


args = {
        u'ag_classes': '67 68 71 72 73 74 75 76 78 79 80 81 82 83 84 85 88 90 91 92',
        u'do_valuation': True,
        u'guilds_uri': u'D:/Martin/Data/Pollination/Input/Guild.csv',
        u'half_saturation': 0.125,
        u'landuse_attributes_uri': u'D:/Martin/Data/Pollination/Input/LU.csv',
        u'landuse_cur_uri': u'D:/Martin/Data/Base_Data/Terrestrial/lulc_samp_cur.tif',
        u'landuse_fut_uri': u'D:/Martin/Data/Base_Data/Terrestrial/lulc_samp_fut.tif',
        u'results_suffix': u'',
        u'wild_pollination_proportion': 1.0,
        u'workspace_dir': u'C:\\Users\\lacayoem/Documents/pollination_workspace',
}

if __name__ == '__main__':
    natcap.invest.pollination.pollination.execute(args)
