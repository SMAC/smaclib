

from smaclib import brokers
from smaclib import routers
from smaclib.db import mongo
from smaclib.conf import settings

import txmongo

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

    def load_settings(self, configfile):
        if configfile:
            settings.load(configfile)

    def get_module(self):
        raise NotImplementedError("No module provided")

    
    def make_service(self, options):
        self.load_settings(options['configfile'])

        module_service = service.MultiService()

        # MongoDB
        mongo.connection.set(txmongo.lazyMongoConnectionPool(
                                            **settings.mongodb['connection']))

        self.module = self.get_module()
        
        if settings.rest['expose']:
            # Root resource
            root = resource.Resource()

            if 'rpc' in settings.rest['expose']:
                # Publish XML RPC interface
                path = settings.rest['expose']['rpc']
                root.putChild(path, brokers.XmlRpcBroker(self.module,
                              router=routers.PrefixRouter('xmlrpc', 'remote')))
        
            if 'soap' in settings.rest['expose']:
                # Publish the SOAP interface
                path = settings.rest['expose']['soap']
                root.putChild(path, brokers.SoapBroker(self.module,
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

        thrift_service = internet.TCPServer(
            settings.thrift_port,
            brokers.ThriftBroker(self.module,
                                 routers.PrefixRouter('thrift', 'remote'))
        )
        thrift_service.setServiceParent(module_service)
        
        print "Starting service, my module ID is", self.module.remote_getID()

        return module_service

    def makeService(self, options):
        """
        Proxy method to avoid twisted' naming conventions.
        """
        return self.make_service(options)

