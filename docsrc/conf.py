import os
import sys

sys.path.insert(0, os.path.abspath('_ext'))

project = 'ESWS'

extensions = ['sphinxcontrib.mermaid', 'invest_inputs']
#    'sphinx.ext.extlinks',
#    'sphinx.ext.autodoc',
#    'sphinx.ext.todo',
#    'sphinx.ext.mathjax',
#    'sphinx.ext.viewcode',
#    'sphinx.ext.napoleon',
#    'pywps.ext_autodoc'
#]

exclude_patterns = ['_build']
source_suffix = '.rst'
master_doc = 'index'

pygments_style = 'sphinx'

#html_static_path = ['_static']

htmlhelp_basename = 'ESWSdoc'
 
