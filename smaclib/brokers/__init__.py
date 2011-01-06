"""
Collection of brokers which can be used to expose the functionality of the
different SMAC modules over different transports, such as XMLRPC or Thrift.
"""


from smaclib.brokers.xmlrpc import XmlRpcBroker
from smaclib.brokers.soap import SoapBroker
from smaclib.brokers.thrift import ThriftBroker


__all__ = ['XmlRpcBroker', 'SoapBroker', 'ThriftBroker']