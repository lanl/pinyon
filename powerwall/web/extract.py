"""Views for extractors"""
from pyramid.response import Response
from pyramid.view import view_config

from powerwall.extract import BaseExtractor


class ExtractorViews:

    def __init__(self, request):
        self.request = request

    @view_config(route_name='extractor_view', renderer = 'template/extractor_view.jinja2')
    def view(self):
        """Just view the extractor"""

        # Get the extractor
        name = self.request.matchdict['name']
        extractor = BaseExtractor.objects.get(name=name)

        return {
            'name': name,
            'extractor': extractor
        }


def includeme(config):
    config.add_route('extractor_view', '/extractor/{name}/view')
