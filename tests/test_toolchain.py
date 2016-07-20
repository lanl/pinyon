from unittest import TestCase

from powerwall import connect_to_database
from powerwall.extract import ExcelExtractor
from powerwall.toolchain import ToolChain
from powerwall.transform import ColumnAddTransformer


class TestToolChain(TestCase):

    def setUp(self):
        connect_to_database(name='powerwall_test', host="")

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
