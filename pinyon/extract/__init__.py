"""This module contains code for extracting data 
from various data repositories"""
import logging
import pickle as pickle

import datetime
from mongoengine import Document
from mongoengine.fields import DateTimeField, DictField, StringField

from pinyon.tool import WorkflowTool
from .. import KnownClass
from pandas import read_excel

__author__ = 'Logan Ward'


class BaseExtractor(Document):
    """Base class for extracting data from a certain resource"""
    meta = {'allow_inheritance': True}
    
    name = StringField(required=True, unique=True)
    """Name of the extractor"""

    description = StringField(required=True)
    """Description of the extractor.

    Can use HTML formatting"""

    last_exported = DateTimeField()
    """Last time the data was pull from the resource"""

    _data_cache = None
    """Storage for DataFrame object generated during extraction"""

    result = StringField(required=False)
    """Storage for the pickled form of _data_cache"""
    
    def get_data(self, ignore_cache=False, save_results=False, run_subsequent=False):
        """Extract data from a certain resource, assemble
        data into a tabular format

        Input:
            :param ignore_cache: boolean, whether to ignore any previously-saved result
            :param save_results: boolean, whether to save the extractor
            :param run_subsequent: boolean, whether to run subsequent tool
        Output:
            Panda's DataFrame object
        """

        # Check if the cache should be ignored
        if ignore_cache:
            # If so, clear it
            self.result = None
            self._data_cache = None

        # Either extract or use the cache
        if self._data_cache is not None:
            # Return cached object
            pass
        elif self.result is not None:
            self._data_cache = pickle.loads(self.result)
        else:
            # Run the extractor
            logging.info("Running extractor: %s"%self.name)
            self._data_cache = self._run_extraction()
            self.last_exported = datetime.datetime.now()

            # Save results, if needed
            if save_results:
                self.save()

            # Invalidate or re-run subsequent steps
            if run_subsequent:
                for tool in self.get_next_steps():
                    # For a re-run
                    tool.run(ignore_results=True, save_results=save_results, run_subsequent=True)
            else:
                for tool in self.get_next_steps():
                    tool.clear_results(save=save_results, clear_next_steps=True)

        return self._data_cache

    def _run_extraction(self):
        """Actually perform the data extraction.

        Not meant to be called directly by the user"""
        raise NotImplementedError()

    def save(self):
        # Register the class
        KnownClass.register_class(self)

        # If present, save pickled form of data
        if self._data_cache is not None:
            self.result = pickle.dumps(self._data_cache)

        return super(BaseExtractor, self).save()

    def get_toolchains(self):
        """Get the toolchains that use this data source

        :return: list of ToolChain, desired toolchains
        """
        from ..toolchain import ToolChain
        return ToolChain.objects(extractor=self)

    def get_next_steps(self):
        """Get all tool that directly pull data from this extractor"""

        # Get all the toolchains that use this extractor
        tc = self.get_toolchains()

        # Get all the tool in each chain that do not have a previous step (i.e., those that pull from the data source)
        output = []
        for t in tc:
            output.extend(WorkflowTool.objects(toolchain=t, previous_step__exists=False))
        return output

class ExcelExtractor(BaseExtractor):
    """Extractor designed to pull data from excel files"""

    path = StringField(required=True)
    """Path to target Excel file"""

    sheet = StringField(required=True)
    """Name of target sheet in target file"""

    import_options = DictField()
    """Any options for the read_excel function of pandas"""

    def _run_extraction(self):
        return read_excel(self.path, self.sheet, **self.import_options)