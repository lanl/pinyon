from unittest import TestCase

from bson.objectid import ObjectId

from powerwall.utility import Note, WorkflowTool


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


class TestWorkFlow(TestCase):

    def test_clone(self):
        # Make a Workflow tool
        x = WorkflowTool()

        # Set some fake values
        x.notes = [Note(note='note')]
        x._result_cache = 'res'
        x.result = str(dict(data='none'))
        x.previous_step = ObjectId()
        x.name = 'Hello'
        x.description = 'World'
        x.toolchain = ObjectId()

        # Make a clone, check results
        y = x.clone()
        self.assertEquals(x.name, y.name)
        self.assertEquals(x.description, y.description)
        self.assertIsNone(y.last_run)
        self.assertEquals(0, len(y.notes))
        self.assertIsNone(y.previous_step)
        self.assertEquals(x.toolchain, y.toolchain.id)
        self.assertIsNone(y._result_cache)
        self.assertIsNone(y.result)

        # Make a clone with new name/description, check results
        y = x.clone(name='NewName', description='NewDescription')
        self.assertEquals('NewName', y.name)
        self.assertEquals('NewDescription', y.description)
        self.assertIsNone(y.last_run)
        self.assertEquals(0, len(y.notes))
        self.assertIsNone(y.previous_step)
        self.assertEquals(x.toolchain, y.toolchain.id)
        self.assertIsNone(y._result_cache)
        self.assertIsNone(y.result)