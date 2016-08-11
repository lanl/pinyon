"""Views for extractors"""
import os
from pyramid.response import Response
from pyramid.view import view_config
import pyramid.httpexceptions as exc
from tempfile import mkstemp

from pinyon.extract import BaseExtractor


class DataOutput:
    """Utility class for outputting data"""

    known_data_formats = {
        'csv': {'extension': 'csv', 'pandas': 'to_csv', 'kwargs': {'index': False}},
        'excel': {'extension': 'xlsx', 'pandas': 'to_excel', 'kwargs': {'index': False}},
        'pickle': {'extension': 'pkl', 'pandas': 'to_pickle', 'kwargs': {}},
        'json': {'extension': 'json', 'pandas': 'to_json', 'kwargs': {'orient': 'values'}}
    }
    """Data formats known by this class

    Key is the human name. Value is a dictionary where:
        'extension' is the desired file extension
        'pandas' is the pandas function name
        'kwargs' are any arguments to the pandas function
    """

    @classmethod
    def prepare_for_output(cls, data, data_format):
        """Convert a DataFrame object into a string

        :param data: Dataset to be transformed
        :param data_format: Desired format
        :return: DataFrame as string
        """

        if data_format not in DataOutput.known_data_formats:
            return exc.HTTPBadRequest(detail='Format unrecognized: %s' % data_format)

        output_settings = DataOutput.known_data_formats[data_format]

        # Write the object
        if data_format in ['excel', 'pickle']:
            # Write to temp file, read it
            fp, filename = mkstemp(output_settings['extension'])
            getattr(data, output_settings['pandas']) \
                (filename, **output_settings['kwargs'])
            output_data = open(filename, 'r').read()
            os.remove(filename)
        else:
            output_data = getattr(data, output_settings['pandas']) \
                (path_or_buf=None, **output_settings['kwargs'])

        return output_settings, output_data


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
            'format_options': DataOutput.known_data_formats.keys(),
        }

    @view_config(route_name='extractor_run')
    def run(self):
        """Reexport data"""

        # Get user request
        extractor, name = self._get_extractor()

        # Check if they specified to recursively run all subsequent tools
        go_recursive = self.request.GET.get('recursive', "False")
        go_recursive = True if go_recursive.lower() == "true" else False

        # Rerun extraction
        extractor.get_data(ignore_cache=True, run_subsequent=go_recursive)
        extractor.save()

        raise exc.HTTPFound(self.request.route_url('extractor_view', name=name))

    @view_config(route_name='extractor_data')
    def data(self):
        """Send out data for external program"""

        # Get user request
        extractor, name = self._get_extractor()

        # Get desired format
        data_format = self.request.GET.get('format', 'csv')

        # Render into desired format
        output_settings, output_data = DataOutput.prepare_for_output(extractor.get_data(), data_format)

        # Send out the data in CSV format
        return Response(
            content_type="application/force-download",
            content_disposition='attachment; filename=%s.%s'%(extractor.name, output_settings['extension']),
            body=output_data
        )


def includeme(config):
    config.add_route('extractor_view', '/extractor/{name}/view')
    config.add_route('extractor_run', '/extractor/{name}/run')
    config.add_route('extractor_data', '/extractor/{name}/data')
