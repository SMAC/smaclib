from zope.interface import implements

from twisted.application import service
from twisted.application import internet
from twisted.plugin import IPlugin
from twisted.python import usage
from twisted.web import server, resource

from smaclib import brokers


class ModuleOptions(usage.Options):
    optParameters = [
        ["port", "p", 7080, "The port number to listen on."]
    ]


class ModuleMaker(object):
    implements(service.IServiceMaker, IPlugin)

    options = ModuleOptions

    def getModule(self):
        raise NotImplementedError("No module provided")

    def makeService(self, options):
        module_service = service.MultiService()

        port = int(options["port"])
        obj = self.getModule()

        # Root resource
        root = resource.Resource()

        # Publish XML RPC interface
        root.putChild('RPC2', brokers.XmlRpcBroker(obj))

        # Publish the SOAP interface
        root.putChild('SOAP', brokers.SoapBroker(obj))

        http_service = internet.TCPServer(port, server.Site(root))
        http_service.setServiceParent(module_service)

        thrift_service = internet.TCPServer(port+1, brokers.ThriftBroker(obj))
        thrift_service.setServiceParent(module_service)

        return module_service
