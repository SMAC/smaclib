"""
"""

from twisted.python import filepath

# pylint: disable=C0103,W0105
# Yes... it is a configuration file, and I want my values to be lowercase as
# they are eventually read as instance properties.
# And as epydoc recognizes docstrings for variables too, I provide them too 
# here.

data_root = filepath.FilePath('recordings')
"""
Base directory to the currently recording session.
"""

recording_executable = filepath.FilePath('C:/smacCapture/capture2.exe')
"""
Path to the binary executable used to access the capture card.
"""