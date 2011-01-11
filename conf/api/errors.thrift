

include "types.thrift"

namespace py smaclib.api.errors


const i16 UNKNOWN_MIMETYPE = 7000
const string UNKNOWN_MIMETYPE_MSG = "Unknown mime type: {mimetype}"

exception UnknownMimetype {
    1: Mimetype mimetype,
}


const i16 INVALID_UPLOAD_ID = 7001
const string INVALID_UPLOAD_ID_MSG = "Invalid upload id: {upload_id}"

exception InvalidUploadID {
    1: string upload_id,
}


const i16 NO_SUITABLE_ENCODER = 7002
const string NO_SUITABLE_ENCODER_MSG = "No suitable encoder for {mimetype}"

exception NoSuitableEncoder {
    1: Mimetype mimetype
}


const i16 INVALID_BITRATE = 7003
const string INVALID_BITRATE_MSG = "Invalid {media} bitrate: {bitrate}"

exception InvalidBitrate {
    1: string media
    2: string bitrate
}


const i16 ASSET_NOT_FOUND = 7004
const string ASSET_NOT_FOUND_MSG = "Asset with ID '{asset_id}' not found"

exception AssetNotFound {
    1: string asset_id
}


const i16 TASK_NOT_FOUND = 7005
const string TASK_NOT_FOUND_MSG = "Task with ID '{task_id}' not found"

exception TaskNotFound {
    1: types.TaskID task_id
}


const i16 OPERATION_NOT_SUPPORTED = 7006
const string OPERATION_NOT_SUPPORTED_MSG = "Task '{task_id}' cannot be {action}"

exception OperationNotSupported {
    1: types.TaskID task_id
    2: string action
}


const i16 INVALID_FORMAT = 7007
const string INVALID_FORMAT_MSG = "Invalid format '{mimetype}' for asset {asset_id}"

exception InvalidFormat {
    1: types.AssetID asset_id
    2: Mimetype mimetype
}
