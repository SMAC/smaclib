

from twisted.internet.utils import _BackRelay as _TxBackRelay
from twisted.internet.utils import _callProtocolWithDeferred


class _BackRelay(_TxBackRelay, object):
    """
    Overrides the original twisted _BackRelay class to allow for one option
    more in the errortoo parameter.
    
    A value of False, instead of triggering the errback, will silently ignore
    any stderr value, while the normal behavior of raising the exception is
    respected when errortoo is None.
    """
    
    def __init__(self, deferred, errortoo):
        super(_BackRelay, self).__init__(deferred)
        if errortoo:
            self.errReceived = self.errReceivedIsGood
        elif errortoo is None:
            self.errReceived = self.errReceivedIsBad
        else:
            self.errReceived = lambda text: None


def get_process_output(executable, args=(), env=None, path=None, reactor=None,
                 errortoo=None):
    """
    Spawn a process and return its output as a deferred returning a string.

    @param executable: The file name to run and get the output of - the
                       full path should be used.

    @param args: the command line arguments to pass to the process; a
                 sequence of strings. The first string should *NOT* be the
                 executable's name.

    @param env: the environment variables to pass to the processs; a
                dictionary of strings.

    @param path: the path to run the subprocess in - defaults to the
                 current directory.

    @param reactor: the reactor to use - defaults to the default reactor

    @param errortoo: If true, include stderr in the result.  If false, discard
        it. If None and stderr is received the returned L{Deferred} will
        errback with an L{IOError} instance with a C{processEnded} attribute.
        The C{processEnded} attribute refers to a L{Deferred} which fires when
        the executed process ends.
    """
    return _callProtocolWithDeferred(lambda d:
                                        _BackRelay(d, errortoo=errortoo),
                                     executable, args, env or {}, path,
                                     reactor)