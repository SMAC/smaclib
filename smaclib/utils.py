from __future__ import absolute_import

import os
import contextlib

from twisted.internet import reactor
from twisted.internet import defer


def sleep(time):
    d = defer.Deferred()
    reactor.callLater(time, d.callback, None)
    return d


class _FileRedirect(object):
    """
    A simple context manager to redirect output written to given file object
    to another one or to discard the data entirely.

    It works at OS level to allow to redirect/discard output from libraries
    written in C too. This means that only file-like objects working on real
    file descriptors are supported (sys.stdout, sys.stderr or any file opened
    using the ``open`` or ``os.fdopen`` functions).
    """

    def __init__(self, source=None, destination=None):
        """
        Omitting the ``destination`` argument causes the output to be
        discarded.
        """

        try:
            self.fd = source.fileno()
        except AttributeError:
            try:
                self.fd = int(source)
            except ValueError:
                raise ValueError("The source argument must either be a " \
                                 "file-like object or a file-descriptor.")
            else:
                self.src = None
        else:
            self.src = source

        self.dst = destination
        self.old = None

    def __enter__(self):
        if self.src is not None:
            self.src.flush()

        if self.dst is None:
            self.dst = open(os.devnull, 'w')

        if self.fd >= 0:
            self.old = os.dup(self.fd)
            os.dup2(self.dst.fileno(), self.fd)
        elif self.src is not None:
            self.old, self.src.write = self.src.write, self.dst.write

    def __exit__(self, *args):
        if self.fd >= 0:
            if self.src is not None:
                self.src.flush()

            if self.dst is not None:
                self.dst.flush()

            os.dup2(self.old, self.fd)
            os.close(self.old)

            # TODO: Hummm... does dup open file with the default buffering mode?
            #try:
            #    stream = ('stdout', 'stderr')[self.fd - 1]
            #except IndexError:
            #    pass
            #else:
            #    setattr(sys, stream, os.fdopen(self.fd, 'w'))
        elif self.src is not None:
            self.src.write = self.old


def discard(*handlers):
    """
    Functional wrapper around the ``_FileRedirect`` context manager to discard
    data printed to the given file object.
    """
    return contextlib.nested(*[_FileRedirect(src) for src in handlers])


def redirect(from_fh, to_fh):
    """
    Functional wrapper around the ``_FileRedirect`` context manager to redirect
    data written to a file to another one.
    """
    return _FileRedirect(from_fh, to_fh)
