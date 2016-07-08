"""Views for extractors"""
from pyramid.view import view_config
import pyramid.httpexceptions as exc

from powerwall.toolchain import ToolChain


class ToolChainViews:

    def __init__(self, request):
        self.request = request

    def _get_toolchain(self):
        """Get the toolchain"""
        # Get the toolchain
        name = self.request.matchdict['name']
        toolchain = ToolChain.objects.get(name=name)
        return toolchain, name

    @view_config(route_name='toolchain_view', renderer = 'template/toolchain_view.jinja2')
    def view(self):
        """Just view the toolchain"""

        toolchain, name = self._get_toolchain()

        return {
            'name': name,
            'toolchain': toolchain
        }

    @view_config(route_name='toolchain_run')
    def run(self):
        """Reexport data"""

        # Get user request
        toolchain, name = self._get_toolchain()

        # Rerun extraction
        toolchain.extractor.get_data(ignore_cache=True)
        toolchain.save()

        raise exc.HTTPFound(self.request.route_url('toolchain_view', name=name))


def includeme(config):
    config.add_route('toolchain_view', '/toolchain/{name}/view')
    config.add_route('toolchain_run', '/toolchain/{name}/run')
