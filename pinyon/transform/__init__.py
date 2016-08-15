"""Modules that manipulate a dataset"""
import numpy as np
from mongoengine.fields import *
from pandas.core.series import Series


from pinyon.utility import WorkflowTool
from wtforms import fields as wtfields

__author__ = 'Logan Ward'


class BaseTransformer(WorkflowTool):
    """Operation that modifies a dataset"""
    pass


class FilterTransformer(BaseTransformer):
    """Get only entries that pass a certain query

    Uses the query syntax described in:
        http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.query.html
    """

    query = StringField(required=True, default="")
    """Query used to define filter"""

    def _run(self, data, inputs):
        return data.query(self.query), dict(inputs)

    def get_form(self):
        super_form = super(FilterTransformer, self).get_form()

        class MyForm(super_form):
            query = wtfields.StringField('Query String', default=self.query,
                                         description='Query string passed to Pandas')

        return MyForm

    def process_form(self, form, request):
        super(FilterTransformer, self).process_form(form, request)

        self.query = form.query.data


class RequiredFieldTransformer(BaseTransformer):
    """Eliminate any rows that have a NaN value for a certain quantity"""

    required_column = StringField(required=True, default="DefaultColumn")

    def _run(self, data, other_inputs):
        return data[~ data[self.required_column].isnull()], other_inputs

    def get_form(self):
        super_form = super(RequiredFieldTransformer, self).get_form()

        class MyForm(super_form):
            required_column = wtfields.StringField('Required Column', default=self.required_column,
                                                   description='Column that must have a value')

        return MyForm

    def process_form(self, form, request):
        super(RequiredFieldTransformer, self).process_form(form, request)

        self.required_column = form.required_column.data


class ColumnAddTransformer(BaseTransformer):
    """Add new columns to the dataset"""

    column_names = ListField(StringField(), required=True, default=['DefaultColumn'])

    def _run(self, data, other_inputs):
        for col in self.column_names:
            if col in data.columns:
                raise Exception('Column already in dataset')
            data[col] = Series()
        return data, other_inputs

    def get_form(self):
        super_form = super(ColumnAddTransformer, self).get_form()

        class MyForm(super_form):
            column_names = wtfields.StringField('Columns',
                                                default=", ".join(self.column_names),
                                                description='Names of columns to be added, separated by commas')

        return MyForm

    def process_form(self, form, request):
        super(ColumnAddTransformer, self).process_form(form, request)

        self.column_names = [x.strip() for x in form.column_names.data.split(",")]


class SimpleEvalTransformer(BaseTransformer):
    """Run a transformation on the dataset using Panda's eval capability

    Documentation for eval can be found at:
        http://pandas.pydata.org/pandas-docs/stable/generated/pandas.eval.html
    """

    eval_string = StringField(required=True, default="")

    def _run(self, data, other_inputs):
        return data.eval(self.eval_string, inplace=False), other_inputs

    def get_form(self):
        super_form = super(SimpleEvalTransformer, self).get_form()

        class MyForm(super_form):
            eval_string = wtfields.StringField('Function', default=self.eval_string,
                                               description='String to be evaluated by Pandas DataFrame.eval function')

        return MyForm

    def process_form(self, form, request):
        super(SimpleEvalTransformer, self).process_form(form, request)

        self.eval_string = form.eval_string.data
