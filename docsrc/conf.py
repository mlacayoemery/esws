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

# sphinxcontrib-mermaid defaults to a fixed 500px-tall box, which letterboxes the
# taller model-input trees down to ~0.23 scale and makes their labels unreadable.
mermaid_height = 'auto'

# alabaster's default 940px page leaves a ~575px content column, and the wider
# model-input trees (natural width ~1160px) then draw at about half scale. This
# widens the column enough to read them without zooming; prose line length stays
# reasonable because the sidebar takes its share.
html_theme_options = {'page_width': '1200px'}

exclude_patterns = ['_build']
source_suffix = '.rst'
master_doc = 'index'

pygments_style = 'sphinx'

#html_static_path = ['_static']

htmlhelp_basename = 'ESWSdoc'
 
