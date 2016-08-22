"""Classes used to store results from processing steps, and facilitate converting them to different formats"""
import cPickle as pickle
from tempfile import mkstemp

import os
from mongoengine.document import EmbeddedDocument
from mongoengine.fields import *


class Artifact(EmbeddedDocument):
    """Holds a output from a tool, and facilitates transforming it into other, useful formats"""

    meta = {'allow_inheritance': True}

    name = StringField(required=True, regex="^[^\\s+]*$", help_text='Name of this artifact. No whitespace')

    description = StringField(required=True, help_text='Longer description of this artifact')

    object = BinaryField(required=True, help_text='Raw data for this artifact')

    def available_formats(self):
        """List the available output formats for this data

        :return: dict, where key is the name of the format and value is a dict holding:
            extension -> desired file extension
            description -> What this format means
        """

        return dict(raw=dict(extension='data', description='Raw value of the output, unformatted'))

    def default_format(self):
        """Default format for output

        :return: string, default format"""

        return 'raw'

    def render_output(self, target_format, **kwargs):
        """Handles turning the data into the required format

        kwargs are, potentially, used by the conversion

        :param target_format: string, desired format for the output
        :return: probably string, output rendered into the desired form
        """

        if target_format == 'raw':
            return self.object
        else:
            raise Exception('No such format: %s' % target_format)


class PythonArtifact(Artifact):
    """Holder for an artifact that is a Python object

    The object is saved in pickled format. To facilitate moving in and out the format, there are two utility operations:
        set_object(x) and get_object

    """

    def available_formats(self):
        output = super(PythonArtifact, self).available_formats()

        output['pkl'] = dict(extension='pkl', description='Object in pickle format')
        del output['raw']

        return output

    def default_format(self):
        return 'pkl'

    def set_object(self, x):
        self.object = pickle.dumps(x)

    def get_object(self):
        return pickle.loads(self.object)

    def render_output(self, target_format, **kwargs):
        if target_format == 'pkl':
            return self.object
        else:
            super(PythonArtifact, self).render_output(target_format, **kwargs)


class PandasArtifact(PythonArtifact):
    """Stores a Pandas data file"""

    def available_formats(self):
        output = super(PandasArtifact, self).available_formats()

        # Prepare out
        output['csv'] = dict(extension='csv', description='Comma-separated values file')
        output['excel'] = dict(extension='xlsx', description='Compatible with Microsoft Excel')
        output['json'] = dict(extension='json', description='JavaScript Object Notation file')
        output['html'] = dict(extension='html', description='HTML table')

        return output

    def default_format(self):
        return 'excel'

    def render_output(self, target_format, **kwargs):

        # Get the pandas object
        data = self.get_object()

        if target_format == 'csv':
            return data.to_csv(index=False, **kwargs)
        elif target_format == 'excel':
            fp, filename = mkstemp(suffix='.xlsx')
            data.to_excel(filename, index=False, **kwargs)
            output_data = open(filename, 'r').read()
            os.remove(filename)
            return output_data
        elif target_format == 'json':
            return data.to_json(**kwargs)
        elif target_format == 'html':
            return data.to_html(index=False)
        else:
            return super(PandasArtifact, self).render_output(target_format, **kwargs)