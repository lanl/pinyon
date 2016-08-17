from datetime import datetime

from mongoengine.document import EmbeddedDocument
from mongoengine.fields import StringField, DateTimeField


class Note(EmbeddedDocument):
    """Stores some kind of record about a tool"""

    _note = StringField(required=True)
    """User-specified note"""

    author = StringField(required=True)
    """Author of this note"""

    created = DateTimeField(required=True)
    """When this note was created"""

    edited = DateTimeField(required=True)
    """When this note was edited last"""

    def __init__(self, *args, **kwargs):
        super(Note, self).__init__(*args, **kwargs)

        # Mark when this note was created
        self.created = datetime.now()
        self.edited = datetime.now()

        # Set the note value
        if 'note' in kwargs:
            self.note = kwargs['note']

    @property
    def note(self):
        """User-specified note"""
        return self._note

    @note.setter
    def note(self,value):
        """Sets the value of the note

        :param value: New value of note
        """

        # Update the value
        self._note = value
        # When this note was last edited
        self.edited = datetime.now()
