

from twisted.application import internet
from twisted.cred import portal

from smaclib import ftp
from smaclib import modules
from smaclib.conf import settings
from smaclib.cred import checkers
from smaclib.twisted.plugins import module


class ArchiverMaker(module.ModuleMaker):
    tapname = "smac-archiver"
    description = "Archiver module for SMAC."

    def load_settings(self, configfile):
        from smaclib.modules.archiver import settings as archiver_settings
        settings.load(archiver_settings)
        
        super(ArchiverMaker, self).load_settings(configfile)

    def get_module(self):
        self.realm = ftp.TransfersRegister(settings.uploads_root,
                                           settings.completed_root)
        return modules.Archiver(self.realm)

    def make_service(self, options):
        module_service = super(ArchiverMaker, self).make_service(options)

        transfer_portal = portal.Portal(self.realm, [
            checkers.HomeDirectoryExistence(settings.uploads_root)
        ])
        
        ##
        
        from twisted.internet import ssl
        context = ssl.DefaultOpenSSLContextFactory(
            '/Users/garetjax/smac/temp/archiver/keys/server.key',
            '/Users/garetjax/smac/temp/archiver/keys/server.crt',
        )
        
        ##

        ftp_service = internet.SSLServer(settings.ftp_server_port,
                                         ftp.FTPFactory(transfer_portal),
                                         context,
                                         interface=settings.ftp_server_ip)
        ftp_service.setServiceParent(module_service)

        return module_service


serviceMaker = ArchiverMaker()
