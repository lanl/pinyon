"""This module contains code for extracting data 
from various data repositories"""
import pickle as pickle

import datetime
from mongoengine import Document, StringField
from mongoengine.fields import DateTimeField

from .. import KnownClass

__author__ = 'Logan Ward'


class BaseExtractor(Document):
    """Base class for extracting data from a certain resource"""
    meta = {'allow_inheritance': True}
    
    name = StringField(required=True, unique=True)
    """Name of the extractor"""

    last_exported = DateTimeField()
    """Last time the data was pull from the resource"""

    _data_cache = None
    """Storage for DataFrame object generated during extraction"""

    result = StringField(required=False)
    """Storage for the pickled form of _data_cache"""
    
    def get_data(self, ignore_cache=True):
        """Extract data from a certain resource, assemble
        data into a tabular format
        
        Output:
            Panda's DataFrame object
        """

        # Check if the cache should be ignored
        if ignore_cache:
            self.result = None
            self._data_cache = self._run_extraction()
            self.last_exported = datetime.datetime.now()
            return self._data_cache

        # Either extract or use the cache
        if self._data_cache is not None:
            # Return cached object
            pass
        elif self.result is not None:
            self._data_cache = pickle.loads(self.result)
        else:
            self._data_cache = self._run_extraction()
            self.last_exported = datetime.datetime.now()
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
            self.result = pickle.dumps(self._data_cache, 0)

        return super(BaseExtractor, self).save()
