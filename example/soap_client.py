from twisted.web.soap import Proxy
from twisted.internet import reactor


def printValue(value):
    print repr(value)
    reactor.stop()


def printError(error):
    print 'error', error
    reactor.stop()


proxy = Proxy('http://127.0.0.1:7080/SOAP')
proxy.callRemote('myself').addCallbacks(printValue, printError)
reactor.run()