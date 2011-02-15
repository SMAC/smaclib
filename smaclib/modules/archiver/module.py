"""
Archiver module interface implementation with FTP based file serving.
"""


import warnings

from smaclib.api.errors import ttypes as error
from smaclib.db.mongo import ObjectId
from smaclib.conf import settings
from smaclib.utils import sleep
from smaclib.modules.base import Module
from smaclib.modules.archiver import encoding
from smaclib.modules.archiver import triggers
from smaclib.modules.archiver import workflow
from smaclib.models.assets import Asset, AssetVersion

from twisted.internet import defer
from twisted.internet import threads

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
        
        for trigger, path in self.triggers.iteritems():
            if trigger.evaluate(asset):
                task = workflow.Workflow(asset, path).getTask()
                self.task_manager.schedule(task)

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

    @defer.inlineCallbacks
    def remote_archiveUpload(self, talk_id, upload_id, role):
        """
        Moves a file to its final destination and add information about it
        to the database.
        """
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
        source = source[0]
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
        defer.returnValue(str(version_id))


#    @defer.inlineCallbacks
#    def encode_video(self, video_id, encoding_info):
#        """
#        Transcodes the video identified by video_id to the format specified by
#        the format attribute of the encoding_info instance.
#        """
#        # 1. Get the asset from the database
#        try:
#            video, version = yield Asset.collection.find_version(video_id)
#        except Asset.DoesNotExist:
#            raise error.AssetNotFound(video_id)
#        else:
#            if version.mimetype.type != 'video':
#                raise error.InvalidFormat(video_id, str(version.mimetype))
#
#        # 2. Check destination format
#        source_extension = mimetypes.guess_extension(str(version.mimetype))
#        target_extension = mimetypes.guess_extension(encoding_info.mimetype)
#
#        if target_extension is None:
#            raise error.UnknownMimetype(encoding_info.mimetype)
#
#        encoder = encoding.FFmpegEncoder()
#
#        yield encoder.init()
#
#        if not encoder.can_decode(source_extension):
#            raise error.NoSuitableEncoder(str(version.mimetype))
#
#        if not encoder.can_encode(target_extension):
#            raise error.NoSuitableEncoder(encoding_info.mimetype)
#
#        # 3. Check and retrieve the bitrates.
#        def _bitrate(bitrate, presets, media):
#            """
#            Checks first in the given presets if a certain bitrate is present
#            and if not validates the provided value to check if it is a valid
#            bitrate representation.
#
#            If both fail, raises an error.InvalidBitrate exception with the
#            provided media type.
#            """
#            # First try to get them from the presets (allows the module to
#            # override provided values):
#            try:
#                bitrate = presets[bitrate]
#            except KeyError:
#                # Not provided in the presets, check if the value is a correct
#                # bitrate
#                if not encoder.validate_bitrate(bitrate):
#                    raise error.InvalidBitrate(media, bitrate)
#            else:
#                return bitrate
#
#        video_bitrate = _bitrate(encoding_info.video_bitrate,
#                                 settings.video_bitrates, "video")
#
#        audio_bitrate = _bitrate(encoding_info.audio_bitrate,
#                                 settings.audio_bitrates, "audio")
#
#        new_id = ObjectId()
#        basename = str(new_id) + target_extension
#        target = version.filename.parent().child(basename)
#
#        # 4. Add the new version to the asset
#        new_version = AssetVersion(
#            version_id=new_id,
#            mimetype=encoding_info.mimetype,
#            filename=target
#        )
#
#        video.versions.append(new_version)
#
#        yield video.save()
#
#        # 5. Start conversion process
#        encoder.flag('y') \
#               .read_from(version.filename.path) \
#               .option('vb', video_bitrate) \
#               .option('ab', audio_bitrate) \
#               .option('ar', settings.audio_sampling_rate) \
#               .write_to(target.path)
#
#        task = encoder.encode()
#
#        @defer.inlineCallbacks
#        def _save(result):
#            """
#            Inserts a new asset in the database by copying the old one.
#            """
#            new_version.archived = True
#            yield video.save()
#            defer.returnValue(result)
#
#        task.addCallback(_save)
#        self.task_manager.register(task)
#        defer.returnValue(task.id)

    def remote_triggerWorkflow(self, asset_id, workflow):
        raise NotImplementedError()



