

namespace py smaclib.api


typedef string TaskID
typedef string UploadID
typedef string AssetID      /** An asset in the system, may have multiple versions */
typedef string VersionID    /** A version of a given asset, may be uniquely idenitified */
typedef string TalkID
typedef string URI
typedef string Mimetype
typedef string ModuleID


enum TaskStatus {
    RUNNING
    PAUSED
    COMPLETED
    FAILED
}

struct FileInfo {
    1: Mimetype mimetype,
    2: Sha1Checksum checksum
}

struct EncodingInfo {
    1: Mimetype format,
    2: string video_bitrate,
    3: string audio_bitrate
}

struct TaskInfo {
    1: TaskID task_id,
    2: string name,
    3: TaskStatus status,
    4: double completed,
}