"""This module contains code for extracting data 
from various data repositories"""
from mongoengine import Document, StringField

__author__ = 'Logan Ward'


class BaseExtractor(Document):
    """Base class for extracting data from a certain resource"""
    meta={'allow_inheritance': True}
    
    name=StringField(required=True)
    """Name of the extractor"""
    
    def get_data(self):
        """Extract data from a certain resource, assemble
        data into a tabular format
        
        Output:
            Panda's DataFrame object
        """
        raise NotImplementedError()
