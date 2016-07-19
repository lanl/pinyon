from powerwall.extract import ExcelExtractor
from powerwall.toolchain import ToolChain
from powerwall.transform.jupyter import JupyterNotebookTransformer

from unittest import TestCase

class TestNotebook(TestCase):

    def test_operation(self):
        tc = ToolChain(name='TestChain', description='A sample toolchain', skip_register=True)
        tc.extractor = ExcelExtractor(path='./test-files/travel-times.xlsx', sheet='To', skip_register=True)

        jt = JupyterNotebookTransformer(notebook='./test-files/jupyter_example.ipynb', skip_register=True)
        jt.toolchain = tc

        output = jt.run(ignore_results=True)
        self.assertTrue('DayOfWeek' in output['data'].columns)
