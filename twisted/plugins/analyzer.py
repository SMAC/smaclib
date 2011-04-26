from smaclib.twisted.plugins import module


class AnalyzerMaker(module.ModuleMaker):
    tapname = "smac-analyzer"
    description = "Analyzer module for SMAC."

    def getModule(self):
        from smaclib.modules.analyzer import module
        return module.Analyzer()


serviceMaker = AnalyzerMaker()