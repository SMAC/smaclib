import os
import re
import urlparse

from smaclib import tasks
from smaclib import text

from zope.interface import implements
from twisted.internet import defer
from twisted.internet import reactor
from twisted.internet import protocol
from twisted.protocols import ftp
from twisted.python import filepath
from twisted.protocols import basic


class FileWriterProtocol(protocol.Protocol):
    def __init__(self, stream):
        self.stream = stream

    def dataReceived(self, data):
        self.stream.write(data)


def putFile(url, stream):
    url = urlparse.urlparse(url)

    username = url.username or ''
    password = url.password or ''
    port = url.port or 21
    
    def gotClient(client, path, fh):
        dC, dL = client.storeFile(path)
        dC.addCallback(sendfile, client, fh)
        dL.addCallback(lambda _: client)
        return dL
    
    def sendfile(consumer, client, fh):
        s = basic.FileSender()
        d = s.beginFileTransfer(fh, consumer)
        d.addCallback(lambda _: consumer.finish())
        
        return d
    
    def close(client):
        client.quit()
    
    creator = protocol.ClientCreator(reactor, ftp.FTPClient, username, password)
    
    d = creator.connectTCP(url.hostname, port)
    d.addCallback(gotClient, url.path, stream)
    d.addCallback(close)
    
    return d


def getFile(url, stream):
    url = urlparse.urlparse(url)

    username = url.username or ''
    password = url.password or ''
    port = url.port or 21

    def gotClient(client, path, size_protocol):
        client.list(path, size_protocol)
        return size_protocol.deferred.addCallback(lambda size: (size, client))

    def gotSize(res, path, recv_protocol):
        size, client = res
        return client.retrieveFile(path, recv_protocol).addCallback(lambda _: client)

    def close(client):
        return client.quit()

    class ListingProtocol(basic.LineReceiver):

        def __init__(self):
            self.deferred = defer.Deferred()

        def lineReceived(self, data):
            match = re.search(r'(?P<permissions>[rwx-]{9})\s+(?P<id>\d+)\s+(?P<user>\w+)\s+(?P<group>\w+)\s+(?P<size>\d+)\s+(?P<date>[A-Z][a-z]{2} \d{1,2} \d{1,2}:\d{1,2})\s+(?P<name>.+)', data)
            if match is None:
                return

            self.deferred.callback(int(match.group('size')))

    creator = protocol.ClientCreator(reactor, ftp.FTPClient, username, password)

    recv_protocol = FileWriterProtocol(stream)
    size_protocol = ListingProtocol()

    d = creator.connectTCP(url.hostname, port)
    d.addCallback(gotClient, url.path, size_protocol)
    d.addCallback(gotSize, url.path, recv_protocol)
    d.addCallback(close)

    return size_protocol.deferred, d


class FileDownloadTask(object):
    implements(tasks.ITaskRunner)

    title = "Downloading {path} ({size})..."

    def __init__(self, source=None, destination=None):
        self.source = source
        self.destination = destination
        self.task = tasks.Task("File transfer", self)
        self.received = 0
        self.size = 0

    @property
    def source(self):
        return self._source
    
    @source.setter
    def source(self, source):
        self._source = source
        self.name = os.path.basename(source)

    def getTask(self):
        return self.task

    def write(self, data):
        self.received += len(data)

        if self.size:
            self.task.completed = 1. * self.received / self.size

        self.destination.write(data)

    def start(self):
        if self.source is None or self.destination is None:
            raise RuntimeError("You have to set both the source and the destination.")
        
        self.task._statustext = self.title.format(path=self.source, size="unknown size")
        sd, fd = getFile(self.source, self)
        sd.addCallback(self.set_size)
        fd.addCallback(self.transfer_completed)

    def set_size(self, size):
        self.size = size
        self.task.statustext = self.title.format(path=self.name, size=text.format_size(self.size))
        return size

    def transfer_completed(self, _):
        self.task._statustext = "Download of {path} completed ({size})".format(path=self.name, size=text.format_size(self.size))
        self.task.callback(self.destination)


class FileUploadTask(object):
    implements(tasks.ITaskRunner)

    title = "Uploading {path} ({size})..."

    def __init__(self, source=None, destination=None):
        self.sent = 0
        self.source = source
        self.destination = destination
        self.task = tasks.Task("File transfer", self)

    @property
    def source(self):
        return self._source
    
    @source.setter
    def source(self, source):
        assert not self.sent

        self._source = source
        self.size = 0
        self.name = "Unknown stream"
        
        try:
            self.name = os.path.basename(source.name)
            self.size = filepath.FilePath(source.name).getsize()
        except:
            pass

    def getTask(self):
        return self.task

    def read(self, *args, **kwargs):
        # If a new chunk is read, then the previous chunk was sent; update the
        # task now
        if self.size:
            self.task.completed = 1. * self.sent / self.size

        chunk = self.source.read(*args, **kwargs)
        self.sent += len(chunk)

        return chunk

    def start(self):
        if self.source is None or self.destination is None:
            raise RuntimeError("You have to set both the source and the destination.")
        
        if self.size:
            size = text.format_size(self.size)
        else:
            size = "unknown size"
        
        self.task._statustext = self.title.format(path=self.name, size=size)
        fd = putFile(self.destination, self)
        fd.addCallback(self.transfer_completed)

    def transfer_completed(self, _):
        self.task._statustext = "Upload of {path} completed ({size})".format(path=self.name, size=text.format_size(self.sent))
        self.task.callback(self.destination)