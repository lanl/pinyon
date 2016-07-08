"""Holds operations and classes useful for constructing model building tool chains"""

from extract import BaseExtractor
from mongoengine import Document
from mongoengine.fields import *


class ToolChain(Document):
    """Stores all elements of an analysis tool chain"""

    name = StringField(required=True, regex='^[^\\s]+$')
    """Name of the analysis toolchain.

    Cannot have any spaces
    """

    description = StringField(required=True)

    extractor = ReferenceField(BaseExtractor)
    """Tool used to extact data from database"""


