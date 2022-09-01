import staticconf
import sphinx_rtd_theme

# -- General configuration -----------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
]

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'

# General information about the project.
project = 'PyStaticConfiguration'
copyright = '2013, Daniel Nephin'

version = staticconf.version
release = version

exclude_patterns = []

pygments_style = 'sphinx'


# -- Options for HTML output ---------------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_static_path = []

htmlhelp_basename = 'PyStaticConfigurationdoc'

# -- Extensions ----------------------------------------------------------------

autodoc_member_order = 'groupwise'

intersphinx_mapping = {
  'http://docs.python.org/': None,
}
