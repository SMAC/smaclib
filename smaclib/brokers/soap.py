"""
Broker implementation to expose a module over SOAP.
"""


from smaclib.brokers import base

from twisted.web import soap


class SoapBroker(base.Broker, soap.SOAPPublisher):
    
    def lookupFunction(self, functionName):
        """
        Intercepts the various SOAP requests and resolves them to methods
        using the given filters.
        """
        
        try:
            func = self.router(self.obj, functionName)
        except AttributeError:
            return None
        else:
            return func if callable(func) else None

