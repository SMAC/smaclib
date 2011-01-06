#!/usr/bin/thrift --gen py:twisted

# Copyright (C) 2005-2010  MISG/ICTI/EIA-FR
# See LICENSE for details.


include "module.thrift"

namespace py smaclib.api.analyser


typedef string AssetID
typedef string TaskID

/** @TODO: Define following types */
typedef i16 VideoInfo
typedef i16 SlideshowInfo


service Analyser extends module.Module {
    /**
     * Analyze the video stream identified by asset_id to obtain segmentation
     * information.
     */
    TaskID analyse_video(1: AssetID video_id, 2: VideoInfo info),

    /**
     * Extract the slide images from the slideshow identified by asset_id.
     */
    TaskID analyse_slideshow(1: AssetID slideshow_id, 2: SlideshowInfo info),

    /**
     * Analyze the document file identified by asset_id to extract the
     * relevant information.
     *
     * The analyser to be used is chosen based on the mime-type of the
     * document.
     */
    TaskID analyse_document(1: AssetID document_id),

    TaskID synchronize_slideshow(1: AssetID video_id, 2: AssetID slideshow_id,
        3: VideoInfo video_segments, 4: VideoInfo slides_file_segments, 5: VideoInfo frames, 6: VideoInfo slides),

    /**
     * Deprecated/never implemented function to synchronize a given document
     * with a video stream.
     */
    //synchronize_document
}
