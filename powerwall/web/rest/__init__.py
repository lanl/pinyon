from cornice import Service

rest_home = Service(name='rest_home', path='/rest')


@rest_home.get()
def get_version(request):
    """Print out the version number"""
    return "Hello REST user"


def includeme(config):
    config.scan('.extractor')

