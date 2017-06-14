import urllib2
import tempfile
import zipfile
import os
import glob

import natcap.invest.sdr


downloads = {
        u'biophysical_table_path': u'http://gala.unige.ch/documents/13/download',
        u'dem_path': u'http://gala.unige.ch:8080/geoserver/wcs?format=image%2Ftiff&request=GetCoverage&version=2.0.1&service=WCS&coverageid=geonode%3Adem',
        u'erodibility_path': u'http://gala.unige.ch:8080/geoserver/wcs?format=image%2Ftiff&request=GetCoverage&version=2.0.1&service=WCS&coverageid=geonode%3Aerodibility',
        u'erosivity_path': u'http://gala.unige.ch:8080/geoserver/wcs?format=image%2Ftiff&request=GetCoverage&version=2.0.1&service=WCS&coverageid=geonode%3Aerosivity',
        u'lulc_path': u'http://gala.unige.ch:8080/geoserver/wcs?format=image%2Ftiff&request=GetCoverage&version=2.0.1&service=WCS&coverageid=geonode%3Alanduse_90',
        u'watersheds_path': u'http://gala.unige.ch:8080/geoserver/wfs?typename=geonode%3Awatersheds&outputFormat=SHAPE-ZIP&version=1.0.0&service=WFS&request=GetFeature',
}

args = {
        u'biophysical_table_path': u'/home/mlacayo/workspace/data/Base_Data/Freshwater/biophysical_table.csv',
        u'dem_path': u'/home/mlacayo/workspace/data/Base_Data/Freshwater/dem',
        u'drainage_path': u'',
        u'erodibility_path': u'/home/mlacayo/workspace/data/Base_Data/Freshwater/erodibility',
        u'erosivity_path': u'/home/mlacayo/workspace/data/Base_Data/Freshwater/erosivity',
        u'ic_0_param': u'0.5',
        u'k_param': u'2',
        u'lulc_path': u'/home/mlacayo/workspace/data/Base_Data/Freshwater/landuse_90',
        u'sdr_max': u'0.8',
        u'threshold_flow_accumulation': u'1000',
        u'watersheds_path': u'/home/mlacayo/workspace/data/Base_Data/Freshwater/watersheds.shp',
        u'workspace_dir': u'/tmp/sedimentation_workspace',
}

if __name__ == '__main__':
    for k in downloads.keys():
        f = tempfile.NamedTemporaryFile(delete=False)
        print "Downloading %s to %s" % (k, f.name)
        
        response = urllib2.urlopen(downloads[k])
        f.write(response.read())
        f.close()

        if "outputFormat=SHAPE-ZIP" in downloads[k]:
            shapefile = zipfile.ZipFile(f.name, 'r')
            shapefolder = tempfile.mkdtemp()
            print "Unzipping shapefile to %s" % shapefolder
            shapefile.extractall(shapefolder)
            shapefile.close()
            os.chdir(shapefolder)
            for shp in glob.glob("*.shp"):
                args[k] = os.path.join(shapefolder,shp)
        else:
            args[k] = f.name

    args[u'workspace_dir'] = tempfile.mkdtemp()
    print args
    natcap.invest.sdr.execute(args)
