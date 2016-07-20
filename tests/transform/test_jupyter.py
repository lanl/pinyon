from powerwall.extract import ExcelExtractor
from powerwall.toolchain import ToolChain
from powerwall.transform.jupyter import JupyterNotebookTransformer

from unittest import TestCase


class TestNotebook(TestCase):

    def test_operation(self):
        tc = ToolChain(name='TestChain', description='A sample toolchain', skip_register=True)
        tc.extractor = ExcelExtractor(path='./test-files/travel-times.xlsx', sheet='To', skip_register=True)

        # Make the settings file
        jt = JupyterNotebookTransformer.load_notebook('Test', 'Test notebook', './test-files/jupyter_example.ipynb')
        jt.calc_settings = {'multiple':1}
        jt.toolchain = tc

        # Test results
        output = jt.run(ignore_results=True)
        jt.write_notebook('test_notebook.ipynb')
        self.assertTrue('DayOfWeek' in output['data'].columns)
        mult1 = output['data']['DayOfWeek']

        # Change the multiple
        jt.calc_settings['multiple'] = 2
        output = jt.run(ignore_results=True)
        self.assertTrue(all(mult1 * 2 == output['data']['DayOfWeek']))
