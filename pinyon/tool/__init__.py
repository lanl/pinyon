import cPickle as pickle
import logging
from copy import deepcopy
from datetime import datetime

from mongoengine import Document, StringField, DateTimeField, ListField, EmbeddedDocumentField, ReferenceField, MapField
from wtforms import Form
import wtforms.fields as wtfields

from pinyon import KnownClass
from pinyon.artifacts import Artifact, PandasArtifact
from pinyon.utility import Note


class WorkflowTool(Document):
    """Abstract class that defines a workflow tool

    Stores name and description, any notes about the tool, and its dependencies. Provides a uniform interface to access
    these capabilities
    """

    meta = {'allow_inheritance': True}

    name = StringField(required=True, regex="^[^\\s+]*$", help_text='Short identifier of this tool')
    """Name of this tool. Cannot have whitespace"""

    description = StringField(required=True, help_text='Longer description of what this tool does')
    """Description of this tool"""

    last_run = DateTimeField(help_text='When this tool was run last')
    """Last time this object was run"""

    notes = ListField(EmbeddedDocumentField(Note), help_text='Any notes about this method')
    """Any notes about this tool"""

    previous_step = ReferenceField('WorkflowTool', help_text='Previous tool in chain. If none, this tool pulls from the data extractor')
    """Previous step / dependency for this tool.

    LW 11July2016: Consider making this a ListField to have multiple dependencies"""

    toolchain = ReferenceField('ToolChain', required=True, help_text='Toolchain this tool is part of')
    """Tool chain that this tool is associated with"""

    _result_cache = None
    """Holds a dictionary results from this calculation"""

    result = MapField(EmbeddedDocumentField(Artifact), help_text='Results produced by this tool, or inherited by any previous tools')
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

        :return: WTForm, used for editing
        """

        # Prepare the previous step choices
        previous_steps = [('extractor', self.toolchain.extractor.name)]
        for choice in self.get_acceptable_previous_steps():
            previous_steps.append((str(choice.id), choice.name))

        class EditForm(Form):
            name = wtfields.StringField('Tool Name', default=self.name,
                                        description='Simple name for this tool')
            description = wtfields.StringField('Tool Description', default=self.description,
                                               render_kw={'type': 'textarea'},
                                               description='Longer form description of what this tool does')
            previous_step = wtfields.SelectField('Previous Step', choices=previous_steps,
                                                 default=str(self.previous_step.id) if self.previous_step else 'extractor',
                                                 description='Previous step in toolchain. Supplies inputs into this tool')

        return EditForm

    def process_form(self, form, request):
        """Given a form, change the settings

        :param form: WTFrom.form.Form, form with new data for the class
        :param request: Request, request accompanying the form submission
        """

        # Make the changes
        self.name = form.name.data
        self.description = form.description.data

        # Get the previous step
        prev_step_choice = form.previous_step.data
        if prev_step_choice == 'extractor':
            self.previous_step = None
        else:
            self.previous_step = WorkflowTool.objects.get(id=prev_step_choice)

        # Clear the results
        self.clear_results()

    def get_file_information(self):
        """Get the list information files that are used as components of this class.

        Each file gets a dictionary, with keys
            description -> string, Short description of what this file is
            extension -> string, desired extension for for the file

        :return: dict, where key is the attribute name and value is a description of the file
        """

        return {}

    def get_inputs(self, save_results=False):
        """Get the results from the previous step, which are used as input into this transformer

        :param save_results: boolean, whether to ensure the previous tool saves new results
        :return: Dict, results from the previous step. Dictionary at least contains an entry 'data' that matches the
        dataset from the previous step
        """

        if self.previous_step is None:
            # Get data from the host workflow
            data = self.toolchain.extractor.get_data(save_results=save_results)

            # Store data as a pandas artifact
            return dict(data=data)

        # Get result from previous step
        return self.previous_step.run(save_results=save_results)

    def get_next_steps(self):
        """Get the tool have this tool as a previous step

        Output:
            :return: List of WorkflowTool objects
        """

        return WorkflowTool.objects.filter(previous_step=self)

    def get_all_next_steps(self):
        """Get any tools later in the toolchain

        Output:
            :return: set, all tools that are after this one """

        output = set(self.get_next_steps())

        for step in set(output):
            output.update(step.get_all_next_steps())

        return output

    def get_acceptable_previous_steps(self):
        """Get all steps that are not after this one in the chain

        Output:
            :return: set, all steps in the toolchain that are not after this
        """

        # Get the bad choices
        bad_tools = self.get_all_next_steps()
        return WorkflowTool.objects.filter(toolchain=self.toolchain,
                                           id__not__in=[x.id for x in bad_tools],
                                           id__ne=self.id)

    def get_all_previous_step(self):
        """Get any steps before this one

        Output:
            :return: list, all steps that are previous, where [0] is the immediately previous step"""

        # Nothing
        if not self.previous_step:
            return set()

        # Propogate!
        output = [self.previous_step]
        output.extend(self.previous_step.get_all_previous_steps())

        return output

    def run(self, ignore_results=False, save_results=False, run_subsequent=False):
        """Run an analysis tool

        If the tool has already been run, returns cached result

        Input:
            :param ignore_results: boolean, whether to redo calculation
            :param save_results: boolean, whether to save results
            :param run_subsequent: boolean, whether to run subsequent tool
        Output:
            :return: dict, result from the tool as Artifact objects
        """

        # Clear output if needed
        if ignore_results:
            self.clear_results()

        # Run it or unpickle cached result
        if self.last_run is None:
            # Inform the logger
            logging.info("Running %s"%self.name)

            # Get the inputs
            inputs = self.get_inputs(save_results=save_results)
            if 'data' not in inputs:
                raise Exception('Input does not include data field')

            # Remove data from its holder (to be easier to work with)
            data_artifact = inputs['data']
            data = data_artifact.get_object()
            del inputs['data']

            # Run the transformer
            data, outputs = self._run(data, inputs)

            # Put data back into the results object as a non-artifact
            outputs['data'] = data_artifact
            outputs['data'].set_object(data)
            self.result = outputs

            # Update the last run time
            self.last_run = datetime.now()

            # If desired, save results
            if save_results:
                self.save()

            # Now, clear or re-run subsequent calculations (which are now out of date)
            for tool in self.get_next_steps():
                if run_subsequent:
                    # Force it to rerun itself
                    tool.run(ignore_results=True, save_results=True, run_subsequent=True)
                else:
                        tool.clear_results(clear_next_steps=True, save=True)

        return self.result

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
        return self.run()['data'].get_object()

    def clear_results(self, clear_next_steps=False, save=False):
        """Clear any cached results

        :param clear_next_steps: bool, Whether to clear results of subsequent steps as well
        :param save: bool, whether to save the results
        """

        # Inform the logger
        logging.info("Clearing %s" % self.name)

        # Clear results in this class
        self.last_run = None
        self.result = {}

        # If desired, save
        if save:
            self.save()

        # If desired, clear any subsequent steps recursively
        if clear_next_steps:
            for tool in self.get_next_steps():
                tool.clear_results(clear_next_steps=True, save=save)

    def delete(self, update_dependencies=True, **write_concern):
        """Delete this object.

        :param update_dependencies: boolean, whether to take subsequent tool in a chain and attach them to the previous tool"""

        if update_dependencies:
            for tool in self.get_next_steps():
                tool.previous_step = self.previous_step
                tool.save()

        logging.info("Deleting %s" % self.name)

        super(WorkflowTool, self).delete(**write_concern)