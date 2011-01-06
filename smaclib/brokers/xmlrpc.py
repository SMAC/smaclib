"""
Broker implementation to expose a module over XML RPC.
"""


from smaclib.brokers import base

from twisted.web import xmlrpc


class XmlRpcBroker(base.Broker, xmlrpc.XMLRPC):

    def _getFunction(self, functionPath):
        """
        Intercepts the various XML RPC requests and resolves them to methods
        using the given filters.
        """
        
        try:
            func = self.router(self.obj, functionPath)
        except AttributeError:
            raise xmlrpc.NoSuchFunction(self.NOT_FOUND,
                    "function {} not found".format(functionPath))
        else:
            if not callable(func):
                raise xmlrpc.NoSuchFunction(self.NOT_FOUND,
                        "function {} not callable".format(functionPath))
            else:
                return func

