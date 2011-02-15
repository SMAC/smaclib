from __future__ import absolute_import

from twisted.internet import reactor
from twisted.internet import defer

def sleep(time):
    d = defer.Deferred()
    reactor.callLater(time, d.callback, None)
    return d