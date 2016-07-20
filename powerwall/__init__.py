import importlib
import mongoengine as mge
from mongoengine.document import Document
from mongoengine.errors import DoesNotExist
from mongoengine.fields import StringField

__author__ = 'Logan Ward'


mongodb_settings = dict(
    name='powerwall',
    user='powerwall_user',
    pswd='powerwall_user',
    host='127.0.0.1',
    port=27018
)
"""Settings for MongoDB server"""


class KnownClass(Document):
    """Record of a certain type of document being present in database

    This collection is designed for storing the full class name (i.e., including module) of a class, so that it
    """

    module_name = StringField(required=True)
    """Name of the module of class being registered"""

    class_name = StringField(required=True, unique_with=['module_name'])
    """Name of the class being registered"""

    @staticmethod
    def register_class(obj):
        """Register a class in the KnownClass database

        :param obj: Object to be registered
        """
        try:
            KnownClass.objects.get(module_name=obj.__module__, class_name=obj.__class__.__name__)
        except DoesNotExist:
            # Create it
            KnownClass(module_name = obj.__module__, class_name = obj.__class__.__name__).save()


def connect_to_database(**setting_overrides):
    """Connect to the MongoDB supporting powerwall

    :param setting_overrides: any settings to be overrode
    from the conventional mongoDB settings
    """

    # Make a local copy of the settings
    settings = dict(mongodb_settings)
    settings.update(setting_overrides)

    # Connect!
    return mge.connect(settings['name'],
                       host=settings['host'],
                       port=settings['port'],
                       username=settings['user'],
                       password=settings['pswd']
    )


def import_all_known_classes(debug=False):
    """Imports all classes known in the KnownClass database

    :param debug: boolean, whether to print which classes are being imported
    """

    for cls in KnownClass.objects:
        if debug:
            print "Importing %s.%s"%(cls.module_name, cls.class_name)
        mod = importlib.import_module(cls.module_name)
        cls = getattr(mod, cls.class_name)
        cls()
