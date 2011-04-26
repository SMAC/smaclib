"""
Default configuration for all publisher modules.
This configuration can be overridden in user defined settings files.
"""


from twisted.python import filepath


# pylint: disable=C0103,W0105
# Yes... it is a configuration file, and I want my values to be lowercase as
# they are eventually read as instance properties.
# And as epydoc recognizes docstrings for variables too, I provide them too 
# here.


data_root = filepath.FilePath('httpdocs')
"""
Base directory to hold all published data.
"""

http_port = 80
"""
Port on which requests have to be served.
"""