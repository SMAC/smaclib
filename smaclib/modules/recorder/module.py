"""
Recorder module interface implementation with support for reservations.
"""

import os
import uuid

from lxml import etree

from smaclib.modules.base import Module
from smaclib import tasks
from smaclib.conf import settings

from twisted.internet import defer
from twisted.internet import reactor
from twisted.python import filepath
from twisted.python import log

from twisted.internet import protocol, error
from twisted.python import failure
from twisted.protocols import basic


class UnexpectedData(Exception):
    pass


class IVC4300Protocol(basic.LineReceiver, object):
    delimiter = '\n'

    def __init__(self):
        self.data = defer.Deferred()

    def connectionMade(self):
        log.msg("Process connected")
        self.factory.onConnectionMade.callback(self)

    def connectionLost(self, failure):
        failure.trap(error.ConnectionDone)
        self.factory.onConnectionLost.callback(self)

    @defer.inlineCallbacks
    def start(self):
        yield self.waitForCommand('Init OK')
        yield self.sendStart()

    @defer.inlineCallbacks
    def stop(self):
        yield self.sendStop()

    def lineReceived(self, data):
        self.data, d = defer.Deferred(), self.data
        d.callback(data)

    def sendStart(self):
        log.msg("Sending start")
        self.sendLine('START')
        return self.waitForCommand('OK')

    def sendStop(self):
        log.msg("Sending stop")
        self.sendLine('STOP')
        return self.waitForCommand('OK')

    def waitForCommand(self, cmd):
        log.msg("Waiting for '{0}'".format(cmd))
        d = defer.Deferred()

        def fire(data, d, cmd):
            if data == cmd:
                log.msg("Command '{0}' received".format(cmd))
                d.callback(None)
            else:
                log.msg("Unexpected '{0}' received".format(data))
                d.errback(failure.Failure(UnexpectedData(data)))
            return None

        self.data.addCallback(fire, d, cmd)

        return d


class IVC4300Process(protocol.ProcessProtocol):

    def __init__(self, stopped):
        self.processStopped = stopped
        self.out = ''

    def connectionMade(self):
        log.msg("Process started")

    def outReceived(self, data):
        self.out += data

    def processEnded(self, failure):
        try:
            failure.trap(error.ProcessDone)
            self.processStopped.callback(self.out)
        except:
            self.processStopped.errback(failure)


class Recorder(Module):

    def __init__(self):
        """
        Creates a new Archiver instance, using the FTP server bound to the
        transfers_registers realm for uploads and downloads.
        """
        super(Recorder, self).__init__()

        self.recording = False

        self.currentReservation = None
        """
        The ID of the current reservation. Set by the reserve method and
        cleared once the recording session is released. A value of None means
        that the capture module is available for a new recording.
        """

        # The three main methods of this module (reserve, start and stop) are
        # mutually exclusive and synchronized through this deferred lock.
        self.recordingLock = defer.DeferredLock()

    @defer.inlineCallbacks
    def remote_reserve(self, setup=None):
        """
        Setup the given session (error checking, directories creation,...) for
        the start action to take as little time as possible to begin to record.

        It is not possible to execute two reservations at the same time or when
        a capture is running.

        Returns a reservation ID to be used later to start, stop and archive
        the recording session.
        """

        #TODO: Implement reservation and setup system

        yield self.recordingLock.acquire()

        try:
            if self.currentReservation:
                raise RuntimeError("Recorder already reserved")

            # Generate a reservation ID
            resId = str(uuid.uuid4()) # Too long for the current binary

            # Setup directory structure
            dest = settings.data_root.child('current')
            #resId = dest.basename() # Too long for the current binary
            #print len(resId)
            #
            #resId = resId[:16]
            #dest = dest.sibling(resId)
            
            if dest.exists():
                dest.remove()
            
            dest.makedirs()

            # Create configuration file and put it into place
            from smaclib import xml

            trans = xml.Transformation(filepath.FilePath(__file__).sibling('config.xsl').path)

            trans.parameters['destination'] = "'{0}'".format(settings.data_root.path)
            trans.parameters['reservationID'] = "'{0}'".format('current')

            trans.transform(
                filepath.FilePath(__file__).sibling('base.xml').path,
                settings.recording_executable.sibling('CaptureConfig.xml').path
            )

            # Mark the module as reserved
            self.currentReservation = resId

            defer.returnValue(resId)
        finally:
            self.recordingLock.release()


    @defer.inlineCallbacks
    def remote_startRecording(self, reservation_id):
        # Reservation ID not used yet, always using a default configuration

        yield self.recordingLock.acquire()

        try:
            if self.currentReservation != reservation_id:
                raise RuntimeError("Invalid reservation ID")

            if self.recording:
                raise RuntimeError("Already recording")

            # Start recording
            started = defer.Deferred()
            self.serverStopped = defer.Deferred()
            self.processStopped = defer.Deferred()

            fact = protocol.Factory()
            fact.protocol = IVC4300Protocol
            fact.onConnectionMade = started
            fact.onConnectionLost = self.serverStopped

            proc = IVC4300Process(self.processStopped)

            path, bin = settings.recording_executable.splitext()

            PORT = 6544
            port = reactor.listenTCP(PORT, fact)
            
            exc = settings.recording_executable
            bin = exc.basename()
            path = exc.dirname()
            
            reactor.spawnProcess(proc, exc.path, [bin,], {}, path)

            self.protocol = yield started
            self.portStopped = defer.maybeDeferred(port.stopListening)
            self.portStopped.addCallback(lambda _: log.msg("Stopped listening"))
            yield self.protocol.start()

            self.recording = True

            print "Start recording session"

        finally:
            self.recordingLock.release()

    @defer.inlineCallbacks
    def remote_stopRecording(self, reservation_id):

        yield self.recordingLock.acquire()

        try:
            if self.currentReservation != reservation_id:
                raise RuntimeError("Invalid reservation ID")
            
            if not self.recording:
                raise RuntimeError("Not recording")

            self.protocol.stop().addCallback(lambda _: log.msg("Stop signal sent"))

            d1 = self.processStopped.addCallback(lambda r: log.msg("Process exited") or r)
            d2 = self.serverStopped.addCallback(lambda _: log.msg("Server stopped"))
            
            try:
                yield d1
            except error.ProcessTerminated:
                pass
            
            yield d2
            
            # Find files
            files = {}
            dest = settings.data_root.child('current')
            l = len(dest.path) + 1
            for child in dest.children():
                key = str(uuid.uuid4())
                _, ext = child.splitext()
                files[key] = child.path[l:]
                child.moveTo(settings.data_root.child(key + ext))
            
            self.recording = False
            self.currentReservation = None
            
            defer.returnValue(files)
        finally:
            self.recordingLock.release()


    def remote_archive(self, asset_id, upload_slot=None):
        settings.data_root.globChildren(asset_id + '.*')[0].remove()

