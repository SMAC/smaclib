from smaclib.twisted.plugins import module
from smaclib.conf import settings

class RecorderMaker(module.ModuleMaker):
    tapname = "smac-recorder"
    description = "Recorder module for SMAC."

    def loadSettings(self, configfile):
        from smaclib.modules.recorder import settings as recorder_settings
        settings.load(recorder_settings)
        
        super(RecorderMaker, self).loadSettings(configfile)
        
    def getModule(self):
        from smaclib.modules.recorder import module
        return module.Recorder()


serviceMaker = RecorderMaker()