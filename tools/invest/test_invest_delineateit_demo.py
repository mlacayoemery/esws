""""
This is a saved model run from natcap.invest.routing.delineateit.
Generated: 11/06/17 10:58:11
InVEST version: 3.3.3
"""

import natcap.invest.routing.delineateit


args = {
        u'dem_uri': u'D:/Martin/Data/Base_Data/Freshwater/dem.tif',
        u'flow_threshold': u'1000',
        u'outlet_shapefile_uri': u'D:/Martin/Data/Base_Data/Freshwater/outlets.shp',
        u'snap_distance': u'10',
        u'workspace_dir': u'C:\\Users\\lacayoem/Documents/delineateit_workspace',
}

if __name__ == '__main__':
    natcap.invest.routing.delineateit.execute(args)
