""""
This is a saved model run from natcap.invest.globio.
Generated: 11/06/17 11:05:24
InVEST version: 3.3.3
"""

import natcap.invest.globio


args = {
        u'aoi_uri': u'D:/Martin/Data/globio/sub_aoi.shp',
        u'infrastructure_dir': u'D:/Martin/Data/globio/infrastructure_dir',
        u'intensification_fraction': u'0.46',
        u'lulc_to_globio_table_uri': u'D:/Martin/Data/globio/lulc_conversion_table.csv',
        u'lulc_uri': u'D:/Martin/Data/globio/lulc_2008.tif',
        u'msa_parameters_uri': u'D:/Martin/Data/globio/msa_parameters.csv',
        u'pasture_threshold': u'0.5',
        u'pasture_uri': u'D:/Martin/Data/globio/pasture.tif',
        u'potential_vegetation_uri': u'D:/Martin/Data/globio/potential_vegetation.tif',
        u'predefined_globio': False,
        u'primary_threshold': u'0.66',
        u'workspace_dir': u'C:/Users/lacayoem/Documents/globio_workspace',
}

if __name__ == '__main__':
    natcap.invest.globio.execute(args)
