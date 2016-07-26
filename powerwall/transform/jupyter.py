import cPickle as pickle
import inspect
import os

import nbformat
from mongoengine import BinaryField, DictField
from nbconvert.preprocessors import ExecutePreprocessor

from powerwall.utility import WorkflowTool


class JupyterNotebookTransformer(WorkflowTool):
    """Uses Jupyter notebook to perform a certain optimization step"""

    notebook = BinaryField(required=True)
    """Stores the actual notebook"""

    calc_settings = DictField()
    """Any settings for the calculation"""

    def __init__(self,*args,**kwargs):
        super(JupyterNotebookTransformer, self).__init__(*args, **kwargs)

    @classmethod
    def load_notebook(cls, name, description, path):
        """Load a notebook from disk, turn into transformer

        :param name: string, name of transformer
        :param description: string, description of transformer
        :param path: string, path to the notebook. None for default notebook
        :return: JupyterNotebookTransformer
        """
        x = JupyterNotebookTransformer(name=name, description=description)

        if path is None:
            x.notebook = open(os.path.join(
                os.path.dirname(inspect.getfile(x.__class__)),
                'jupyter_templates',
                'python2_template.ipynb'
            )).read()
        else:
            x.notebook = open(path).read()
        return x

    def get_settings(self):
        settings = super(JupyterNotebookTransformer, self).get_settings()

        # Don't print the whole notebook
        del settings['notebook']

        # Make the settings a little prettier
        del settings['calc_settings']
        settings.update(self.calc_settings)

        return settings

    def _run(self, data, other_inputs):
        # Combine data into a form to send to the notebook
        inputs = dict(other_inputs)
        inputs['data'] = data

        # Parse the notebook
        nb = nbformat.reads(self.notebook, nbformat.NO_CONVERT)
        self._add_data(nb, inputs)

        # Run the notebook
        ep = ExecutePreprocessor(timeout=-1)
        ep.preprocess(nb, {})

        # Get the results
        outputs = pickle.loads(eval(nb.cells[-1]['outputs'][0]['data']['text/plain']))
        data = outputs['data']
        del outputs['data']

        # Save the notebook
        self.notebook = str(nbformat.writes(nb))
        return data, outputs

    def _add_data(self, nb, inputs, use_placeholder=False):
        """Update the code used to import and export data into this notebook

        :param nb: NotebookNode, notebook used to perform the code
        :param input: dict, inputs provided to this nbformat
        :param use_placeholder: boolean, whether to put in an input / output placeholder
        """

        # Render the code
        if use_placeholder:
            import_code = "# Placeholder code for inputs"
            export_code = "# Placeholder code for outputs"
        else:
            import_code = "import cPickle as pickle\n" \
                        + ("powerwall = pickle.loads(%s)\n" % repr(pickle.dumps(inputs))) \
                        + ("settings = pickle.loads(%s)" % repr(pickle.dumps(self.calc_settings)))
            export_code = "pickle.dumps(powerwall)"
        self.check_notebook(nb)

        # Put them in the documents
        nb.cells[2]['source'] = import_code
        nb.cells[2]['metadata']['collapsed'] = True
        nb.cells[-1]['source'] = export_code
        nb.cells[-1]['metadata']['collapsed'] = True

        # For display mode, delete the last output
        nb.cells[-1]['outputs'] = {}

    def check_notebook(self, nb):
        if "Input Cell" not in nb.cells[1]['source'] or "Output Cell" not in nb.cells[-2]['source']:
            raise Exception('Notebook not in expected format. Please use the template')

    def load_workbook(self, f):
        """Load a workbook

        :param f: string or file-like object, path or object to be read from"""

        # Prepare to read
        if isinstance(f, str):
            fp = open(f, 'r')
        else:
            fp = f

        # Read it
        nb_str = fp.read()

        # Set the notebook
        self.set_notebook(nb_str)

    def set_notebook(self, nb_str):
        """Set the notebook from string, and check the format

        :param nb_str: string, notebook to be set
        """
        # Make sure it is in the correct format
        nb = nbformat.reads(nb_str, nbformat.NO_CONVERT)
        self.check_notebook(nb)

        # Set and leave
        self.notebook = nb_str

    def write_notebook(self, f):
        """Write the notebook to disk with the current data

        :param f: string or file-like object, path or object used to be written to disk. None to print to return string"""

        # Prepare to write
        if isinstance(f, str):
            fp = open(f, 'w')
        else:
            fp = f

        # Add data to the notebook
        nb = nbformat.reads(self.notebook, nbformat.NO_CONVERT)
        self._add_data(nb, self.get_input())

        # Write the notebook
        notebook = nbformat.writes(nb, nbformat.NO_CONVERT)
        if f is None:
            return notebook
        fp.write(notebook)

        if isinstance(f, str):
            fp.close()
