from unittest import TestCase

from pinyon import connect_to_database
from pinyon.extract import ExcelExtractor
from pinyon.toolchain import ToolChain
from pinyon.tool.simple import ColumnAddTransformer


class TestToolChain(TestCase):

    def setUp(self):
        connect_to_database(name='pinyon_test', host="")

    @staticmethod
    def make_class():
        tc = ToolChain(name='TestChain', description='A sample toolchain')
        tc.extractor = ExcelExtractor(name='TravelTimeLoader',
                                      description='Load travel times from Excel file',
                                      path='./test-files/travel-times.xlsx', sheet="To")
        return tc

    def test_instantiate(self):
        tc = self.make_class()

        self.assertEquals('TestChain', tc.name)
        self.assertEquals('A sample toolchain', tc.description)
        self.assertEquals(ExcelExtractor.__name__, tc.extractor.__class__.__name__)
