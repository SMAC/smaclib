"""

"""


from __future__ import absolute_import

import uuid
import os
from functools import partial

from twisted.cred import portal
from twisted.internet import defer
from twisted.internet import threads
from twisted.python import log
from twisted.protocols import ftp
from twisted.protocols.ftp import FTPFactory

from zope.interface import implements

from smaclib.conf import settings


__all__ = ['FTPFactory', 'TransfersRegister']


class TransfersRegister(object):
    """
    A register to keep track of running transfers an their avatars.
    """

    implements(portal.IRealm)

    def __init__(self, downloads_root, uploads_root, completed_root):
        self.downloads_root = self.assureExists(downloads_root)
        self.uploads_root = self.assureExists(uploads_root)
        self.completed_root = self.assureExists(completed_root)

    def assureExists(self, directory):
        if not directory.exists():
            # Logging not yet started
            #log.msg("Creating {0}".format(directory))
            print "Creating '{0}'".format(directory.path)
            directory.makedirs()
        
        return directory

    def cleanAll(self):
        self.downloads_root.remove()
        self.uploads_root.remove()
        self.completed_root.remove()

    def address_by_id(self, uid):
        return 'ftp://{0}@{1}:{2}'.format(uid, settings.ftp_server_ip,
                                       settings.ftp_server_port)

    def allocate_upload_slot(self, name=None):
        """
        Create a new upload slot and register the relative avatar. Returns the
        name of the newly created upload slot and a deferred which fires upon
        upload completion with the path to the uploaded file.
        """
        if name is None:
            name = str(uuid.uuid4())
        try:
            self.uploads_root.child(name).makedirs()
        except:
            pass
        return name

    def allocate_download_slot(self, name=None):
        """
        Create a new upload slot and register the relative avatar. Returns the
        name of the newly created upload slot and a deferred which fires upon
        upload completion with the path to the uploaded file.
        """
        if name is None:
            name = str(uuid.uuid4())
        try:
            self.downloads_root.child(name).makedirs()
        except:
            pass
        return name

    def deallocate_upload_slot(self, name):
        slot = self.uploads_root.child(name)
        if slot.exists():
            slot.remove()
    
    def deallocate_download_slot(self, name):
        slot = self.downloads_root.child(name)
        if slot.exists():
            slot.remove()

    def download_slot_consumed(self, avatar_id, filename):
        self.deallocate_download_slot(avatar_id)

    def upload_slot_consumed(self, avatar_id, filename):
        # Create a new empty file to mark the slot as consumed in the case
        # someone connects between the file move operation and the deletion
        # of the directory.
        flag = self.uploads_root.child(avatar_id).child('completed')
        if flag == filename:
            # Someone uploaded a file named completed, can't use it as flag
            flag.path += '.flag'
        flag.touch()

        # Now move the uploaded file to its final destination, but in a new
        # thread to prevent rename operations between different disks to block
        # the reactor.
        # TODO: The blocking behavior refers to windows based operating
        # systems, but there is a comment in twisted/python/filepath.py:926
        # indicating that such a behavior is not supported on linux hosts.
        # Investigate and provide a correct solution if needed.
        # Anyway, the two directories (uploads_root and completed_root)
        # should really be on the same file system.
        extension = filename.splitext()[1]
        destination = self.completed_root.child(avatar_id).path + extension
        d = threads.deferToThread(os.rename, filename.path, destination)

        # Deallocate the slot once the transfer is completed
        d.addCallback(lambda _: self.deallocate_upload_slot(avatar_id))

    def get_upload_directory(self, avatar_id):
        return self.uploads_root.child(avatar_id)

    def get_download_directory(self, avatar_id):
        return self.downloads_root.child(avatar_id)

    def requestAvatar(self, avatar_id, mind, *interfaces):
        for iface in interfaces:
            if iface is ftp.IFTPShell:
                upload_directory = self.get_upload_directory(avatar_id)
                download_directory = self.get_download_directory(avatar_id)
                
                logout = lambda: None
                
                if upload_directory.exists():
                    cb = partial(self.upload_slot_consumed, avatar_id)
                    avatar = FTPUploadSlot(upload_directory, cb)
                elif download_directory.exists():
                    cb = partial(self.download_slot_consumed, avatar_id)
                    avatar = FTPDownloadSlot(download_directory, cb)
                else:
                    raise AssertionError("Authentication failure")

                return (ftp.IFTPShell, avatar, logout)

        raise NotImplementedError(
            "Only IFTPShell interface is supported by this realm")


class FTPTransferSlot(ftp.FTPShell, object):

    def __init__(self, transfer_root, completion_callback):
        super(FTPTransferSlot, self).__init__(transfer_root)
        self.transfer_root = transfer_root
        self.completion_callback = completion_callback
        self.already_consumed = bool(self.transfer_root.listdir())
    
    def _path(self, path):
        path = super(FTPTransferSlot, self)._path(path)
        path.changed() # Don't cache anything please
        return path
    
    def makeDirectory(self, path):
        return defer.fail(ftp.PermissionDeniedError("MKD not allowed"))

    def removeDirectory(self, path):
        return defer.fail(ftp.PermissionDeniedError("RMD not allowed"))

    def removeFile(self, path):
        return defer.fail(ftp.PermissionDeniedError("DELE not allowed"))

    def rename(self, from_path, to_path):
        return defer.fail(ftp.PermissionDeniedError("RNTO not allowed"))

    def access(self, path):
        return defer.fail(ftp.PermissionDeniedError("CWD not allowed"))

    def openForReading(self, path):
        return defer.fail(ftp.PermissionDeniedError("RETR not allowed"))

    def openForWriting(self, path):
        return defer.fail(ftp.PermissionDeniedError("STOR not allowed"))


class FTPDownloadSlot(FTPTransferSlot):
    
    def logout(self):
        """
        Checks if the user uploaded a file and fires the completion_callback
        if needed.
        """
        self.transfer_root.changed()
        if not self.transfer_root.exists():
            # Already uploaded by a concurrent connection
            return
        
        if hasattr(self, 'successfully_read'):
            self.completion_callback(self.transfer_root)
        
    def access(self, path):
        return super(FTPTransferSlot, self).access(path)
    
    def readCompleted(self, result):
        self.successfully_read = True
    
    def openForReading(self, path):
        p = self._path(path)
        
        if p.isdir():
            return defer.fail(ftp.IsADirectoryError(path))
        
        try:
            f = p.open('r')
        except (IOError, OSError), e:
            return ftp.errnoToFailure(e.errno, path)
        except:
            return defer.fail()
        else:
            reader = _FileReader(f)
            reader.completed.addCallback(self.readCompleted)
            return defer.succeed(reader)


class _FileReader(ftp._FileReader):
    def __init__(self, fObj):
        super(_FileReader, self).__init__(fObj)
        self.completed = defer.Deferred()
        
    def send(self, consumer):
        d = super(_FileReader, self).send(consumer)
        d.chainDeferred(self.completed)
        return d


class FTPUploadSlot(FTPTransferSlot):
    def logout(self):
        """
        Checks if the user uploaded a file and fires the completion_callback
        if needed.
        """
        if self.already_consumed:
            return
        
        self.transfer_root.changed()
        if not self.transfer_root.exists():
            # Already uploaded by a concurrent connection
            return
        
        files = self.transfer_root.listdir()
        if files:
            self.completion_callback(self.transfer_root.child(files[0]))

    def openForWriting(self, path):
        msg = None
        self.transfer_root.changed()
        
        if not self.transfer_root.exists():
            # Probably a concurrent connection has already uploaded a file
            # here and closed before this one.
            return defer.fail(ftp.FileNotFoundError(self.transfer_root.path))
        
        if self.transfer_root.listdir():
            # There is already a file here...
            msg = "STOR not allowed, upload slot already used"
        elif len(path) != 1:
            # Want to write where you can't...
            msg = "STOR not allowed"
        elif path[0].startswith('.'):
            # Too much trouble handling hidden files (os.listdir does not list
            # them by default, and so doesn't filepath.listdir)
            msg = "STOR of hidden files not allowed"
        
        if msg:
            return defer.fail(ftp.PermissionDeniedError(msg))
        else:
            return super(FTPTransferSlot, self).openForWriting(path)

