from unittest import TestCase

from bson.objectid import ObjectId

from powerwall import connect_to_database
from powerwall.extract import ExcelExtractor
from powerwall.toolchain import ToolChain
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


class BogusTool(WorkflowTool):
    def _run(self, data, other_inputs):
        return data, {'data2': data}


class TestWorkFlow(TestCase):

    def test_get_input(self):
        connect_to_database()
        # Make a toolchain
        tc = ToolChain(name='TestChain', description='A sample toolchain')
        tc.extractor = ExcelExtractor(path='./test-files/travel-times.xlsx')

        # Make a FilterExtractor
        wt = WorkflowTool(skip_register=True)
        wt.toolchain = tc
        inputs = wt.get_input()
        self.assertEquals(['data'], inputs.keys())

        # Make a fake tool that adds a second field to the output
        wt2 = BogusTool(skip_register=True)
        wt2.toolchain = tc

        wt.previous_step = wt2
        inputs = wt.get_input()
        # Should have the output form Bogus tool
        self.assertEquals(['data', 'data2'], inputs.keys())
        self.assertEquals(inputs['data'], inputs['data2'])

    def test_clone(self):
        connect_to_database()

        # Make a Workflow tool
        x = WorkflowTool(skip_register=True)

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