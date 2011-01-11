
import sys
import xmlrpclib


module = xmlrpclib.ServerProxy(sys.argv[1])
print module.request_upload_slot()