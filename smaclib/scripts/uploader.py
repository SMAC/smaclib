#!/usr/bin/env python


import sys
import xmlrpclib
import ftplib
import argparse
import urlparse


def upload(module, files):
    uploads = {}
    
    for f in files:
        print "Requesting upload slot for", f.name
        
        try:
            slot = module.request_upload_slot()
        except xmlrpclib.ProtocolError as e:
            print "Could not allocate an upload slot:", e.errcode, e.errmsg
        else:
            slot = urlparse.urlparse(slot)
            client = ftplib.FTP()
            client.connect(slot.hostname, slot.port)
            client.login(slot.username, slot.password)
            print "Uploading...",
            sys.stdout.flush()
            client.storbinary("STOR my_upload", f)
            client.quit()
            uploads[slot.username] = f.name
            print "OK"
            ##
            print "Archiving"
            print module.archive_upload("mytalkid", slot.username, {'mimetype': 'video/quicktime'})
            
    
    return uploads


def report(uploads):
    for id, file in uploads.iteritems():
        print "{}    {}".format(id, file)


def main():
    parser = argparse.ArgumentParser(description="Upload a bunch of files " \
                                     "to a SMAC archiver.")
    parser.add_argument('module', help="The address of the RPC endpoint of " \
                        "the archiver to which the files shall be uploaded.")
    parser.add_argument('files', metavar='FILE', type=argparse.FileType('rb'),
                        nargs='+', help="A list of files to upload.")
    parser.add_argument('--version', action='version', version='%(prog)s 0.1')
    
    args = parser.parse_args()
    
    try:
        module = xmlrpclib.ServerProxy(args.module)
    except IOError:
        print "Invalid module address:", args.module
        return 1
    
    uploads = upload(module, args.files)
    
    print
    print "Uploads completed; you can process your files with the following ids:"
    print
    print "ID                                      File"
    print "------------------------------------    ------------------------"
    
    report(uploads)
    
    print


if __name__ == '__main__':
    sys.exit(main())