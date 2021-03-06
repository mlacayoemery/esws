import pywps

import urllib

import sys
if sys.version_info.major == 2:
    import urllib
    urlretrieve = urllib.URLopener().retrieve
    unquote = urllib.unquote

else:
    from urllib.request import urlretrieve
    from urllib.parse import unquote

import tempfile
import zipfile

import os
from shutil import copyfile

class WebProcess(pywps.Process):
    def __init__(self):
        inputs = [pywps.LiteralInput('model',
                                     'SWAT ZIP',
                                     data_type='string')]

        outputs = [pywps.LiteralOutput('response',
                                       'Output response',
                                       data_type='string')]

        super(WebProcess, self).__init__(
            self._handler,
            identifier='swat',
            title='SWAT',
            abstract='SWAT rev 664',
            version='664',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):
        prefix = "esws-"
        value = unquote(request.inputs['model'][0].data)

        swat_exe = "swat.exe"
        swat_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
                                 swat_exe)
        
        _, tmp_path = tempfile.mkstemp(suffix=".zip", prefix=prefix)
        urllib.URLopener().retrieve(value, tmp_path)

        tmp_dir = tempfile.mkdtemp(prefix=prefix)

        try:
            zipfile.ZipFile(tmp_path, 'r').extractall(tmp_dir)
            swat_dst = os.path.join(tmp_dir, swat_exe)            
            copyfile(swat_path, swat_dst)
            os.chdir(tmp_dir)
            os.system(swat_exe)

            msg = tmp_dir
            
        except zipfile.BadZipfile:
            msg = "Invalid inputs"
        
        response.outputs['response'].data = msg
        response.outputs['response'].uom = pywps.UOM('unity')
        return response
