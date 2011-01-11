"""
Default configuration for all archiver modules.
This configuration can be overridden in user defined settings files.
"""


from twisted.python import filepath


# pylint: disable=C0103,W0105
# Yes... it is a configuration file, and I want my values to be lowercase as
# they are eventually read as instance properties.
# And as epydoc recognizes docstrings for variables too, I provide them too 
# here.


data_root = filepath.FilePath('contributions')
"""
Base directory to hold all archived data once processed.
"""

uploads_root = filepath.FilePath('transfers')
"""
Base directory for all on-going uploads. Will contain a folder for each
upload slot.
"""

completed_root = filepath.FilePath('completed')
"""
Base directoriy to which completed uploads will be moved, waiting to be
archived.

This directory should be on the same partition as the uploads_root, in order
to speed up the move operations.
"""

ftp_server_ip = '127.0.0.1'
"""
IP on which the FTP server for the uploads shall listen on. This value is also
sent back to the clients as the host when requesting the allocation of an 
upload slot.
"""

ftp_server_port = 10000
"""
Port on which the FTP server shall listen.
"""

video_bitrates = {
    'default':  '128k',
    'speaker':  '150k',
    'slide':    '64k',
    'overview': '150k',
}
"""
Video bitrate presets
"""

audio_bitrates = {
    'default':  '164k',
}
"""
Audio bitrate presets
"""

audio_sampling_rate = '22050'

