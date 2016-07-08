from pyramid.view import view_config

from powerwall.toolchain import ToolChain


@view_config(route_name='home', renderer='template/home.jinja2')
def home(request):
    """Home page"""

    # Get the names of the extractors
    names = [ x.name for x in ToolChain.objects ]
    return {'names': names}


def includeme(config):
    """Used to perform includes for routes"""
    config.add_route('home', '/')