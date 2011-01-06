import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'gen-py.twisted'))
from service import Calculator

from zope.interface import implements


class MyModule(object):
    
    implements(Calculator.Iface)
    
    name = 'Ciao'
    
    def add(self, a, b):
        return a + b
    
    def myself(self):
        self.name = 'ciaos'
        return self


# It is possible to personalize the encoding
#import xmlrpclib
#
#def encode(_, value, write):
#    write('<value><int>1000</int></value>\n')
#
#xmlrpclib.Marshaller.dispatch[MyModule] = encode