"""Web views for tools"""
import nbformat
import nbconvert
from nbconvert.exporters.html import HTMLExporter
from pyramid.response import Response
from pyramid.view import view_config
import pyramid.httpexceptions as exc
import cPickle as pickle

from powerwall.transform.jupyter import JupyterNotebookTransformer
from powerwall.utility import WorkflowTool
from .extract import DataOutput


class ToolViews:

    def __init__(self, request):
        self.request = request

    def _get_tool(self):
        """Get the tool"""
        # Get the tool
        try:
            tid = self.request.matchdict['id']
            tool = WorkflowTool.objects.get(id=tid)
            return tool, tid
        except:
            exc.HTTPNotFound(detail='No such tool: %s' % tid)

    @view_config(route_name='tool_view', renderer='template/tool_view.jinja2')
    def view(self):
        """Just view the tool"""

        tool, name = self._get_tool()

        return {
            'name': name,
            'tool': tool,
            'format_options': DataOutput.known_data_formats.keys(),
            'is_jupyter': isinstance(tool, JupyterNotebookTransformer)
        }

    @view_config(route_name='tool_run')
    def run(self):
        """Reexport data"""

        # Get user request
        tool, name = self._get_tool()

        # Rerun extraction
        tool.run(ignore_results=True, save_results=True)
        tool.save()

        raise exc.HTTPFound(self.request.route_url('tool_view', id=name))

    @view_config(route_name='tool_data')
    def data(self):
        """Send out data for external program"""

        # Get user request
        tool, name = self._get_tool()

        # Get desired format
        data_format = self.request.GET.get('format', 'csv')

        # Get the results of the tool
        res = tool.run(save_results=True)

        # Render into desired format
        output_settings, output_data = DataOutput.prepare_for_output(res['data'], data_format)

        # Send out the data in CSV format
        return Response(
            content_type="application/force-download",
            content_disposition='attachment; filename=%s.%s' % (name, output_settings['extension']),
            body=output_data
        )

    @view_config(route_name='tool_output')
    def output(self):
        """Download an output from this tool"""

        # Get the requested tool
        tool, tid = self._get_tool()

        # Get request output
        output_name = self.request.matchdict['piece']

        # Get that object, or throw a 404
        outputs = tool.run(save_results=True)
        if output_name not in outputs:
            return exc.HTTPNotFound(detail='No such output: %s'%output_name)
        output = outputs[output_name]

        # Render that object as a pkl and return
        return Response(
            content_type="application/force-download",
            content_disposition='attachment; filename=%s.%s' % (output_name, 'pkl'),
            body=pickle.dumps(output)
        )

    @view_config(route_name='tool_jupyter')
    def render_notebook(self):

        # Get the requested tool
        tool, tid = self._get_tool()

        # If this is an IPython notebook, render it into HTML
        if not isinstance(tool, JupyterNotebookTransformer):
            return exc.HTTPNotAcceptable(detail='Tool is not a Jupyter notebook')

        # Get whether to download or view in HTML
        output_style = self.request.GET.get('format', 'html')

        # Load in the notebook
        if output_style == 'html':
            # Parse the notebook as an notebook object
            nb = nbformat.reads(tool.notebook, nbformat.NO_CONVERT)
            tool._add_data(nb, None, use_placeholder=True)

            # Render it as HTML
            ex = HTMLExporter()
            output, _ = ex.from_notebook_node(nb)
            return Response(output)

        elif output_style == 'file':
            return Response(
                content_type='application/force-download',
                content_dispsoition='attachment; filename=%s.%s'%(tool.name, 'ipynb'),
                body=tool.write_notebook(None)
            )
        else:
            return exc.HTTPBadRequest(detail='Format not recognized: ' + output_style)


def includeme(config):
    config.add_route('tool_view', '/tool/{id}/view')
    config.add_route('tool_run', '/tool/{id}/run')
    config.add_route('tool_data', '/tool/{id}/data')
    config.add_route('tool_output', '/tool/{id}/output/{piece}')
    config.add_route('tool_jupyter', '/tool/{id}/jupyter')
