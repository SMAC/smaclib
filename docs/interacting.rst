Interacting with a SMAC module
==============================

XMLRPC
------

To access a SMAC module using the XMLRPC protocol, proceed as follows::

   import xmlrpclib
   
   
   HOSTNAME = 'localhost'
   PORT = 7081
   
   
   # Define the URL to connect to the remote module (use 'https' if necessary)
   url = 'http://{0}:{1:d}/RPC2'.format(HOSTNAME, PORT)
   
   # Create a new remote module instance
   module = xmlrpclib.ServerProxy(url)
   
   # Now you can work on the module as if it were a local object
   print module.getID()


SOAP
----

Thrift over HTTP
----------------

Thrift over AMQP
----------------

Thrift RPC
----------

To access a SMAC module using the thrift RPC protocol, proceed as follows::

   from thrift.transport import TSocket
   from thrift.transport import TTransport
   from thrift.protocol import TBinaryProtocol

   # Import the right module
   # NOTE: Be sure to chose the version generated with 'make python' or
   #       'thrift --gen py:new_style' and not the one generated using 
   #       'make twisted'.
   from smaclib.api.archiver import Archiver as module_class


   HOSTNAME = 'localhost'
   PORT = 7081


   # Define the socket to use
   transport = TSocket.TSocket(HOSTNAME, PORT)

   # Wrap the socket connection in a framed transport
   transport = TTransport.TFramedTransport(transport)

   # Define the protocol used to encode the requests
   protocol = TBinaryProtocol.TBinaryProtocol(transport)

   # Create the module instance
   module = module_class.Client(protocol)
   
   # Open the communication
   transport.open()

   # Now you can work on the module as if it were a local object
   print module.getID()


