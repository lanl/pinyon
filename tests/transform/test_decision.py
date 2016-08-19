from bs4 import BeautifulSoup
from unittest import TestCase

from pinyon.extract import ExcelExtractor
from pinyon.toolchain import ToolChain
from pinyon.tool.decision import HTMLDecisionTracker


class DecisionTest(TestCase):

    def test(self):
        # Make a toolchain
        tc = ToolChain(name='TestChain', description='A sample toolchain', skip_register=True)
        tc.extractor = ExcelExtractor(path='./test-files/travel-times.xlsx', sheet='To')

        # Add in a decision tracker
        wt = HTMLDecisionTracker.load_template('TestTool', 'Test for this test', None, skip_register=True)
        wt.toolchain = tc
        inputs = wt.get_inputs()
        self.assertEquals(['data'], inputs.keys()) # Make sure it fires up

        # Make sure it renders a table without error, and with 0 as the index of the first row in the body
        tool = wt.get_html_tool()
        soup = BeautifulSoup(tool, 'lxml')
        table = soup.find('table', id='pinyondata')
        row_1 = table.find('tbody').find('tr')
        self.assertEquals("0", row_1['entry_key'])

        # Make the entry key the data
        wt.entry_key = 'Date'
        tool = wt.get_html_tool()
        soup = BeautifulSoup(tool, 'lxml')
        table = soup.find('table', id='pinyondata')
        row_1 = table.find('tbody').find('tr')
        self.assertEquals("2016-06-16 00:00:00", row_1['entry_key'])

        # Simulate a decision
        to_change = row_1.find_all('td')[2]
        to_change['original-value'] = to_change.string
        to_change['decision-notes'] = "Because I felt like it."
        to_change.string = 'Flew'
        to_change['class'] = ['editedCell']

        wt.process_results(soup.prettify())

        self.assertTrue(1, len(wt._decisions_cache))
        self.assertEquals(('2016-06-16 00:00:00', 'Route'), wt._decisions_cache.keys()[0])
        self.assertEquals(('30-4', 'Flew', 'Because I felt like it.'), wt._decisions_cache.values()[0])

        # Apply it to the dataset
        data = wt.get_inputs()['data']
        self.assertEquals('30-4', data['Route'][0])

        outputs = wt.run()

        self.assertEquals('Flew', outputs['data']['Route'][0])

        # Make sure the new table includes the current decision list
        tool = wt.get_html_tool()
        soup = BeautifulSoup(tool, 'lxml')
        changed_table = soup.find('table', id='pinyondata')

        previous_results = wt._decisions_cache
        wt.process_results(changed_table.prettify())
        self.assertEquals(previous_results, wt._decisions_cache)


