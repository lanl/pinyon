"""Holds operations and classes useful for constructing model building tool chains"""

from extract import BaseExtractor
from mongoengine import Document
from mongoengine.fields import *

from pinyon import KnownClass
from pinyon.utility import WorkflowTool
import networkx as nx


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
    """Tool used to extract data from database"""

    def __init__(self, *args, **kwargs):
        super(ToolChain, self).__init__(*args, **kwargs)

        # Add to repo
        KnownClass.register_class(self)

    def get_all_tools(self):
        """Get all `WorkflowTool` objects associated with this workflow"""

        return WorkflowTool.objects.filter(toolchain=self)

    def get_tool_network(self):
        """Get a network representing current tools"""

        # Get tools
        tools = self.get_all_tools()

        # Make the network
        G = nx.DiGraph()

        #  Make the edges
        for tool in tools:
            if tool.previous_step is None:
                G.add_edge(self.extractor, tool)
            else:
                G.add_edge(tool.previous_step, tool)

        return G
