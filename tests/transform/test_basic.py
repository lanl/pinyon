import unittest

from pandas import DataFrame

from pinyon.tool.simple import FilterTransformer, RequiredFieldTransformer, ColumnAddTransformer, SimpleEvalTransformer


class TestFilter(unittest.TestCase):

    def test_filter(self):
        # Make a test dataset
        data = DataFrame([[1, 1], [0, 0]], columns=['a', 'b'])

        # Run the query
        trans = FilterTransformer(query='a < 0.5', skip_register=True)
        data, _ = trans._run(data, {})

        # Check result
        self.assertEquals(1, len(data))
        self.assertEquals([1], list(data.index))


class TestColumnAdd(unittest.TestCase):

    def test_transformer(self):
        # Make a test dataset
        data = DataFrame([[1, 1], [0, 0]], columns=['a', 'b'])

        # Add some columns
        trans = ColumnAddTransformer()
        trans.column_names = ['c','d']
        data, _ = trans._run(data, {})

        # Check result
        self.assertEquals(4, len(data.columns))
        self.assertEquals(2, len(data))


class TestRequiredField(unittest.TestCase):

    def test_required(self):
        # Make a test dataset
        data = DataFrame([[1, None], [0, 0]], columns=['a', 'b'])

        # Eliminate the row that
        trans = RequiredFieldTransformer(required_column='b')
        data, _ = trans._run(data, {})

        # Check result
        self.assertEquals(1, len(data))
        self.assertEquals([1], data.index)


class TestSimpleEval(unittest.TestCase):

    def test_simpleeval(self):
        # Make a test dataset
        data = DataFrame([[1, 1], [0, 0]], columns=['a', 'b'])

        # Eliminate the row that
        trans = SimpleEvalTransformer(eval_string='c = a + 1')
        data, _ = trans._run(data, {})

        # Check result
        self.assertEquals(2, len(data))
        self.assertTrue(all([2, 1] == data['c']))
