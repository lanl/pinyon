"""Modules that manipulate a dataset"""

from mongoengine.fields import *

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


class JupyterNotebookTransformer(BaseTransformer):
    """Uses Jupyter notebook to perform a certain optimization step"""

    notebook = BinaryField(required=True)
