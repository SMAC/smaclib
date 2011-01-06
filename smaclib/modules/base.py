
from smaclib.api.module import Module

from twisted.internet import reactor

from zope.interface import implements


class Module(object):
    
    implements(Module.Iface)
    
    def ping(self):
        print "Pinged"
    
    def restart(self):
        print "Restart"
    
    def shutdown(self):
        print "Stopping"
        reactor.stop()
    


