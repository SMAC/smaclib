"""
OpenOffice Document conversion server
-------------------------------------

A server for local to local conversions of any OpenOffice.org readable document
to its PDF counterpart.

The protocol is line based: each line contains two space separated paths.
The first path is the path to the document to convert, the second one is the
destination of the resulting asset.

The response (always line based) contains the response code for the operation:
0 for a successfull operation, a positive integer as error code if the
operation failed.

.. todo::
   Error reporting to the client

"""


import os
import tempfile

from smaclib import process, utils

from twisted.application import internet
from twisted.internet import defer
from twisted.internet import error
from twisted.internet import reactor
from twisted.internet import protocol
from twisted.protocols import basic
from twisted.python import log
from twisted.python import filepath


class RemoteConversionError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
    
    def __str__(self):
        return 'Remote conversion error ({0:d}): {1!s}'.format(self.code,
                                                               self.message)


class ConversionService(internet.TCPServer, object):
    """
    A conversion service listening for incoming TCP connections.
    """

    def __init__(self, port, interface=''):
        factory = ConverterServerFactory()
        super(ConversionService, self).__init__(port, factory,
                                                interface=interface)


class ConversionClientProtocol(basic.LineReceiver):
    def __init__(self, result, source, target):
        self.result = result
        self.source = source
        self.target = target
    
    def connectionMade(self):
        self.sendLine(self.source)
        self.sendLine(self.target)
    
    def lineReceived(self, line):
        code, message = line.split(' ', 1)
        code = int(code)
        
        if code == 200:
            self.result.callback(None)
        else:
            self.result.errback(RemoteConversionError(code, message))


def remoteConversion(host, port, source, target):
    """
    Executes a conversion on a remote server by instantiating a TCP connection
    to the conversion server listening at ``host:port`` and requesting a
    conversion from ``source`` to ``target`` as soon as the connection is made.
    
    Returns a deferred which will fire upon successful conversion.
    
    :param host: The hostname of the remote server
    :param port: The port to which connect to
    :param source: The path of the source file
    :param target: The path of the destination file
    :type host: str
    :type port: int
    :type source: str
    :type target: str
    :rtype: twisted.internet.defer.Deferred
    """
    d = defer.Deferred()
    creator = protocol.ClientCreator(reactor, ConversionClientProtocol,
                                     d, source, target)
    creator.connectTCP(host, port)
    return d


class ConverterServerProtocol(basic.LineReceiver):

    def __init__(self):
        self.source = None
        self.dest = None

    def lineReceived(self, line):
        if not self.source:
            self.source = line
        elif not self.dest:
            self.dest = line

        if self.dest:
            d = self.factory.convert(self.source, self.dest)
            d.addCallbacks(self.conversionSuccessful, self.conversionError)

    def conversionSuccessful(self, _):
        self.sendLine('200 OK')
        self.transport.loseConnection()

    def conversionError(self, failure):
        self.transport.write('500 ' + str(failure.value) + "\n")
        self.transport.loseConnection()


class ConverterProcessProtocol(process.LineProcessProtocol):
    def __init__(self, exited, job_id):
        super(ConverterProcessProtocol, self).__init__()
        self.job_id = job_id
        self.exited = exited

    def errLineReceived(self, line):
        line = line.strip()
        
        if line:
            log.msg("JID {0} - {1}".format(self.job_id, line))

    def processEnded(self, reason):
        if reason.check(error.ProcessDone):
            self.exited.callback(self.job_id)
        else:
            self.exited.errback((self.job_id, reason))

class ConverterServerFactory(protocol.ServerFactory):
    protocol = ConverterServerProtocol

    def __init__(self):
        self.queue = defer.DeferredLock()
        self.jobs = 0

    def getJobID(self):
        self.jobs += 1
        return self.jobs - 1

    def convert(self, source, target):
        jid = self.getJobID()

        source = filepath.FilePath(source)
        target = filepath.FilePath(target)
        
        log.msg("JID {0} - New job received ({1} > {2})".format(
            jid, source.path, target.path
        ))

        if not source.exists() or not source.isfile():
            log.msg("JID {0} - Source file not found ({1})".format(
                jid, source
            ))
            return defer.fail("No such file {0}".format(source.path))

        return self.runConversion(jid, source, target)

    @defer.inlineCallbacks
    def runConversion(self, job_id, source, target, format='pdf'):
        tempdir = filepath.FilePath(tempfile.mkdtemp(suffix='-unoconv'))
        tempsrc = tempdir.child(source.basename())

        source.copyTo(tempsrc)

        bin = "unoconv"

        args = ["-v"] * 5 + [
            "-f", format,
            "-T", "10",
            tempsrc.path,
        ]

        yield self.queue.acquire()

        log.msg("JID {0} - Spawning conversion process".format(job_id))

        try:
            d = defer.Deferred()
            prot = ConverterProcessProtocol(d, job_id)
            reactor.spawnProcess(prot, bin, [bin] + args, env=os.environ)
            d.addCallback(self.handleResult, tempsrc, target)
            d.addErrback(self.handleError, tempdir)
            result = yield d
        except:
            raise
        finally:
            # Release the lock only after some time to make sure all uno
            # resources are freed before restarting the service.
            utils.sleep(10).addCallback(lambda _: self.queue.release())

        defer.returnValue(result)

    def handleResult(self, job_id, source, target):
        log.msg("JID {0} - Conversion done, moving asset to final " \
                "destination".format(job_id))

        result = source.parent().globChildren('*.pdf')[0]
        result.moveTo(target)

        log.msg("JID {0} - Cleaning up temporary files".format(job_id))

        source.parent().remove()

    @defer.inlineCallbacks
    def handleError(self, result, source):
        job_id, failure = result

        log.err(failure.value, "JID {0} - Conversion failed".format(job_id))

        try:
            yield failure.value.processEnded
        except error.ProcessDone:
            pass

        log.msg("JID {0} - Cleaning up temporary files".format(job_id))

        source.remove()

        raise failure.value


