#!/usr/bin/env python


import sys
import argparse
import xmlrpclib
import IPython
import imp


def main():
    parser = argparse.ArgumentParser(description="Interactive shell for " \
                                     "interacting with a SMAC module.")
    parser.add_argument('module', help="The address of the RPC endpoint of " \
                        "the archiver to which the files shall be uploaded.")
    parser.add_argument('--version', action='version', version='%(prog)s 0.1')
    
    args = parser.parse_args()
    
    if args.module.startswith('http'):
        try:
            module = xmlrpclib.ServerProxy(args.module)
        except IOError:
            print "Invalid module address:", args.module
            return 1
    elif args.module.startswith('thrift'):
        import urlparse
        from thrift.transport import TSocket, TTransport
        from thrift.protocol import TBinaryProtocol
        
        url = urlparse.urlparse(args.module.replace('thrift://', 'http://'))
        
        transport = TSocket.TSocket(url.hostname, url.port)
        # Buffering is critical. Raw sockets are very slow
        #transport = TTransport.TBufferedTransport(transport)
        transport = TTransport.TFramedTransport(transport)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        
        base = "/Users/garetjax/Versioning/git/smac/api/build/python"
        mod = urlparse.parse_qs(url.query)['iface'][0]
        mod = 'smaclib.api.{1}.{2}'.format(base, mod, mod.capitalize())
        sys.path.insert(0, base)
        __import__(mod)
        module = sys.modules[mod]
        sys.path.pop(0)
        module = module.Client(protocol)
        
        transport.open()
        
    else:
        raise ValueError("Unknown protocol")
    
    shell = IPython.Shell.IPShell(argv=[], user_ns={'module':module})
    shell.mainloop()

if __name__ == '__main__':
    sys.exit(main())