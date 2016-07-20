"""Modules that manipulate a dataset"""
import numpy as np
from mongoengine.fields import *
from pandas.core.series import Series


from powerwall.utility import WorkflowTool

__author__ = 'Logan Ward'


class BaseTransformer(WorkflowTool):
    """Operation that modifies a dataset"""
    pass


class FilterTransformer(BaseTransformer):
    """Get only entries that pass a certain query

    Uses the query syntax described in:
        http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.query.html
    """

    query = StringField(required=True)
    """Query used to define filter"""

    def _run(self, data, inputs):
        return data.query(self.query), dict(inputs)


class ColumnAddTransformer(WorkflowTool):
    """Add new columns to the dataset"""

    column_names = ListField(StringField(), required=True)

    def _run(self, data, other_inputs):
        for col in self.column_names:
            if col in data.columns:
                raise Exception('Column already in dataset')
            data[col] = Series()
        return data, other_inputs