"""Views for extractors"""
import os
from pyramid.response import Response
from pyramid.view import view_config
import pyramid.httpexceptions as exc
from tempfile import mkstemp

from pinyon.artifacts import PandasArtifact
from pinyon.extract import BaseExtractor


class ExtractorViews:

    def __init__(self, request):
        self.request = request

    def _get_extractor(self):
        """Get the extractor"""
        # Get the extractor
        try:
            name = self.request.matchdict['name']
            extractor = BaseExtractor.objects.get(name=name)
            return extractor, name
        except:
            exc.HTTPNotFound(detail='No such extractor: %s' % name)

    @view_config(route_name='extractor_view', renderer='template/extractor_view.jinja2')
    def view(self):
        """Just view the extractor"""

        extractor, name = self._get_extractor()

        return {
            'name': name,
            'extractor': extractor,
            'format_options': PandasArtifact().available_formats().keys()
        }

    @view_config(route_name='extractor_run')
    def run(self):
        """Reexport data"""

        # Get user request
        extractor, name = self._get_extractor()

        # Check if they specified to recursively run all subsequent tool
        go_recursive = self.request.GET.get('recursive', "False")
        go_recursive = True if go_recursive.lower() == "true" else False

        # Rerun extraction
        extractor.get_data(ignore_cache=True, save_results=True, run_subsequent=go_recursive)

        raise exc.HTTPFound(self.request.route_url('extractor_view', name=name))

    @view_config(route_name='extractor_data')
    def data(self):
        """Send out data for external program"""

        # Get user request
        extractor, name = self._get_extractor()

        # Get desired format
        data_format = self.request.GET.get('format', 'csv')

        # Render into desired format
        data_artifact = extractor.get_data()
        output_data = data_artifact.render_output(data_format)
        extension = self.available_formats()[data_format]['extension']

        # Send out the data in CSV format
        return Response(
            content_type="application/force-download",
            content_disposition='attachment; filename=%s.%s'%(extractor.name, extension),
            body=output_data
        )


def includeme(config):
    config.add_route('extractor_view', '/extractor/{name}/view')
    config.add_route('extractor_run', '/extractor/{name}/run')
    config.add_route('extractor_data', '/extractor/{name}/data')
