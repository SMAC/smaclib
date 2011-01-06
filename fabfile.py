"""
Project management commands based upong the fabric python tool.
"""


import tempfile

from fabric.operations import local
from fabric.context_managers import show


def pylint():
    """
    Does a syntax and code-style check on the python code of this project
    using pylint.
    """
    with show('everything'):
        local("pylint smaclib", capture=False)


def pyflakes():
    """
    Does a syntax and code-style check on the python code of this project
    using pyflakes.
    """
    with show('everything'):
        local("pyflakes .", capture=False)


def thrift():
    """
    Compiles the thrift IDL files and places them at the right pace inside the
    library.
    """
    # Create temporary directory to hold build results
    tempdir = tempfile.mkdtemp(suffix='-thrift')
    
    # Compilation configuration
    flags = ' '.join(['-strict', '-recurse'])
    source = 'conf/api/all.thrift'
    destination = 'smaclib/api'
    command = "thrift --gen py:twisted {} -o {} {}".format(
        flags,
        tempdir,
        source
    )
    
    with show('everything'):
        # Compile
        local(command, capture=False)
        
        # Empty destination directory
        local('rm -rf {}/*'.format(destination))
        
        # Move generated files in place
        local('mv {}/*/smaclib/api/* {}'.format(tempdir, destination))
        
        # Cleanup
        local('rm -rf {}'.format(tempdir))

