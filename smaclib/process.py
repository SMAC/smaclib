"""
External process based tasks
----------------------------

The following classes offer the basic building blocks to construct advanced
deferred tasks based on external system processes.
"""


from __future__ import absolute_import

from smaclib import tasks

from twisted.internet import error
from twisted.internet import defer
from twisted.internet import protocol


class LineProcessProtocol(protocol.ProcessProtocol, object):
    
    def __init__(self, *args, **kwargs):
        super(LineProcessProtocol, self).__init__(*args, **kwargs)
        
        self.outBuffer = ""
        self.errBuffer = ""
    
    def outLineReceived(self, out):
        pass
    
    def errLineReceived(self, err):
        pass
    
    def outReceived(self, out):
        out = out.split("\n")
        
        self.outBuffer += out[0]
        
        if len(out) > 1:
            self.outLineReceived(self.outBuffer)
        
            for o in out[1:-1]:
                self.outLineReceived(o)
            
            self.outBuffer = out[-1]
    
    def errReceived(self, err):
        err = err.split("\n")
        
        self.errBuffer += err[0]
        
        if len(err) > 1:
            self.errLineReceived(self.errBuffer)
        
            for e in err[1:-1]:
                self.errLineReceived(e)
            
            self.errBuffer = err[-1]

class DeferredProcessProtocol(LineProcessProtocol):
    """
    Protocol to handle the execution a process and the bookkeeping of the Task
    instance tied to it.
    """
    
    def __init__(self, task_name='', delegate=None):
        super(DeferredProcessProtocol, self).__init__()
        
        self.delegate = delegate
        
        if delegate is not None:
            self.task = tasks.Task(task_name, self.delegate)
        else:
            self.task = defer.Deferred()
        
        self.cancelled = False

    def abort(self, task):
        self.cancelled = True
        self.transport.signalProcess('KILL')

    def processEnded(self, status):
        if self.cancelled:
            status.trap(error.ProcessTerminated)
        else:
            status.trap(error.ProcessDone)
            self.task.callback(self.delegate)


