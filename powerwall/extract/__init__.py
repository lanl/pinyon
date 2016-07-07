"""This module contains code for extracting data 
from various data repositories"""
from mongoengine import Document, StringField
from .. import KnownClass

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

    def save(self):
        # Register the class with the "Known Object"
        KnownClass.register_class(self)

        return super(BaseExtractor, self).save()
