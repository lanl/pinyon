from pyramid.response import Response
from pyramid.view import view_config
from ..extract import BaseExtractor


@view_config(route_name='home', renderer='template/home.jinja2')
def home(request):
    """Home page"""

    # Get the names of the extractors
    names = [ x.name for x in BaseExtractor.objects ]
    return {'names': names}


def includeme(config):
    """Used to perform includes for routes"""
    config.add_route('home', '/')
    config.add_route('load', '/load')