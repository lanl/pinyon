"""Holds operations and classes useful for constructing model building tool chains"""
from collections import OrderedDict

from extract import BaseExtractor
from mongoengine import Document
from mongoengine.fields import *

from pinyon import KnownClass
from pinyon.tool import WorkflowTool
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
        if 'skip_register' in kwargs and not kwargs['skip_register']:
            KnownClass.register_class(self)

    def get_all_tools(self):
        """Get all `WorkflowTool` objects associated with this workflow"""

        return WorkflowTool.objects.filter(toolchain=self)

    def get_tool_network(self):
        """Get a network representing current tool"""

        # Get tool
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

    def get_tool_hierarchy(self):
        """Get a dictionary that expresses the hierarchical nature of the tools in the toolchain.

        Dictionary is in the format of data used in this d3.js example: http://bl.ocks.org/mbostock/4339184

        :return: dict, tool hierarchy"""

        # Define the recursive function used to do this
        def get_tree(node):
            # Capture the information about this note
            output = OrderedDict()
            output["name"] = node.name
            output["id"] = str(node.id)
            output["type"] = node.__class__.__name__
            output["class_hierarchy"] = node._cls
            output["children"] = [get_tree(x) for x in node.get_next_steps()]
            return output

        # Get the first node
        start = self.extractor

        return get_tree(start)

    def get_stats(self):
        """Get statistics about the toolchain

        Computes the depth of the workflow, and the number of terminal nodes

        :return: dict, where keys are:
            depth -> int, longest chain of tools
            width -> int, number of terminal nodes"""

        # Get the depth
        def depth_func(node):
            next_steps = node.get_next_steps()
            if len(next_steps) == 0:
                return 1
            else:
                return 1 + max([depth_func(x) for x in next_steps])
        depth = depth_func(self.extractor)

        # Get the number of terminal nodes
        def leaf_count(node):
            next_steps = node.get_next_steps()
            if len(next_steps) == 0:
                return 1
            else:
                return sum([leaf_count(x) for x in next_steps])
        width = leaf_count(self.extractor)

        return dict(depth=depth, width=width)
