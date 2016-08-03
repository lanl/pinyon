from pinyon.transform.jupyter import JupyterNotebookTransformer
from ..utility import WorkflowTool

import inspect
from jupyter import run_notebook
import cPickle as pickle
import os

from bs4 import BeautifulSoup
from jinja2 import Environment, DictLoader
from mongoengine.fields import *
from wtforms import fields as wtfields


class HTMLDecisionTracker(WorkflowTool):
    """Uses HTML forms to make changes made to data

    This tool works by rendering an HTML page that a user can employ to make changes to the dataset. This page contains
     a specially-formatted table marked with the id "pinyondata." As the table is edited, the cells that are changed
     are marked with the class "editedCell" and the notes behind the decision are stored as a attribute named "decision-notes."
     Once the user is done editing, the webpage sends back the HTML table and the locations and changes to
     the table identified and stored.

    The changes marked by the user are applied to the dataset when this tool is run.
    """

    entry_key = StringField()
    """Defines what key should used to be track which entries.

    If None, the Pandas index will be used. Setting this to another value (e.g., title of entry) makes these decisions
    more resistant to changes earlier in the workflow that might affect the entry number (e.g., adding more data).
    """

    _decisions_cache = None
    """A dictionary holding records of the decisions made

    Key of each entry is a tuple (key, column) defining where the change was made and the value is a tuple defining the
     decision that was made (old_value, new_value, notes). Where:
        key -> Key for this entry
        column -> Column of the record being adjusted
        old_value -> Original value
        new_value -> New value (post decision)
        notes -> Any notes about the decision
    """

    decisions = BinaryField(required=True)
    """Holds the pickled form of a dictionary holding the changes that were made."""

    html_template = BinaryField(required=True)
    """Holds the HTML template being used as the decision making tool"""

    columns = ListField(StringField())
    """Which columns to display"""

    @classmethod
    def load_template(cls, name, description, path, skip_register=False):
        """Load a HTML template from disk, use to intialize a decision tool

        :param name: string, name of transformer
        :param description: string, description of transformer
        :param path: string, path to the notebook. None for default page
        :param skip_register: boolean, whether to auto-register the tool
        :return: JupyterNotebookTransformer
        """
        x = HTMLDecisionTracker(name=name, description=description, skip_register=skip_register)

        if path is None:
            x.html_template = open(os.path.join(
                os.path.dirname(inspect.getfile(x.__class__)),
                'html_templates',
                'simple_example.jinja2'
            )).read()
        else:
            x.html_template = open(path).read()
        return x

    def get_settings(self):
        settings = super(HTMLDecisionTracker, self).get_settings()

        # Don't print the template or decisions
        del settings['decisions']
        del settings['html_template']

        return settings

    def get_form(self):
        super_form = super(HTMLDecisionTracker, self).get_form()

        class MyForm(super_form):
            html_template = wtfields.FileField('HTML Template',
                                               description='Jinja2 template used to render the decision form.',
                                               render_kw={'class': 'form-control-file'}
                                               )
            column_names = wtfields.StringField('Columns',
                                                default=", ".join(self.columns),
                                                description='Names of columns to be added, separated by commas')

        return MyForm

    def process_form(self, form, request):
        super(HTMLDecisionTracker, self).process_form(form, request)

        # Read in the template
        if not type(request.POST['html_template']) == unicode:
            self.html_template = str(request.POST['html_template'].file.read())
        self.columns= [x.strip() for x in form.column_names.data.split(",")]

    def get_decisions(self):
        """Get the dictionary of all decisions that were made

        :return: dict, record of decisions made"""

        if self._decisions_cache is not None:
            return self._decisions_cache
        if self._decisions_cache is None and self.decisions is not None:
            self._decisions_cache = pickle.loads(self.decisions)
            return self._decisions_cache
        else:
            return dict()

    def get_html_tool(self, **kwargs):
        """Generate the HTML tool used to make decisions

        Keyword arguments are extra arguments being passed to the template

        :return: Valid HTML page"""

        # Unpickle the decision cache
        if self._decisions_cache is None:
            self._decisions_cache = dict() if self.decisions is None else pickle.loads(self.decisions)

        # Get the template
        env = Environment(loader=DictLoader({'my_template': self.html_template}))
        template = env.get_template('my_template')

        # Get the stuff to be put in the page
        inputs = self.get_input()
        data = inputs['data']

        # Render data as html
        chosen_columns = None if len(self.columns) == 0 else self.columns
        output = data.to_html(columns=chosen_columns, na_rep='Unknown')
        soup = BeautifulSoup(output, 'lxml')
        table = soup.find('table')

        #  Add the "pinyondata" id to the table, to be able to find it in the mess
        table['id'] = 'pinyondata'

        #  Add coordinates to the table
        columns = ['index']
        if self.columns is None:
            columns.extend(data.columns)
        else:
            columns.extend(self.columns)
        for row, (rid, row_data) in zip(table.find('tbody').find_all('tr'), data.iterrows()):
            # Add coordinate to the row
            row['entry_key'] = rid if self.entry_key is None else str(row_data[self.entry_key])

            # Process the data entries
            for cell, col in zip(row.find_all(), columns):
                # Save the value in the HTML tage
                cell['column'] = col

                # Check for any decisions
                if (row['entry_key'], col) in self._decisions_cache:
                    # Get decision
                    decision = self._decisions_cache[(row['entry_key'], col)]

                    # Mark the decision
                    cell.string = decision[1]
                    cell['original-value'] = decision[0]
                    cell['class'] = ['editedCell']
                    cell['decision-notes'] = decision[2]

        # Render away!
        return template.render(
            data=data,
            data_html=str(table),
            tool=self,
            **kwargs
        )

    def process_results(self, result_data, save_results=False):
        """ Given the output results from the decision tool, get a list of decisions

        Decisions are returned as an HTML table. Cells that have been changed have a class of

        :param result_data: string, table rows from the decision table
        :param save_results: boolean, whether to save results after processing
        """

        # Get the soup!
        soup = BeautifulSoup(result_data, "lxml")

        # Get all entries that were changed
        cells = soup.find_all("td", class_="editedCell")

        # Store the decisions
        self._decisions_cache = dict()
        for cell in cells:
            # Get the coordinates
            key = cell.parent['entry_key']
            if self.entry_key is None:
                key = int(key)
            column = cell['column']
            key = (key, column)

            # Get the decison notes
            old_value = cell['original-value']
            new_value = cell.string.strip()
            decisionnotes = cell['decision-notes']
            value = (old_value, new_value, decisionnotes)

            # Store them in the list
            self._decisions_cache[key] = value

        # Optionally,save
        if save_results:
            self.save()

    def _run(self, data, other_inputs):
        # Clone the input data
        output_data = data.copy()

        # Unpack the decisions
        if self._decisions_cache is None:
            self._decisions_cache = pickle.loads(self.decisions)

        # Apply them
        for (entry_id, column), (old_value, new_value, reasons) in self._decisions_cache.iteritems():
            # Lookup entry ID if needed
            if self.entry_key is not None:
                hits = data.query('%s == "%s"'%(self.entry_key, entry_id))
                if len(hits) == 0:
                    raise Exception('Entry %s not found'%entry_id)
                elif len(hits) > 1:
                    raise Exception('More than one hit for entry %s'%entry_id)
                entry_id, entry = hits.iterrows().next()

            # Make the change
            if new_value.lower() == "true":
                new_value = True
            elif new_value.lower() == "false":
                new_value = False
            output_data.ix[entry_id, 'BeforePeak'] = new_value

        return output_data, other_inputs

    def save(self):
        # Add in an empty dictionary if no decisions are recorded
        if self._decisions_cache is None and self.decisions is None:
            self._decisions_cache = dict()

        # Pickle decision cache (if present)
        if self._decisions_cache is not None:
            self.decisions = pickle.dumps(self._decisions_cache)

        # Run the normal save
        super(HTMLDecisionTracker, self).save()


class BokehHTMLDecisionTracker(HTMLDecisionTracker):
    """A decision tracker that includes a Bokeh decision tracker

    Uses a Jupyter notebook in the background to generate the scripts and other data required to run the Bokeh plot"""

    notebook = BinaryField(required=True)
    """Notebook used to make the """

    def get_settings(self):
        last = super(BokehHTMLDecisionTracker, self).get_settings()

        del last['notebook']

        return last

    def load_notebook(cls, name, description, path):
        if path is None:
            path = os.path.join(
                os.path.dirname(inspect.getfile(cls.__class__)),
                'jupyter_templates',
                'python2_template.ipynb'
            )
        return JupyterNotebookTransformer.load_notebook(name, description, path)

    def get_html_tool(self, **kwargs):
        # First, run the underlying notebook to get the Bokeh plot information
        self.notebook, plot_data = run_notebook(self.notebook, self.get_input(), {})

        # Pass it on the tool renderer
        return super(BokehHTMLDecisionTracker, self).get_html_tool(**plot_data)

    def get_form(self):
        super_form = super(BokehHTMLDecisionTracker, self).get_form()

        class MyForm(super_form):
            notebook = wtfields.FileField('Notebook',
                                           description='Jupyter notebook used to generate the Bokeh figure components.',
                                           render_kw={'class': 'form-control-file'}
                                         )

        return MyForm

    def process_form(self, form, request):
        super(BokehHTMLDecisionTracker, self).process_form(form, request)

        # Read in the template
        if not type(request.POST['notebook']) == unicode:
            self.notebook = str(request.POST['notebook'].file.read())
