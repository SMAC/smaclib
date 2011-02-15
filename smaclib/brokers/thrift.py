"""

"""


from __future__ import absolute_import

from smaclib import routers
from smaclib.brokers import base

from thrift.transport import TTwisted
from thrift.protocol import TBinaryProtocol

from zope.interface import providedBy
from zope.interface import directlyProvides


class ThriftBroker(TTwisted.ThriftServerFactory, object):
    def __init__(self, service, router=None, processor=None):
        
        ifaces = list(providedBy(service))
        
        if processor is None:
            if not ifaces:
                raise ValueError("This service provides no interfaces.")
            
            if len(ifaces) > 1:
                raise ValueError("Could not guess processor from service.")
            
            module = ifaces[0].__module__
            thrift_service = __import__(module, fromlist=['Processor'], level=0)
            processor = thrift_service.Processor
        
        router = router or routers.default_router
        
        proxy = ThriftRoutingProxy(service, router)
        for i in ifaces:
            directlyProvides(proxy, i)
        
        super(ThriftBroker, self).__init__(
            processor=processor(proxy),
            iprot_factory=TBinaryProtocol.TBinaryProtocolFactory()
        )


class ThriftRoutingProxy(base.Broker):
    def __getattr__(self, name):
        try:
            return self.router(self.obj, name)
        except AttributeError:
            # We can trust thrift requests. If the prefixed method does not
            # exists, then thrift wants to access an attribute directly
            return getattr(self.obj, name)