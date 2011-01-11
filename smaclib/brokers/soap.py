"""
Broker implementation to expose a module over SOAP.
"""


from smaclib.brokers import base

from twisted.web import soap


class SoapBroker(base.Broker, soap.SOAPPublisher):
    """
    A Broker specialization for SOAP based communication.
    
    Extends the soap.SOAPPublisher class to provide a smaclib compatible
    broking interface.
    
    @todo: Add patches to handle structures through custom dictionary types for
           compatibility with thrift.
    """
    
    def lookup_function(self, function_name):
        """
        Intercepts the various SOAP requests and resolves them to methods
        using the given filters.
        """
        
        try:
            func = self.router(self.obj, function_name)
        except AttributeError:
            return None
        else:
            return func if callable(func) else None
    lookupFunction = lookup_function


