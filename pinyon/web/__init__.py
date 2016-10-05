from pyramid.config import Configurator

from .. import connect_to_database, import_all_known_classes

from ..extract import BaseExtractor


def main(global_config, **settings):
    """Launch a Pyramid server. Used by PasteDeploy"""

    # Connect to mongoDB
    connect_to_database()

    # Make sure all known classes are registered
    import_all_known_classes(debug=True)

    # Create the configuration tool
    config = Configurator(settings=settings)
    
    # Add in additional modules
    config.include('pyramid_jinja2')
    
    # Add in static directories
    config.add_static_view(name='static', path='pinyon:web/static')

    # Add in the routes
    config.include('.extract')
    config.include('.home')
    config.include('.toolchain')
    config.include('.tool')

    # Add in the views
    config.scan()

    # San the REST interface
    config.scan('.rest')

    # Render the web server
    return config.make_wsgi_app()
