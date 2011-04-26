"""
Archiver module interface implementation with FTP based file serving.
"""

import itertools
import os
import tarfile
import tempfile
import warnings

from smaclib.api.errors import ttypes as error
from smaclib.db.mongo import ObjectId
from smaclib.conf import settings
from smaclib.utils import sleep
from smaclib import tasks
from smaclib.modules.base import Module
from smaclib.modules.archiver import triggers
from smaclib.modules.archiver import workflow
from smaclib.models.assets import Asset, AssetVersion

from twisted.internet import defer
from twisted.internet import threads
from twisted.python import filepath

from lxml import etree


class Archiver(Module):
    """
    Archiver module for SMAC. Manages assets such as video/audio streams,
    PDF documents, slideshows and related media.

    Is also responsible for the conversion of media such as videos in a format
    suitable for publication.
    """

    def __init__(self, transfers_register):
        """
        Creates a new Archiver instance, using the FTP server bound to the
        transfers_registers realm for uploads and downloads.
        """
        super(Archiver, self).__init__()
        self.transfers_register = transfers_register

        # Read the available workflows
        self.loadWorkflows(settings.workflows_root)

    def loadWorkflows(self, path):
        """
        Parses and validates all workflows found in the ``path`` directory and
        registers their triggers to be processed for each incoming upload.

        The validation is performed by validation the workflow document against
        the ``<path>/workflow.xsd`` XML schema. If the validation fails a
        warning is emitted and the workflow ignored.

        .. note::
           A warning is emitted insted of logging the error because this method
           is intended to be called at startup time and thus:

            1. The logging subsystem is not yet configured
            2. The error is displayed before the module is demonized

        :param path: The path to the directory containing the workflows.
        :type path: twisted.python.filepath.FilePath
        """

        # Load validation schema
        schema_doc = etree.parse(path.child('workflow.xsd').open())
        schema = etree.XMLSchema(schema_doc)

        self.triggers = {}

        # Process each workflow
        for workflow_definition in path.globChildren('*.xml'):
            # Load
            with workflow_definition.open() as fh:
                doc = etree.parse(fh)

            # Validate
            try:
                schema.assertValid(doc)
            except etree.DocumentInvalid as e:
                warnings.warn("Ignoring invalid workflow {0}:\n{1}".format(
                              workflow_definition.path, e), RuntimeWarning)
                continue

            # Create the trigger
            trigger = triggers.Trigger()
            trigger.parse(doc)
            self.triggers[trigger] = workflow_definition

    def processAsset(self, asset):
        """
        This method is called once the first phase of the archiving
        process (moving to the final destination and saving to the database) is
        completed and the asset is ready to be processed.

        The processing consist of two phases:

         1. Select the workflows to apply to this asset by evaluating the
            triggers
         2. Load, parse and run the selected workflows

        :param asset: The model instance of the asset to process.
        :type asset: smaclib.models.assets.Asset

        .. todo::
           Provide a working implementation
        """

        task_list = []

        for trigger, path in self.triggers.iteritems():
            if trigger.evaluate(asset):
                task = workflow.Workflow(asset, path).getTask()
                self.task_manager.schedule(task)
                task_list.append(task)

        filename = asset.versions[0].filename.path
        name = "Running workflows for {0}".format(filename)
        compound_task = tasks.SimpleCompositeTask(name, task_list)
        self.task_manager.register(compound_task)
        return compound_task

    @defer.inlineCallbacks
    def remote_requestDownloadSlot(self, version_id):
        """
        Creates a new FTP backed download slot and returns the full FTP address
        to the client.
        """
        _, version = yield Asset.collection.find_version(version_id)

        # Create a new upload slot by using the transfers register
        slot_id = self.transfers_register.allocate_download_slot()

        source = version.filename
        target = self.transfers_register.get_download_directory(slot_id)
        target = target.child(source.basename())
        source.linkTo(target)

        url = self.transfers_register.address_by_id(slot_id)
        url = os.path.join(url, source.basename())

        # Create the complete ftp address
        defer.returnValue(url)

    def remote_requestUploadSlot(self):
        """
        Creates a new FTP backed upload slot and returns the full FTP address
        to the client.

        The FTP user is the same as the final upload ID of the file which is
        going to be added.
        """
        # Create a new upload slot by using the transfers register
        slot_id = self.transfers_register.allocate_upload_slot()

        # Create the complete ftp address
        return self.transfers_register.address_by_id(slot_id)

    def remote_abortUpload(self, upload_id):
        """
        Allows a client to abort a not yet completed upload by providing its ID.
        Clean up all resources coupled with the allocated upload slot.

        .. todo::
           Thoroughly test this behavior and the behavior of the FTP server.
           Add auto-cleaning capabilities after a certain time-out and check
           the effect of calling abortUpload with the connection still open and
           the client still transferring data.
        """
        self.transfers_register.deallocate_upload_slot(upload_id)

        # Also remove the file if the upload is already completed
        completed = settings.completed_root.child(upload_id)
        if completed.exists():
            completed.remove()

    @staticmethod
    def buildVersionsBundle(asset):
        tarname = str(asset.pk) + '-bundle.tar.gz'

        tempdir = tempfile.mkdtemp(prefix='smac-', suffix='-' + str(asset.pk) + '-bundle')
        tempdir = filepath.FilePath(tempdir)
        temptar = tempdir.child(tarname)

        # TODO: Use context manager protocol once switched to python 2.7
        bundle = tarfile.open(name=temptar.path, mode='w:gz')
        for version in asset.versions:
            f = version.filename

            if f.path.endswith('-bundle.tar.gz'):
                continue

            bundle.add(f.path, f.basename())
        bundle.close()
        del bundle

        # Move to final destination
        tardest = asset.original.filename.parent().child(tarname)
        temptar.moveTo(tardest)

        # Delete temp directory
        tempdir.remove()

        return tardest

    @staticmethod
    def buildPublishingBundle(talk_id, files, tardest):
        tempdir = tempfile.mkdtemp(prefix='smac-', suffix='-' + talk_id + '-bundle')
        tempdir = filepath.FilePath(tempdir)
        temptar = tempdir.child(tardest.basename())

        # TODO: Use context manager protocol once switched to python 2.7
        bundle = tarfile.open(name=temptar.path, mode='w:gz')
        for path, filename in files:
            bundle.add(path, filename)
        bundle.close()
        del bundle

        # Move to final destination
        temptar.moveTo(tardest)

        # Delete temp directory
        tempdir.remove()

        return tardest

    @defer.inlineCallbacks
    def remote_requestPublishingSlot(self, talk_id):
        assets = yield Asset.collection.find({'talk_id': talk_id})

        # Filter assets
        def take(version):
            base, ext = version.filename.splitext()
            return ext not in ('.gz', '.tar', '.avi')

        dest = settings.data_root.child(talk_id).child(talk_id + '-bundle.tar.gz')
        l = len(dest.parent().path)

        versions = itertools.chain(*[a.versions for a in assets])
        versions = [v for v in versions if take(v)]
        versions = [v.filename for v in versions]
        
        # Check creation date
        if dest.exists():
            mtime = dest.getModificationTime()
            
            for version in versions:
                if version.getModificationTime() > mtime:
                    versions = [(v.path, v.path[l+1:]) for v in versions]
                    source = yield threads.deferToThread(self.buildPublishingBundle, talk_id, versions, dest)
                    break
            else:
                # Don't rebuild it
                source = dest
        
        slot_id = self.transfers_register.allocate_download_slot()

        target = self.transfers_register.get_download_directory(slot_id)
        target = target.child(source.basename())
        source.linkTo(target)

        url = self.transfers_register.address_by_id(slot_id)
        url = os.path.join(url, source.basename())

        # Create the complete ftp address
        defer.returnValue(url)

    @defer.inlineCallbacks
    def remote_updateVersionsBundle(self, document_id):
        """
        TODO: Add this to the workflow and do it automatically. Maybe wrap it
              in a task.
        """

        asset = yield Asset.collection.one({
            '_id': ObjectId(document_id),
        })

        dest = yield threads.deferToThread(self.buildVersionsBundle, asset)

        if asset.bundle is None:
            asset.versions.append(AssetVersion(
                version_id=ObjectId(),
                filename=dest
            ))
            yield asset.save()

        defer.returnValue(str(asset.bundle.version_id))

    @defer.inlineCallbacks
    def remote_archiveSlideshowMetadata(self, slideshow_id, upload_id):
        source = yield self.getUpload(upload_id)
        extension = source.splitext()[1]

        asset = yield Asset.collection.one({
            '_id': ObjectId(slideshow_id),
            'role': 'slideshow',
        })
        destination = settings.data_root.child(asset.talk_id) \
                                        .child(asset.role) \
                                        .child(str(asset.pk) + '-metadata' + extension)
        source.moveTo(destination)

        if asset.metadata is None:
            asset.versions.append(AssetVersion(
                version_id=ObjectId(),
                filename=destination
            ))
            yield asset.save()

        defer.returnValue(str(asset.metadata.version_id))

    @defer.inlineCallbacks
    def remote_archiveVideoSegmentation(self, video_id, upload_id):
        source = yield self.getUpload(upload_id)
        extension = source.splitext()[1]

        asset = yield Asset.collection.one({
            '_id': ObjectId(video_id),
            'role': 'video',
        })
        destination = settings.data_root.child(asset.talk_id) \
                                        .child(asset.role) \
                                        .child(str(asset.pk) + '-segmentation' + extension)
        source.moveTo(destination)
        if asset.segmentation is None:
            asset.versions.append(AssetVersion(
                version_id=ObjectId(),
                filename=destination
            ))
            yield asset.save()

        defer.returnValue(str(asset.segmentation.version_id))


    @defer.inlineCallbacks
    def getUpload(self, upload_id):
        # 1. Santiy check and initialization
        source = settings.completed_root.globChildren(upload_id + '.*')
        if not source:
            # Before raising an InvalidUploadID exception, let some grace
            # period to allow to close the ftp connection/move the file if the
            # client is too fast.

            yield sleep(2)

            source = settings.completed_root.globChildren(upload_id + '.*')

            # If the file still does not exists, throw the exception
            if not source:
                raise error.InvalidUploadID(upload_id)
        defer.returnValue(source[0])

    @defer.inlineCallbacks
    def remote_archiveUpload(self, talk_id, upload_id, role):
        """
        Moves a file to its final destination and add information about it
        to the database.
        """
        source = yield self.getUpload(upload_id)
        extension = source.splitext()[1]

        # TODO: Check if the talk identified by talk_id exists and bind the
        #       document to it.

        # TODO: Validate the given ``role`` argument (either strictly against a
        #       list of known roles or loosely for sanity).

        # 2. Construct the final pathname
        version_id = ObjectId()
        basename = str(version_id) + extension
        destination = settings.data_root.child(talk_id).child(role)
        if not destination.exists():
            destination.makedirs()
        destination = destination.child(basename)

        # 3. move the file to its destination
        yield threads.deferToThread(source.moveTo, destination)

        # 2. Save the info to the database
        asset = Asset(
            _id=version_id,
            archiver_id=self.getID(),
            talk_id=talk_id,
            role=role
        )
        version = AssetVersion(
            version_id=version_id,
            filename=destination
        )
        asset.versions.append(version)

        yield asset.save()

        # 5. Start the upload triggers
        task = self.processAsset(asset)

        # TODO: Define the return value of this method. Shall it be the task,
        #       the version_id/asset_id or both?
        defer.returnValue((str(version_id), task.id))

    def remote_triggerWorkflow(self, asset_id, workflow):
        raise NotImplementedError()



