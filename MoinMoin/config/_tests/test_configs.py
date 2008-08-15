from MoinMoin.config.multiconfig import DefaultConfig

class NoUnderlay(DefaultConfig):
    data_underlay_dir = None

_tests = [NoUnderlay, ]

class TestConfigs:
    def testConfigs(self):
        for cls in _tests:
            cls.data_dir = self.request.cfg.data_dir
            cls.secrets = self.request.cfg.secrets
            # quite a bad hack to make _importPlugin succeed
            cls('MoinMoin')
