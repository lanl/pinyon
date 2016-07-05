"""Holds operations and classes useful for constructing model building tool chains"""

from extract import BaseExtractor
from mongoengine import Document
from mongoengine.fields import *


class ToolChain(Document):
    """Stores all elements of an analysis tool chain"""

    extractors = ListField(ReferenceField(BaseExtractor))
    """Tools used to extact data from different databases"""