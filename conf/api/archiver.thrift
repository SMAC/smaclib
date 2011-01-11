#!/usr/bin/thrift --gen py:twisted

# Copyright (C) 2005-2010  MISG/ICTI/EIA-FR
# See LICENSE for details.


include "errors.thrift"
include "types.thrift"
include "module.thrift"


namespace py smaclib.api.archiver


service Archiver extends module.Module {
    /**
     * Creates an upload slot for a general file. Returns an address valid for
     * a single file upload.
     *
     * An uploaded file may then be processed using an archive_* method and
     * the ID of the uploaded file. The ID of the uploaded file can always be
     * inferred from the upload URI.
     *
     * The default implementation provides FTP based slots, where the URI
     * is a complete FTP address to a directory where a file shall be
     * uploaded; in this case the upload ID is the FTP user and the remote
     * filename is not relevant.
     */
    types.URI request_upload_slot()

    /**
     * Aborts a not yet processed upload.
     */
    void abort_upload(1: types.UploadID upload_id)

    /**
     * Archives (and thus confirms) a successfull upload.
     *
     * The file_info struct has to contain at least the values for the mime
     * type and, if validation is desired, the sha1 checksum of the
     * transferred asset.
     */
    types.VersionID archive_upload(1: types.TalkID talk_id,
                                   2: types.UploadID upload_id,
                                   3: types.FileInfo file_info)
                           throws (1: errors.InvalidUploadID upload_err,
                                   2: errors.UnknownMimetype mime_err)
    
    /**
     * Encodes a video stream from its original format to the given one if a
     * suitable encoder is available.
     *
     * The EncodingInfo struct carries informations about the output format,
     * such as encoding mimetype and bitrates for both audio and video.
     *
     * The video and audio bitrates can be a name of a preset to use (such as
     * default, speaker, slide,..) or a literal value (such as 64k, 150k,...).
     */
    types.TaskID encode_video(1: types.VersionID video_id,
                              2: types.EncodingInfo encoding_info)
                      throws (1: errors.AssetNotFound asset_err,
                              2: errors.InvalidFormat format_err,
                              3: errors.UnknownMimetype mime_err,
                              4: errors.NoSuitableEncoder encoder_err,
                              5: errors.InvalidBitrate bitrate_err)
}



/**
 * Analyze the video stream identified by asset_id to obtain segmentation
 * information.
 */
#convertImageJPEG           --> is this really needed?
#getArchivedFile            --> request_asset_download(AssetID)
#                           --> create_talk_archive(TalkInfo):TalkID
#removeContributionFiles    --> delete_talk_archive(TalkID)
#removeFile                 --> delete_asset(AssetID)
#extract_thumbnail          --> create_thumbnail(AssetID)


