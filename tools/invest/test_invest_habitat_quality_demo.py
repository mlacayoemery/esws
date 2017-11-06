""""
This is a saved model run from natcap.invest.habitat_quality.
Generated: 11/06/17 11:07:35
InVEST version: 3.3.3
"""

import natcap.invest.habitat_quality
import os

args = {
        u'access_uri': u'~/workspace/data/HabitatQuality/access_samp.shp',
        u'half_saturation_constant': u'0.5',
        u'landuse_cur_uri': u'~/workspace/data/HabitatQuality/lc_samp_cur_b.tif',
        u'sensitivity_uri': u'~/workspace/data/HabitatQuality/sensitivity_samp.csv',
        u'threat_raster_folder': u'~/workspace/data/HabitatQuality',
        u'threats_uri': u'~/workspace/data/HabitatQuality/threats_samp.csv',
        u'workspace_dir': u'/tmp/habitat_quality_workspace',
}

if __name__ == '__main__':
    for k in args.keys():
        try:
            args[k] = os.path.expanduser(args[k])

        except AttributeError:
            continue

    natcap.invest.habitat_quality.execute(args)
