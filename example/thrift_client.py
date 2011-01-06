from twisted.internet import reactor
from twisted.internet.protocol import ClientCreator
from thrift.transport import TTwisted
from thrift.protocol import TBinaryProtocol
from smaclib.api.module import Module


def printValue(value, proto):
    print repr(value)
    proto.client.shutdown()


def printError(error):
    print 'error', error
    reactor.stop()


def got_proto(proto):
    # now actually make a thrift call and print the results
    proto.client.ping().addCallbacks(printValue, printError, [proto])


ClientCreator(
    reactor,
    TTwisted.ThriftClientProtocol,
    client_class=Module.Client,
    iprot_factory=TBinaryProtocol.TBinaryProtocolFactory(),
).connectTCP("127.0.0.1", 7081).addCallback(got_proto)


reactor.run()