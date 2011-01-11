"""

"""


from __future__ import absolute_import

from thrift.transport import TTwisted
from thrift.protocol import TBinaryProtocol

from zope.interface import providedBy


class ThriftBroker(TTwisted.ThriftServerFactory, object):
    def __init__(self, service, processor=None):
        
        if processor is None:
            ifaces = list(providedBy(service))
            
            if not ifaces:
                raise ValueError("This service provides no interfaces.")
            
            if len(ifaces) > 1:
                raise ValueError("Could not guess processor from service.")
            
            module = ifaces[0].__module__
            thrift_service = __import__(module, fromlist=['Processor'], level=0)
            processor = thrift_service.Processor
        
        super(ThriftBroker, self).__init__(
            processor=processor(service),
            iprot_factory=TBinaryProtocol.TBinaryProtocolFactory()
        )
