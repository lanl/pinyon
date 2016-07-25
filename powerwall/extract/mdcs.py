"""Extractors and flattening operations designed for use with MDCS

This module is tailored towards materials, and has many operations that
assume data is structured according to certain schema. Where applicable,
the schema definition is specified along with the documentation if a
extractor is specifically tailored to a certain data structure.
"""
from __future__ import absolute_import

import mdcs

from powerwall import KnownClass
from . import BaseExtractor
from mongoengine.fields import *
from mongoengine import EmbeddedDocument, Document
import pandas as pd
from pint import UnitRegistry
from periodictable import elements as pt_elements

__author__ = 'Logan Ward'

_ureg = UnitRegistry(autoconvert_offset_to_baseunit = True)
"""Unit conversion tool"""


class EntryFlattener(EmbeddedDocument):
    """Base class for methods that flatten data from an MDCS data file."""
    meta={'allow_inheritance': True}
    
    name = StringField(required=True, unique=True, unique_with='_instance')
    """Name for this flattener object. Will be used as the name in 
    for the column with this data in the data table"""
    
    description = StringField(required=False)
    """Description of this data column """

    def __init__(self, *args, **kwargs):
        super(EntryFlattener, self).__init__(*args, **kwargs)

        # Register this object with Powerwall
        KnownClass.register_class(self)

    def extract_data(self, record):
        """Extract a data from an MDCS data record
        
        Input:
            record - OrderedDict, MDCS data record
        Output:
            value from this record. Can be nan or None
        """
        raise NotImplementedError()


class ExtractorFlattener(EntryFlattener):
    """Flattener that pulls data simply pulls from the MDCS record

    The data record from MDCS is passed as an OrderedDict from the API. Each element
     is represented as a key and its subelements as dictionary. In most cases, one just needs to specify a list of
     the keys to point to the correct location in the documented. For example, to get the value of the <b>
     field in the following document

     <a>
        <b>Yes</b>
        <c>No</c>
     </a>

     the proper location string would be ['a','b'], which would resolve to 'Yes'.

     As elements can appear multiple times, the XML parser (xmltodict) puts all instances of a certain element
        into a list. For example, for the document

      <a>
        <b>
            <english>Hello</english>
            <spanish>Hola</spanish>
        </b>
        <b>
            <english>Goodbye</english>
            <spanish>Adios</spanish>
        </b>
      </a>

    the location string ['a','b'] will resolve into a list [dict('english'='Hello', spanish='Hola'),
      dict('english'='Goodbye', spanish='Adios')]. To resolve which of these entries, we offer a few options all of which
      are based on providing a tuple to the location vector and not a string:

        1. ('tag', index) - Where index is an int defining the list index
        2. ('tag', 'subeelement', 'desired_value') - Which can be used to select the field with a subelement with a certain
            value. Using the previous example, ['a',('b','english','Hello')] will return the first entry (i.e., the one
            where the english field has a value of 'Hello')
    """
    
    location = ListField(StringField(), required=True)
    """Name of the field to extract"""

    def extract_data(self, record):
        # Iteratively move through data hierarchy
        current = record
        for loc in self.location:

            # Operation for a simple dictionary lookup
            if isinstance(loc, unicode):
                # Simple lookup
                if loc not in current:
                    return None
                else:
                    current = current[loc]

            # Handling duplicate keys
            else:
                if not type(loc) == tuple:
                    raise Exception('Due to duplicate elements, you must provide more information to specify which to retrieve')

                # Get the possibilities
                poss = current[loc[0]]
                if len(loc) == 2 and type(loc[1]) == int:
                    current = poss[loc[1]]
                elif len(loc) == 3:
                    hits = [ x for x in poss if x[loc[1]] == loc[2] ]
                    if len(hits) == 0:
                        return None # Subelement not found
                    elif len(hits) > 1:
                        raise Exception('More than 1 possibility found')
                    current = hits[0]

        return current


class PhysicalQuantityExtractorFlattener(ExtractorFlattener):
    """Extract a physical quantity from an entry
    
    The physical quantity is assumed to follow the format shown in: 
    https://github.com/MDCS-community/modular-data-models-include/blob/master/physical-quantity.xsd
    
    Has the ability to convert a quantity to a certain unit
    """
    
    units = StringField(required=False)
    """Desired units for the property value"""
            
    def extract_data(self, record):
        quantity = super(PhysicalQuantityExtractorFlattener, self).extract_data(record)
        
        # Make sure it exists
        if quantity is None:
            return quantity
        
        # Get the values
        values = quantity['value']

        # Convert to float
        if type(values) is list:
            values = [float(x) for x in values]
        else:
            values = float(values)
        
        # If no unit conversion desired, just return the values
        if self.units is None:
            return values
        
        # Prepare for unit conversion
        current_unit = _ureg.parse_expression(quantity['unit'])
        desired_unit = _ureg.parse_expression(self.units)
        
        # Run conversions
        if type(values) is list:
            return [(x * current_unit).m_as(desired_unit) for x in values]
        else:
            return (values * current_unit).m_as(desired_unit)


class ElementFractionFlattener(ExtractorFlattener):
    """Extract amount of a certain element for a composition object

    Assumes that the provided data is formatted according to simple-composition.xsd
    """

    element=StringField(max_length=2, required=True)
    """Element to be extracted"""

    mass_units=BooleanField(required=True)
    """Whether to express amount in in mass units"""

    fraction=BooleanField(required=True)
    """Whether to express amount in fraction or percentage"""

    @staticmethod
    def convert_composition(comp, to_mole):
        """Convert from mole to mass fraction

        Will convert to fractions (i.e., not percentages)

        Input:
            comp - dict, key is element symbol, value is amount
            to_mole - boolean, whether to convert to mole fraction. Note that
                this method assumes that the method always needs to be converted
        """

        # Convert to other units
        total_weight = 0.0
        for e,a in comp.iteritems():
            weight = a / pt_elements.symbol(e).mass if to_mole else a * pt_elements.symbol(e).mass
            comp[e] = weight
            total_weight += weight
        for e,a in comp.iteritems():
            comp[e] = a / total_weight

    def extract_data(self, record):
        # Get composition field
        comp_record = super(ElementFractionFlattener, self).extract_data(record)

        # Convert composition to a dict
        comp = dict()
        for entry in comp_record['constituent']:
            comp[entry['element']] = float(entry['amount'])

        # If no amount of this element, return 0 now
        if self.element not in comp:
            return 0

        # Run the conversion
        cur_type, cur_units = comp_record['quantityUnit'].split(" ")
        des_type = "mass" if self.mass_units else "mole"
        des_units = "fraction" if self.fraction else "percent"

        # Convert between percent and fraction if needed
        if cur_units != des_units:
            if cur_units == "fraction":
                for e, a in comp.iteritems():
                    comp[e] = a * 100.0
            else:
                for e, a in comp.iteritems():
                    comp[e] = a / 100.0

        # Convert between mole and mass fraction if needed
        if cur_type != des_type:
            to_mole = cur_type == "mass"

            # Convert to/from mole fraction
            self.convert_composition(comp, to_mole)

            # If percentage desired, multiply by 100
            if des_units == 'percent':
                for e, a in comp.iteritems():
                    comp[e] = 100.0 * a

        # Return result
        return comp.get(self.element, 0)


class CompositionPrinterFlattener(ExtractorFlattener):
    """Parse the composition into a human-friendly string

    Assumes data follows simple-composition.xsd
    """

    mole_percent=BooleanField(required=True)
    """Whether to print mole fractions or, conversely, mass fraction"""

    base_element=StringField(max_length=2)
    """A base element for the alloy"""

    print_units=BooleanField(required=True)
    """Whether to print at% or wt%"""

    def extract_data(self, record):
        # Get composition record
        comp_record = super(CompositionPrinterFlattener, self).extract_data(record)

        # Convert composition to a dict
        comp = dict()
        for entry in comp_record['constituent']:
            comp[entry['element']] = float(entry['amount'])

        # If needed, convert to between mole/mass
        cur_type, cur_units = comp_record['quantityUnit'].split(" ")
        if cur_type not in ['mass', 'mole']:
            raise Exception('Composition type not recognized: ' + comp_record['quantityUnit'])
        if cur_units not in ['fraction', 'percent']:
            raise Exception('Composition type not recognized: ' + comp_record['quantityUnit'])
        if (cur_type == 'mole') != self.mole_percent:
                ElementFractionFlattener.convert_composition(comp, self.mole_percent)

        # Convert to percentage
        if sum(comp.values()) <= 1:
            for e, a in comp.iteritems():
                comp[e] = a * 100

        # Render the amounts
        if self.print_units:
            for e, a in comp.iteritems(): comp[e] = "%.1f%s" % (a, 'at%' if self.mole_percent else 'wt%')
        else:
            for e, a in comp.iteritems(): comp[e] = "%.1f" % a

        # Print it out
        if self.base_element is None:
            return "".join(["%s%s" % (e, a) for e, a in comp.iteritems()])
        else:
            return self.base_element + "-" + "".join(
                ["%s%s" % (a, e) for e, a in comp.iteritems() if e != self.base_element]
            )


class MDCSExtractor(BaseExtractor):
    """A tool for extracting data from the MDCS and flattening it
    into a tabular format"""
    
    host = StringField(required=True)
    """URL of the MDCS host"""
    
    username = StringField(required=True)
    """User name for account used to extract data"""
    
    password = StringField()
    """Password for user account. Dev Note: At some point,
        we need to avoid storing this in plaintext"""
        
    template = StringField(required=True)
    """Name of template used to describe each MDCS record"""
        
    flatteners = ListField(EmbeddedDocumentField(EntryFlattener))
    """Tools used to flatten records from MDCS into a table"""
        
    def _run_extraction(self):
        # Get the schema ID for the data to be extracted
        schema_id = mdcs.templates.current_id(self.host,
                                              self.username,
                                              self.password,
                                              title=self.template)
            
        # Get the data records for this template
        entries = mdcs.explore.select(self.host,
                                      self.username,
                                      self.password,
                                      template=schema_id,
                                      format='json')
            
        # Extract data from the records
        data = pd.DataFrame()
        for flattener in self.flatteners:
            # Run the flatteners
            values = []
            for entry in entries:
                try:
                    values.append(flattener.extract_data(entry))
                except:
                    values.append(None)
            
            # Store in the DataFrame
            data[flattener.name] = values
            
        # Output the dataset
        return data
