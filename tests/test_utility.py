from unittest import TestCase

from powerwall.utility import Note


class TestNote(TestCase):

    def test(self):
        # Make a simple note
        note = Note()

        # Make sure that validation date is not null
        self.assertIsNotNone(note.created)
        self.assertIsNotNone(note.edited)

        # Set the note, and make sure the editted time changes
        note.note = "Hello"
        self.assertGreater(note.edited, note.created)