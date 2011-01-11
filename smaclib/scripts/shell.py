#!/usr/bin/env python


import sys
import argparse
import xmlrpclib
import IPython


def main():
    parser = argparse.ArgumentParser(description="Interactive shell for " \
                                     "interacting with a SMAC module.")
    parser.add_argument('module', help="The address of the RPC endpoint of " \
                        "the archiver to which the files shall be uploaded.")
    parser.add_argument('--version', action='version', version='%(prog)s 0.1')
    
    args = parser.parse_args()
    
    try:
        module = xmlrpclib.ServerProxy(args.module)
    except IOError:
        print "Invalid module address:", args.module
        return 1
    
    shell = IPython.Shell.IPShell(argv=[], user_ns={'module':module})
    shell.mainloop()

if __name__ == '__main__':
    sys.exit(main())