"""Views for extractors"""
from pyramid.renderers import render_to_response
from pyramid.response import Response
from pyramid.view import view_config
import pyramid.httpexceptions as exc

from pinyon.toolchain import ToolChain
import networkx as nx
from matplotlib import pyplot as plt
import mpld3

import json


class ToolChainViews:

    def __init__(self, request):
        self.request = request

    def _get_toolchain(self):
        """Get the toolchain"""
        # Get the toolchain
        name = self.request.matchdict['name']
        toolchain = ToolChain.objects.get(name=name)
        return toolchain, name

    @view_config(route_name='toolchain_view', renderer='template/toolchain_view.jinja2')
    def view(self):
        """Just view the toolchain"""

        toolchain, name = self._get_toolchain()

        # Get stats about the toolchain network
        net_stats = toolchain.get_stats()

        return {
            'name': name,
            'toolchain': toolchain,
            'stats': net_stats
        }

    @view_config(route_name='toolchain_run')
    def run(self):
        """Reexport data"""

        # Get user request
        toolchain, name = self._get_toolchain()

        # Rerun extraction
        toolchain.extractor.get_data(ignore_cache=True, run_subsequent=True, save_results=True)
        toolchain.save()

        raise exc.HTTPFound(self.request.route_url('toolchain_view', name=name))

    @view_config(route_name='toolchain_network')
    def network(self):
        # Get user request
        toolchain, name = self._get_toolchain()

        # Get the hierarchy
        network = toolchain.get_tool_hierarchy()

        # Return raw data
        return Response(body=json.dumps(network, indent=2))


def includeme(config):
    config.add_route('toolchain_view', '/toolchain/{name}/view')
    config.add_route('toolchain_run', '/toolchain/{name}/run')
    config.add_route('toolchain_network', '/toolchain/{name}/network')
