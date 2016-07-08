"""Views for extractors"""
from pyramid import url
from pyramid.view import view_config
import pyramid.httpexceptions as exc

from powerwall.extract import BaseExtractor


class ExtractorViews:

    def __init__(self, request):
        self.request = request

    def _get_extractor(self):
        """Get the extractor"""
        # Get the extractor
        name = self.request.matchdict['name']
        extractor = BaseExtractor.objects.get(name=name)
        return extractor, name

    @view_config(route_name='extractor_view', renderer = 'template/extractor_view.jinja2')
    def view(self):
        """Just view the extractor"""

        extractor, name = self._get_extractor()

        return {
            'name': name,
            'extractor': extractor
        }

    @view_config(route_name='extractor_run')
    def run(self):
        """Reexport data"""

        # Get user request
        extractor, name = self._get_extractor()

        # Rerun extraction
        extractor.get_data(ignore_cache=True)
        extractor.save()

        raise exc.HTTPFound(self.request.route_url('extractor_view', name=name))


def includeme(config):
    config.add_route('extractor_view', '/extractor/{name}/view')
    config.add_route('extractor_run', '/extractor/{name}/run')
