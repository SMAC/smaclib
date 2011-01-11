"""
Default configuration for the whole smac architecture.
This configuration can be overridden in module settings files and in user
defined settings files.
"""


import os


# pylint: disable=C0103,W0105
# Yes... it is a configuration file, and I want my values to be lowercase as
# they are eventually read as instance properties.


mime_files = [
    os.path.join(os.path.dirname(__file__), 'mime.types')
]


mongodb = {
    'connection': {
        'host': "127.0.0.1",
        'port': 27017,
        'reconnect': True,
        'pool_size': 5,
    },
    'database': 'smac',
}

rest = {
    'port': 7080,
    'ssl': False,
    'private_key': None,
    'certificate': None,
    'expose': {
        'rpc': 'RPC2',
        'soap': 'SOAP',
    }
}

thrift_port = 7081

module_id = None