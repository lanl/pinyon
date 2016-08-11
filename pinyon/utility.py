import cPickle as pickle
from copy import deepcopy
from datetime import datetime
import logging

from mongoengine.fields import EmbeddedDocumentField, ListField, StringField, DateTimeField, ReferenceField, BinaryField
from mongoengine.document import EmbeddedDocument, Document
from wtforms.form import Form
from wtforms import fields as wtfields

from pinyon import KnownClass


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


class WorkflowTool(Document):
    """Abstract class that defines a workflow tool

    Stores name and description, any notes about the tool, and its dependencies. Provides a uniform interface to access
    these capabilities
    """

    meta = {'allow_inheritance': True}

    name = StringField(required=True, regex="^[^\\s+]*$")
    """Name of this tool. Cannot have whitespace"""

    description = StringField(required=True)
    """Description of this tool"""

    last_run = DateTimeField()
    """Last time this object was run"""

    notes = ListField(EmbeddedDocumentField(Note))
    """Any notes about this tool"""

    previous_step = ReferenceField('WorkflowTool')
    """Previous step / dependency for this tool.

    LW 11July2016: Consider making this a ListField to have multiple dependencies"""

    toolchain = ReferenceField('ToolChain', required=True)
    """Tool chain that this tool is associated with"""

    _result_cache = None
    """Holds a dictionary results from this calculation"""

    result = BinaryField()
    """Holds the pickled version of `result_cache`"""

    def __init__(self, *args, **kwargs):
        super(WorkflowTool, self).__init__(*args, **kwargs)

        # Register this class with the KnownClass library
        if not ('skip_register' in kwargs and kwargs['skip_register']):
            KnownClass.register_class(self)

    def clone(self, name=None, description=None):
        """Create a new copy of this tool

        :param name: string, new name for new copy
        :param description: string, description for new copy
        :return: WorkflowTool, new copy of this object"""

        # Make a copy
        output = deepcopy(self)
        output.id = None
        output.previous_step = None

        # Set name of description, if desired
        if name:
            output.name = name
        if description:
            output.description = description

        # Clear the notes, and anything related to result
        output.result_cache = None
        output.result = None
        output.last_run = None
        output.notes = []

        return output

    def get_settings(self):
        """Get the settings that could be printed or adjusted via a web form

        :return: dict of settings to be printed"""
        output = dict(self._data)
        for nogo in ['id', 'name', 'description', 'notes', 'last_run', 'toolchain', 'result', 'previous_step']:
            del output[nogo]
        return output

    def get_form(self):
        """Get a WTForm class that can be used to edit this class

        :return: WTForm, used for editting
        """

        class EditForm(Form):
            name = wtfields.StringField('Tool Name', default=self.name,
                                        description='Simple name for this tool')
            description = wtfields.StringField('Tool Description', default=self.description,
                                               render_kw={'type': 'textarea'},
                                               description='Longer form description of what this tool does')

        return EditForm

    def process_form(self, form, request):
        """Given a form, change the settings

        :param form: WTFrom.form.Form, form with new data for the class
        :param request: Request, request accompanying the form submission
        """

        # Make the changes
        self.name = form.name.data
        self.description = form.description.data

        # Clear the results
        self.clear_results()

    def get_input(self, save_results=False):
        """Get the results from the previous step, which are used as input into this transformer

        :param save_results: boolean, whether to ensure the previous tool saves new results
        :return: Dict, results from the previous step. Dictionary at least contains an entry 'data' that matches the
        dataset from the previous step
        """

        if self.previous_step is None:
            # Get data from the host workflow
            data = self.toolchain.extractor.get_data(save_results=save_results)

            # Return the dictionary
            return {'data': data}

        # Get result from previous step
        return self.previous_step.run(save_results=save_results)

    def get_next_steps(self):
        """Get the tools have this tool as a previous step

        Output:
            :return: List of WorkflowTool objects
        """

        return WorkflowTool.objects.filter(previous_step=self)

    def run(self, ignore_results=False, save_results=False, run_subsequent=False):
        """Run an analysis tool

        If the tool has already been run, returns cached result

        Input:
            :param ignore_results: boolean, whether to redo calculation
            :param save_results: boolean, whether to save results
            :param run_subsequent: boolean, whether to run subsequent tools
        Output:
            :return: dict, result from the analysis tool
        """

        # Clear output if needed
        if ignore_results:
            self.clear_results()

        # Run it or unpickle cached result
        if self._result_cache is None:
            if self.result is not None:
                self._result_cache = pickle.loads(self.result)
            else:
                # Inform the logger
                logging.info("Running %s"%self.name)

                # Get the inputs
                inputs = self.get_input(save_results=save_results)
                if 'data' not in inputs:
                    raise Exception('Input does not include data field')
                data = inputs['data']
                del inputs['data']

                # Run the transformer
                data, outputs = self._run(data, inputs)
                outputs['data'] = data
                self._result_cache = outputs
                self.last_run = datetime.now()

                # Now, clear or re-run subsequent calculations (which are now out of date)
                for tool in self.get_next_steps():
                    if run_subsequent:
                        # Force it to rerun itself
                        tool.run(ignore_results=True, save_results=True, run_subsequent=True)
                    else:
                        tool.clear_results(clear_next_steps=True, save=True)

                # If desired, save results
                if save_results:
                    self.save()

        # Print out the results
        return self._result_cache

    def _run(self, data, other_inputs):
        """Do the actual running

        :param data: DataFrame, data to be transformed
        :param other_inputs: dict, other inputs to the transformer
        :return: DataFame holding results after processing, Dictionary holding other results from this tool
        """
        raise NotImplementedError()

    def get_data(self):
        """Get at after this step

        :return: DataFrame
        """
        return self.run()['data']

    def clear_results(self, clear_next_steps=False, save=False):
        """Clear any cached results

        :param clear_next_steps: bool, Whether to clear results of subsequent steps as well
        :param save: bool, whether to save the results
        """

        # Inform the logger
        logging.info("Clearing %s" % self.name)

        # Clear results in this class
        self.last_run = None
        self._result_cache = None
        self.result = None

        # If desired, save
        if save:
            self.save()

        # If desired, clear any subsequent steps recursively
        if clear_next_steps:
            for tool in self.get_next_steps():
                tool.clear_results(clear_next_steps=True, save=save)

    def save(self):
        # Pickle result cache, if present
        if self._result_cache is not None:
            self.result = pickle.dumps(self._result_cache)

        super(WorkflowTool, self).save()
