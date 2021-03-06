"""
Project management commands based upong the fabric python tool.
"""


import os
import tempfile

from fabric.operations import local
from fabric.context_managers import show, cd


def _get_files():
    import smaclib
    ignored = set(('api', '.DS_Store'))
    files = os.listdir(os.path.dirname(smaclib.__file__))
    files = (f for f in files if not f.endswith(".pyc"))
    files = (f for f in files if f not in ignored)
    files = (f.replace('.py', '') for f in files)
    files = ("smaclib." + f for f in files)
    files = ' '.join(files)
    
    return files


def sslcert(name):
    with show('everything'):
        local("openssl genrsa -des3 -out {0}.key.crypt 1024".format(name), capture=False)
        local("openssl rsa -in {0}.key.crypt -out {0}.key".format(name), capture=False)
        local("openssl req -new -key {0}.key -out {0}.csr".format(name), capture=False)
        local("openssl x509 -req -days 365 -in {0}.csr -signkey {0}.key -out {0}.crt".format(name), capture=False)


def pyrate():
    with show('everything'):
        local("python conf/pyrate.py", capture=False)


def pylint(modules=None, html=False):
    """
    Does a syntax and code-style check on the python code of this project
    using pylint.
    """
    modules = modules or _get_files()
    
    if html:
        format = 'html >temp/pylint.html'
    else:
        format = 'text'
    
    with show('everything'):
        local("pylint --rcfile=conf/pylint.ini {} --output-format={}".format(
              modules, format), capture=False)
        if html:
            local('open temp/pylint.html')


def pycheck():
    with show('everything'):
        local("pychecker --config=conf/pychecker.ini {}".format(_get_files()),
              capture=False)


def test(module='smaclib', coverage_report=False, open_report=False):
    """
    Runs the trial test suite on the whole smaclib package.
    Also generates the HTML code coverage report.
    """
    trial = "$(which trial) --temp-directory=temp/trial " + module
    coverage = "coverage run --rcfile=conf/coverage.ini"
    
    with show('everything'):
        if coverage_report:
            local(coverage + " " + trial, capture=False)
            local("coverage html --rcfile=conf/coverage.ini", capture=False)
            if open_report:
                local('open temp/coverage-report/index.html')
        else:
            local(trial, capture=False)


def pyflakes():
    """
    Does a syntax and code-style check on the python code of this project
    using pyflakes.
    """
    with show('everything'):
        local("pyflakes . | grep -v smaclib/api | grep -v example/gen-py", capture=False)


def thrift():
    """
    Compiles the thrift IDL files and places them at the right pace inside the
    library.
    """
    base = os.path.dirname(__file__)
    destination = os.path.join(base, 'smaclib/api')
    api = os.path.join(base, 'conf/api')
    build = os.path.join(api, 'build/twisted/smaclib/api')
    
    with cd(api):
        local('make twisted', capture=False)
        
    with show('everything'):
        # Empty destination directory
        local('rm -rf {}/*'.format(destination))
        
        # Move generated files in place
        local('mv {}/* {}'.format(build, destination))
        
    with cd(api):
        # Cleanup
        local('make clean')
    