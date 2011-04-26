from smaclib.twisted.plugins import module
from twisted.application import internet
from smaclib.conf import settings
from twisted.web import server
from twisted.web import static


class PublisherMaker(module.ModuleMaker):
    tapname = "smac-publisher"
    description = "Publisher module for SMAC."

    def loadSettings(self, configfile):
        from smaclib.modules.publisher import settings as publisher_settings
        settings.load(publisher_settings)

        super(PublisherMaker, self).loadSettings(configfile)

    def getModule(self):
        from smaclib.modules.publisher import module
        return module.Publisher()

    def makeService(self, options):
        module_service = super(PublisherMaker, self).makeService(options)

        # Web service
        resource = static.File(settings.data_root.path)
        factory = server.Site(resource)
        web_service = internet.TCPServer(settings.http_port, factory)
        web_service.setServiceParent(module_service)

        return module_service


serviceMaker = PublisherMaker()