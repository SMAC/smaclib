import txmongo

from twisted.application import internet
from twisted.internet import ssl
from twisted.cred import portal
from twisted.web import server, static

from smaclib import ftp
from smaclib.db import mongo
from smaclib.conf import settings
from smaclib.cred import checkers
from smaclib.twisted.plugins import module

from smaclib.services import converter



class ArchiverMaker(module.ModuleMaker):
    tapname = "smac-archiver"
    description = "Archiver module for SMAC."

    def loadSettings(self, configfile):
        from smaclib.modules.archiver import settings as archiver_settings
        settings.load(archiver_settings)
        
        super(ArchiverMaker, self).loadSettings(configfile)

    def getModule(self):
        from smaclib.modules.archiver import module
        
        self.ftp_realm = ftp.TransfersRegister(settings.downloads_root,
                                               settings.uploads_root,
                                               settings.completed_root)
        return module.Archiver(self.ftp_realm)

    def makeService(self, options):
        # MongoDB
        mongo.connection.set(txmongo.lazyMongoConnectionPool(
                                            **settings.mongodb['connection']))
        
        module_service = super(ArchiverMaker, self).makeService(options)

        transfer_portal = portal.Portal(self.ftp_realm, [
            checkers.HomeDirectoryExistence(settings.uploads_root,
                                            settings.downloads_root)
        ])
        
        ##
        #context = ssl.DefaultOpenSSLContextFactory(
        #    settings.server_key,
        #    settings.server_crt
        #)
        #
        #ftp_service = internet.SSLServer(settings.ftp_server_port,
        #                                 ftp.FTPFactory(transfer_portal),
        #                                 context,
        #                                 interface=settings.ftp_server_ip)
        ##
        
        conv_service = converter.ConversionService(settings.conv_server_port,
                                          interface=settings.conv_server_ip)
        conv_service.setServiceParent(module_service)
        
        ftp_service = internet.TCPServer(settings.ftp_server_port,
                                         ftp.FTPFactory(transfer_portal),
                                         interface=settings.ftp_server_ip)
        ftp_service.setServiceParent(module_service)

        return module_service


serviceMaker = ArchiverMaker()
