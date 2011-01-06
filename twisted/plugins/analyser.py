
from smaclib.twisted.plugins import module
from smaclib import modules


class AnalyzerMaker(module.ModuleMaker):
    tapname = "smac-analyse"
    description = "Analyzer module for the SMAC system"
    
    def getModule(self):
        return modules.base.Module()


serviceMaker = AnalyzerMaker()