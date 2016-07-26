from mongoengine import Document
from mongoengine.fields import StringField, BinaryField


class BaseVisualizer(Document):
    """Base class for objects that create a visualization"""

    name = StringField(required=True, unique=True)
    """Name of this plot"""

    description = StringField(required=True)
    """Long-form description of this visualization"""

    type = StringField(required=True, regex="^[\w]+/[\w]+$")
    """HTML type of this visualization"""

    result_data = BinaryField(required=False)
    """Holds the image of the visualization"""

