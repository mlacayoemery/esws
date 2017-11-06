""""
This is a saved model run from natcap.invest.ndr.ndr.
Generated: 11/06/17 11:11:36
InVEST version: 3.3.3
"""

import natcap.invest.ndr.ndr
import os

args = {
        u'biophysical_table_path': u'~/workspace/data/Base_Data/Freshwater/biophysical_table.csv',
        u'calc_n': True,
        u'calc_p': True,
        u'dem_path': u'~/workspace/data/Base_Data/Freshwater/dem.tif',
        u'k_param': u'2',
        u'lulc_path': u'~/workspace/data/Base_Data/Freshwater/landuse_90.tif',
        u'runoff_proxy_path': u'~/workspace/data/Base_Data/Freshwater/precip.tif',
        u'subsurface_critical_length_n': u'150',
        u'subsurface_critical_length_p': u'150',
        u'subsurface_eff_n': u'0.8',
        u'subsurface_eff_p': u'0.8',
        u'threshold_flow_accumulation': u'1000',
        u'watersheds_path': u'~/workspace/data/Base_Data/Freshwater/watersheds.shp',
        u'workspace_dir': u'/tmp/ndr_workspace',
}

if __name__ == '__main__':
    for k in args.keys():
        try:
            args[k] = os.path.expanduser(args[k])

        except AttributeError:
            continue

    natcap.invest.ndr.ndr.execute(args)
