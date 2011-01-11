
from smaclib import modules
from smaclib.twisted.plugins import module


class AnalyzerMaker(module.ModuleMaker):
    tapname = "smac-analyser"
    description = "Analyzer module for SMAC."
    
    def getModule(self):
        return modules.base.Module()


serviceMaker = AnalyzerMaker()