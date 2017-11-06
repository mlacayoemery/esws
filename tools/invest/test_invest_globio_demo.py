""""
This is a saved model run from natcap.invest.globio.
Generated: 11/06/17 11:05:24
InVEST version: 3.3.3
"""

import natcap.invest.globio
import os

args = {
        u'aoi_uri': u'~/workspace/data/globio/sub_aoi.shp',
        u'infrastructure_dir': u'~/workspace/data/globio/infrastructure_dir',
        u'intensification_fraction': u'0.46',
        u'lulc_to_globio_table_uri': u'~/workspace/data/globio/lulc_conversion_table.csv',
        u'lulc_uri': u'~/workspace/data/globio/lulc_2008.tif',
        u'msa_parameters_uri': u'~/workspace/data/globio/msa_parameters.csv',
        u'pasture_threshold': u'0.5',
        u'pasture_uri': u'~/workspace/data/globio/pasture.tif',
        u'potential_vegetation_uri': u'~/workspace/data/globio/potential_vegetation.tif',
        u'predefined_globio': False,
        u'primary_threshold': u'0.66',
        u'workspace_dir': u'C:/Users/lacayoem/Documents/globio_workspace',
}

if __name__ == '__main__':
    for k in args.keys():
        try:
            args[k] = os.path.expanduser(args[k])

        except AttributeError:
            continue

    natcap.invest.globio.execute(args)
