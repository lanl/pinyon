from unittest import TestCase
import os

import pickle

from pinyon.extract import ExcelExtractor


class TestBase(TestCase):

    def test_extract(self):
        """Make sure that the extract loads data into the right fields"""

        ex = ExcelExtractor(path=os.path.join('test-files', 'travel-times.xlsx'), sheet='To')

        # Check that read data puts data in cache
        data = ex.get_data()
        self.assertIsNotNone(ex._data_cache)
        self.assertIsNone(ex.result)

        # Run again, make sure time wasn't updated
        first_pull = ex.last_exported
        self.assertEquals(first_pull, ex.last_exported)

        # Call with ignore cache, make sure it updates
        ex.get_data(ignore_cache=True)
        self.assertNotEquals(first_pull, ex.last_exported)

        # Simulate a save: Store the pickle in the result and delete the cache
        ex.result = pickle.dumps(data)
        ex._data_cache = None
        self.assertEquals(data.to_csv(), ex.get_data().to_csv())
        self.assertIsNotNone(ex._data_cache)
