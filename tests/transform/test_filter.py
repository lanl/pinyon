import unittest
from pandas import DataFrame
from powerwall.transform import FilterTransformer

class TestFilter(unittest.TestCase):

    def test_filter(self):
        # Make a test dataset
        data = DataFrame([[1, 1], [0, 0]], columns=['a', 'b'])

        # Run the query
        trans = FilterTransformer(query='a < 0.5')
        trans.apply_transform(data)

        # Check result
        self.assertEquals(1, len(data))
        self.assertEquals([1], list(data.index))
