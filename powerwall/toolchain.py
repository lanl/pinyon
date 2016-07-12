"""Holds operations and classes useful for constructing model building tool chains"""

from extract import BaseExtractor
from mongoengine import Document
from mongoengine.fields import *

from powerwall.utility import WorkflowTool


class ToolChain(Document):
    """Stores all elements of an analysis tool chain"""

    name = StringField(required=True, regex='^[^\\s]+$', unique=True)
    """Name of the analysis toolchain.

    Cannot have any spaces
    """

    description = StringField(required=True)
    """Longer description of analysis toolchain.

    Can include HTML formatting"""

    extractor = ReferenceField(BaseExtractor, required=True)
    """Tool used to extact data from database"""

    def get_all_tools(self):
        """Get all `WorkflowTool` objects associated with this workflow"""

        return WorkflowTool.objects.filter(toolchain=self)
