""""
This is a saved model run from natcap.invest.pollination.pollination.
Generated: 11/06/17 11:13:30
InVEST version: 3.3.3
"""

import natcap.invest.pollination.pollination
import os

args = {
        u'ag_classes': '67 68 71 72 73 74 75 76 78 79 80 81 82 83 84 85 88 90 91 92',
        u'do_valuation': True,
        u'guilds_uri': u'~/workspace/data/Pollination/Input/Guild.csv',
        u'half_saturation': 0.125,
        u'landuse_attributes_uri': u'~/workspace/data/Pollination/Input/LU.csv',
        u'landuse_cur_uri': u'~/workspace/data/Base_Data/Terrestrial/lulc_samp_cur.tif',
        u'landuse_fut_uri': u'~/workspace/data/Base_Data/Terrestrial/lulc_samp_fut.tif',
        u'results_suffix': u'',
        u'wild_pollination_proportion': 1.0,
        u'workspace_dir': u'/tmp/pollination_workspace',
}

if __name__ == '__main__':
    for k in args.keys():
        try:
            args[k] = os.path.expanduser(args[k])

        except AttributeError:
            continue

    natcap.invest.pollination.pollination.execute(args)
