
from smaclib import routers
from smaclib.conf import settings

from twisted.application import service
from twisted.application import internet
from twisted.plugin import IPlugin
from twisted.python import usage
from twisted.web import server, resource
from twisted.internet import ssl

from zope.interface import implements


class ModuleOptions(usage.Options):
    def parseArgs(self, configfile=None):
        self['configfile'] = configfile


class ModuleMaker(object):
    implements(service.IServiceMaker, IPlugin)

    options = ModuleOptions
    module = None

    def loadSettings(self, configfile):
        if configfile:
            settings.load(configfile)

    def getModule(self):
        raise NotImplementedError("No module provided")

    
    def makeService(self, options):
        self.loadSettings(options['configfile'])

        module_service = service.MultiService()

        self.module = self.getModule()
        
        if settings.rest['expose']:
            # Root resource
            root = resource.Resource()

            if 'rpc' in settings.rest['expose']:
                from smaclib.brokers.xmlrpc import XmlRpcBroker
                
                # Publish XML RPC interface
                path = settings.rest['expose']['rpc']
                root.putChild(path, XmlRpcBroker(self.module,
                              router=routers.PrefixRouter('xmlrpc', 'remote')))
        
            if 'soap' in settings.rest['expose']:
                from smaclib.brokers.soap import SoapBroker
                # Publish the SOAP interface
                path = settings.rest['expose']['soap']
                root.putChild(path, SoapBroker(self.module,
                              router=routers.PrefixRouter('soap', 'remote')))
            
            if settings.rest['ssl']:
                context = ssl.DefaultOpenSSLContextFactory(
                    settings.rest['private_key'],
                    settings.rest['certificate'],
                )
                rest_service = internet.SSLServer(
                    settings.rest['port'],
                    server.Site(root),
                    context
                )
            else:
                rest_service = internet.TCPServer(
                    settings.rest['port'],
                    server.Site(root)
                )
            rest_service.setServiceParent(module_service)

        from smaclib.brokers.thrift import ThriftBroker

        thrift_service = internet.TCPServer(
            settings.thrift_port,
            ThriftBroker(self.module, routers.PrefixRouter('thrift', 'remote'))
        )
        thrift_service.setServiceParent(module_service)
        
        print "Starting service, my module ID is", self.module.getID()

        return module_service


