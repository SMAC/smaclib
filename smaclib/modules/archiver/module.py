"""
Archiver module interface implementation with FTP based file serving.
"""


import mimetypes

from smaclib.api.errors import ttypes as error
from smaclib.db.mongo import ObjectId
from smaclib.conf import settings
from smaclib.modules.base import Module
from smaclib.modules.archiver import encoding
from smaclib.models.assets import Asset, AssetVersion

from twisted.internet import defer
from twisted.internet import threads


class Archiver(Module):
    """
    Archiver module for SMAC. Manages assets such as video/audio streams,
    PDF documents, slideshows and related media.

    Is also responsible for the conversion of media such as videos in a format
    suitable for pubblication.
    """

    def __init__(self, transfers_register):
        """
        Creates a new Archiver instance, using the FTP server bound to the
        transfers_registers realm for uploads and downloads.
        """
        super(Archiver, self).__init__()
        self.transfers_register = transfers_register

    def request_upload_slot(self):
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

    def abort_upload(self, upload_id):
        """
        Allows a client to abort a running upload by providing its ID.

        Clean up all resources coupled with the allocated upload slot.
        """
        self.transfers_register.deallocate_upload_slot(upload_id)

        # Also remove the file if the upload is already completed
        completed = settings.completed_root.child(upload_id)
        if completed.exists():
            completed.remove()

    @defer.inlineCallbacks
    def archive_upload(self, talk_id, upload_id, file_info):
        """
        Moves a file to its final destination and add information about it
        to the database.
        """
        # 1. Santiy check and initialization
        source = settings.completed_root.child(upload_id)
        extension = mimetypes.guess_extension(file_info.mimetype)
        mediatype = file_info.mimetype.split('/')[0]

        # TODO: Check if the talk identified by talk_id exists and bind the
        #       document to it.

        if not source.exists() or not source.isfile():
            raise error.InvalidUploadID(upload_id)

        if mediatype == 'application':
            mediatype = 'document'

        if extension is None:
            raise error.UnknownMimetype(file_info.mimetype)

        # 2. Construct the final pathname
        version_id = ObjectId()
        basename = str(version_id) + extension
        destination = settings.data_root.child(talk_id).child(mediatype)
        if not destination.exists():
            destination.makedirs()
        destination = destination.child(basename)

        # 2. Save the info to the database
        asset = Asset(archiver_id=self.get_id())
        version = AssetVersion(
            version_id=version_id,
            mimetype=file_info.mimetype,
            filename=destination
        )
        asset.versions.append(version)

        yield asset.save()

        # 4. move the file to its destination
        yield threads.deferToThread(source.moveTo, destination)

        version.archived = True

        yield asset.save()

        defer.returnValue(str(version_id))

    @defer.inlineCallbacks
    def encode_video(self, video_id, encoding_info):
        """
        Transcodes the video identified by video_id to the format specified by
        the format attribute of the encoding_info instance.
        """
        # 1. Get the asset from the database
        try:
            video, version = yield Asset.collection.find_version(video_id)
        except Asset.DoesNotExist:
            raise error.AssetNotFound(video_id)
        else:
            if version.mimetype.type != 'video':
                raise error.InvalidFormat(video_id, str(version.mimetype))

        # 2. Check destination format
        source_extension = mimetypes.guess_extension(str(version.mimetype))
        target_extension = mimetypes.guess_extension(encoding_info.mimetype)

        if target_extension is None:
            raise error.UnknownMimetype(encoding_info.mimetype)

        encoder = encoding.FFmpegEncoder()

        yield encoder.init()

        if not encoder.can_decode(source_extension):
            raise error.NoSuitableEncoder(str(version.mimetype))

        if not encoder.can_encode(target_extension):
            raise error.NoSuitableEncoder(encoding_info.mimetype)

        # 3. Check and retrieve the bitrates.
        def _bitrate(bitrate, presets, media):
            """
            Checks first in the given presets if a certain bitrate is present
            and if not validates the provided value to check if it is a valid
            bitrate representation.

            If both fail, raises an error.InvalidBitrate exception with the
            provided media type.
            """
            # First try to get them from the presets (allows the module to
            # override provided values):
            try:
                bitrate = presets[bitrate]
            except KeyError:
                # Not provided in the presets, check if the value is a correct
                # bitrate
                if not encoder.validate_bitrate(bitrate):
                    raise error.InvalidBitrate(media, bitrate)
            else:
                return bitrate

        video_bitrate = _bitrate(encoding_info.video_bitrate,
                                 settings.video_bitrates, "video")

        audio_bitrate = _bitrate(encoding_info.audio_bitrate,
                                 settings.audio_bitrates, "audio")

        new_id = ObjectId()
        basename = str(new_id) + target_extension
        target = version.filename.parent().child(basename)

        # 4. Add the new version to the asset
        new_version = AssetVersion(
            version_id=new_id,
            mimetype=encoding_info.mimetype,
            filename=target
        )

        video.versions.append(new_version)

        yield video.save()

        # 5. Start conversion process
        encoder.flag('y') \
               .read_from(version.filename.path) \
               .option('vb', video_bitrate) \
               .option('ab', audio_bitrate) \
               .option('ar', settings.audio_sampling_rate) \
               .write_to(target.path)

        task = encoder.encode()

        @defer.inlineCallbacks
        def _save(result):
            """
            Inserts a new asset in the database by copying the old one.
            """
            new_version.archived = True
            yield video.save()
            defer.returnValue(result)

        task.addCallback(_save)
        self.task_manager.register(task)
        defer.returnValue(task.id)


