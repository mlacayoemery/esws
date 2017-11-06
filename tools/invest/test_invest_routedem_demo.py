""""
This is a saved model run from natcap.invest.routing.routedem.
Generated: 11/06/17 11:16:05
InVEST version: 3.3.3
"""

import natcap.invest.routing.routedem
import os

args = {
        u'calculate_downstream_distance': True,
        u'calculate_slope': True,
        u'dem_uri': u'~/workspace/data/Base_Data/Freshwater/dem.tif',
        u'downstream_distance_filename': u'downstream_distance.tif',
        u'flow_accumulation_filename': u'flow_accumulation.tif',
        u'flow_direction_filename': u'flow_direction.tif',
        u'multiple_stream_thresholds': True,
        u'pit_filled_filename': u'pit_filled_dem.tif',
        u'slope_filename': u'slope.tif',
        u'threshold_flow_accumulation': u'1000',
        u'threshold_flow_accumulation_stepsize': u'100',
        u'threshold_flow_accumulation_upper': u'2000',
        u'workspace_dir': u'/tmp/routedem_workspace',
}

if __name__ == '__main__':
    for k in args.keys():
        try:
            args[k] = os.path.expanduser(args[k])

        except AttributeError:
            continue

    natcap.invest.routing.routedem.execute(args)
