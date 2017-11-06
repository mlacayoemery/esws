""""
This is a saved model run from natcap.invest.routing.delineateit.
Generated: 11/06/17 10:58:11
InVEST version: 3.3.3
"""

import natcap.invest.routing.delineateit
import os

args = {
        u'dem_uri': u'~/workspace/data/Base_Data/Freshwater/dem.tif',
        u'flow_threshold': u'1000',
        u'outlet_shapefile_uri': u'~/workspace/data/Base_Data/Freshwater/outlets.shp',
        u'snap_distance': u'10',
        u'workspace_dir': u'/tmp/delineateit_workspace',
}

if __name__ == '__main__':
    for k in args.keys():
        try:
            args[k] = os.path.expanduser(args[k])

        except AttributeError:
            continue

    natcap.invest.routing.delineateit.execute(args)
