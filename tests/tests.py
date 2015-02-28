import battalion
from version import Version

class TestClass(object):
    def test_version(self):
        assert battalion.__version__ == Version('battalion')