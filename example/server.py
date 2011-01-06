from smaclib import brokers

from twisted.internet import reactor
from twisted.web import server, resource

import module


def main():
    # Create the service
    service = module.MyModule()
    
    # Root resource
    root = resource.Resource()
    
    # Publish XML RPC interface
    root.putChild('RPC2', brokers.XmlRpcBroker(service))
    
    # Publish the SOAP interface
    root.putChild('SOAP', brokers.SoapBroker(service))
    
    # Run the HTTP server
    reactor.listenTCP(7080, server.Site(root))
    
    # Publish thrift interface on standalone server
    reactor.listenTCP(7081, brokers.ThriftBroker(service))
    
    # Let it do its job
    reactor.run()


if __name__ == '__main__':
    main()

