"""
This package provides at least a basic implementation of all SMAC modules.

Each module implementation is conceived to be compatible with a general broker
and it should thus be possible to expose it over an arbitrary protocol (the
smac library provides brokers for the XMLRPC, SOAP and Thrift protocols).
"""


from smaclib.modules import base
#from smaclib.modules.archiver.module import Archiver
#from smaclib.modules.analyzer.module import Analyzer


__all__ = ['base']