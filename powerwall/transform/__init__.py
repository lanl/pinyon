"""Modules that manipulate a dataset"""

from mongoengine import Document
from mongoengine.fields import *

__author__ = 'Logan Ward'


class BaseTransformer(Document):
    """Base module for all operations that modify a dataset

    These can be used for a multitude of purposes including filtering unwanted entries, transforming a variable to a
    more useful form, etc. All methods must have two pieces of information: a name and a description that captures the
    rationale for these states"""

    meta={'allow_inheritance': True}

    name=StringField(required=True, regex="^[^\\s+]*$")
    """Name of this transformer.

    Cannot have any whitespace"""

    description=StringField(required=True)
    """Description of this transformer"""

    def apply_transform(self,data):
        """Apply transformation on input dataset

        Input / Output:
            :param data: DataFrame, dataset to be transformed
        """
        raise NotImplementedError

class FilterTransformer(BaseTransformer):
    """Get only entries that pass a certain query

    Uses the query syntax described in:
        http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.query.html
    """

    query=StringField(required=True)
    """Query used to define filter"""

    def apply_transform(self,data):
        data.query(self.query, inplace=True)
