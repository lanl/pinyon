from unittest import TestCase

from powerwall.extract import ExcelExtractor
from powerwall.toolchain import ToolChain


class TestToolChain(TestCase):

    @staticmethod
    def make_class():
        tc = ToolChain(name='TestChain', description='A sample toolchain')
        tc.extractor = ExcelExtractor(path='./test-files/travel-times.xlsx')
        return tc

    def test_instantiate(self):
        tc = self.make_class()

        self.assertEquals('TestChain', tc.name)
        self.assertEquals('A sample toolchain', tc.description)
        self.assertEquals(ExcelExtractor.__name__, tc.extractor.__class__.__name__)