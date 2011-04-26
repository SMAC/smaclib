"""
Broker implementation to expose a module over XML RPC.
"""


import sys
import xmlrpclib

from smaclib import text
from smaclib.brokers import base

from twisted.python import log
from twisted.web import xmlrpc


class XmlRpcBroker(base.Broker, xmlrpc.XMLRPC):
    """
    A Broker specialization for XMLRPC based communication.
    
    Extends the xmlrpc.XMLRPC class to provide a smaclib compatible broking
    interface and patches the stdlib to handle structures through custom
    dictionary types for compatibility with thrift.
    
    Additionally wraps thrift errors in fault objects with a proper error code
    and error message.
    """

    def __init__(self, obj, router=None, allow_none=True):
        super(XmlRpcBroker, self).__init__(obj, router=router,
                                           allowNone=allow_none)

        self._patch_xmlrpclib()

    def _patch_xmlrpclib(self):
        """
        Patches the standard xmlrpclib Unmarshaller to wrap structures
        (normally returned as dictionaries) in AttributeDict instances.
        
        This allows the modules to access items as attributes, as which they
        where thrift types. We can thus support both protocols transparently.
        """
        
        class AttributeDict(dict):
            """
            A simple attribute dictionary. A dictionary which allows to set and
            retrieve items as attributes.
            """
            def __setattr__(self, name, value):
                self[name] = value

            def __getattr__(self, name):
                return self[name]

        def decode_struct(unmarsh, _):
            """
            Decodes a structure in order to wrap the resulting dictionary
            in an AttributeDict instance.
            """
            # pylint: disable=W0212
            mark = unmarsh._marks.pop()

            dct = AttributeDict()

            items = unmarsh._stack[mark:]
            for i in range(0, len(items), 2):
                dct[xmlrpclib._stringify(items[i])] = items[i+1]

            unmarsh._stack[mark:] = [dct]
            unmarsh._value = 0

        xmlrpclib.Unmarshaller.dispatch['struct'] = decode_struct

    def _get_function(self, function_path):
        """
        Intercepts the various XML RPC requests and resolves them to methods
        using the given filters.
        """

        try:
            func = self.router(self.obj, function_path)
        except AttributeError:
            raise xmlrpc.NoSuchFunction(self.NOT_FOUND,
                    "function {0} not found".format(function_path))
        else:
            if not callable(func):
                raise xmlrpc.NoSuchFunction(self.NOT_FOUND,
                        "function {0} not callable".format(function_path))
            else:
                return func
    _getFunction = _get_function

    def _errordetails(self, exception_class, default=xmlrpc.XMLRPC.FAILURE):
        """
        Returns an error code for a given exception by looking it up in the
        sibling module called 'constants' using the uppercased class name as
        identifier.

        Example: the exception::

            smac.api.errors.UnknownMimetype

        causes the following lookup::

            smac.api.constants.UNKNOWN_MIMETYPE         # Error code
            smac.api.constants.UNKNOWN_MIMETYPE_MSG     # Error message

        A value of default is retuned in no definition is found.
        """
        const_name = text.camelcase_to_uppercase(exception_class.__name__)
        module_name = exception_class.__module__.replace('ttypes', 'constants')

        __import__(module_name)

        errno = getattr(sys.modules[module_name], const_name, default)
        errmsg = getattr(sys.modules[module_name], const_name + '_MSG', "")

        return errno, errmsg

    def _ebRender(self, failure):
        """
        Intercepts any exception in the smac.api namespace (i.e. defined by
        thrift) and converts it into a xmlrpc.Fault instance.
        """
        exception = failure.value

        if isinstance(exception, xmlrpc.Fault):
            return exception
        elif exception.__class__.__module__.startswith('smaclib.api'):
            errno, errmsg = self._errordetails(exception.__class__)
            return xmlrpc.Fault(errno, errmsg.format(**exception.__dict__))

        log.err(failure)
        return xmlrpc.Fault(self.FAILURE, "error")

