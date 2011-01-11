"""
Various settings loaders provided by default by the smac architecture.

You can add your own loaders and register them with the Settings provider to
be able to load settings from other sources.
"""


import os
import sys

from smaclib.conf.decorators import regex_matcher
from smaclib.conf.decorators import type_loader


@type_loader('module')
def module_loader(provider, module):
    # Update the dict by filtering out private members
    for key, value in module.__dict__.iteritems():
        if not key.startswith('_'):
            provider[key] = value


@regex_matcher(r'\.pyc?$')
def python_loader(provider, filename):
    """
    Loads the settings from a python module based on its file name.
    """
    dirname, basename = os.path.split(filename)
    module = basename.rsplit('.', 1)[0]

    # Add containing directory to the path for import
    sys.path.insert(0, dirname)
    
    try:
        # Import the settings module
        __import__(module, level=0)
    except ImportError:
        raise
    else:
        # If it was loaded successfully retrieve it by looking it up in the
        # loaded modules
        module_loader(provider, sys.modules[module])
    finally:
        # And finally remove the previously added dirname from the path
        sys.path.remove(dirname)


# pylint: disable=W0613

@regex_matcher(r'\.ini$')
def ini_loader(provider, filename):
    raise NotImplementedError("The ini file loader is not yet implemented, " \
                              "use another settings format.")


@regex_matcher(r'\.xml$')
def xml_loader(provider, filename):
    raise NotImplementedError("The xml file loader is not yet implemented, " \
                              "use another settings format.")


@regex_matcher(r'^redis://')
def redis_loader(provider, address):
    raise NotImplementedError("The redis db loader is not yet implemented, " \
                              "use another settings format.")


@regex_matcher(r'\.json$')
def json_loader(provider, filename):
    raise NotImplementedError("The json file loader is not yet implemented," \
                              " use another settings format.")


