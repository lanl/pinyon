import unittest
from powerwall.extract.mdcs import *
import xmltodict
import os


class TestMDCSUtilities(unittest.TestCase):
    test_xml = xmltodict.parse(open(os.path.join('test-files', '1971jac2-0.xml')))

    def test_extractor(self):
        flat = ExtractorFlattener(location=['HardnessMeasurement', 'Hardness', 'measurement-type'], \
                                  name='HardnessType', description="Hi Logan!")
        val = flat.extract_data(self.test_xml)
        self.assertEquals('rockwell a', val)
        self.assertEquals('HardnessType', flat.name)
        self.assertEquals('Hi Logan!', flat.description)

    def test_physical_value_extractor(self):
        # No unit conversion
        flat = PhysicalQuantityExtractorFlattener(location=['HardnessMeasurement', 'AgingCondition', 'temperature'])
        self.assertEquals(25, flat.extract_data(self.test_xml))

        # With unit conversion
        flat = PhysicalQuantityExtractorFlattener(location=['HardnessMeasurement', 'AgingCondition', 'temperature'], units='kelvin')
        self.assertEquals(25+273.15, flat.extract_data(self.test_xml))

    def test_extractor_base(self):
        example_xml = xmltodict.parse('<a>' +
                                      '<b><english>Hello</english><spanish>Hola</spanish></b>' +
                                      '<b><english>Goodbye</english><spanish>Adios</spanish></b>' +
                                      '</a>')

        flat = ExtractorFlattener(location=['a',('b',0),'spanish'])
        self.assertEquals('Hola', flat.extract_data(example_xml))

        flat = ExtractorFlattener(location=['a', ('b', 'english', 'Hello'), 'spanish'])
        self.assertEquals('Hola', flat.extract_data(example_xml))

    def test_element_fraction(self):
        # Make the sample value
        value = {
            'quantity-type':'mole fraction',
            'constituent':[
                dict(element='Na', quantity=dict(value=0.5)),
                dict(element='Cl', quantity=dict(value=0.5)),
            ]
        }

        # mole percent
        flat = ElementFractionFlattener(location=[], element='Na', mass_units=False, fraction=False)
        self.assertAlmostEqual(50, flat.extract_data(value), 2)

        # mole fraction
        flat = ElementFractionFlattener(location=[], element='Na', mass_units=False, fraction=True)
        self.assertAlmostEqual(0.5, flat.extract_data(value), 2)

        # mass fraction
        flat = ElementFractionFlattener(location=[], element='Na', mass_units=True, fraction=True)
        self.assertAlmostEqual(0.393372, flat.extract_data(value), 4)

        # mole fraction, but assuming that data is in mass fraction
        value['quantity-type'] = 'mass percent'
        value['constituent'][0]['quantity']['value'] = 50
        value['constituent'][1]['quantity']['value'] = 50
        flat = ElementFractionFlattener(location=[], element='Na', mass_units=False, fraction=False)
        self.assertAlmostEqual(60.6628, flat.extract_data(value), 4)

        # Test out on the test_xml
        test_file = xmltodict.parse(open(os.path.join('test-files', '1971jac2-Figure10-0.xml')))
        flat = ElementFractionFlattener(location=['literature-data', 'material', 'nominal-composition'],
                                        element='Nb', mass_units=True)
        self.assertAlmostEqual(4.5, flat.extract_data(test_file), 2)

    def test_composition_printer(self):
        # Make the sample value
        value = {
            'quantity-type': 'mass fraction',
            'constituent': [
                dict(element='Na', quantity=dict(value=0.5)),
                dict(element='Cl', quantity=dict(value=0.5)),
            ]
        }

        # Mass percent, no units, no base element
        flat = CompositionPrinterFlattener(location=[], mole_percent=False)
        self.assertEquals("Na50.0Cl50.0", flat.extract_data(value))

        # Mole percent, no units, no base element
        flat = CompositionPrinterFlattener(location=[], mole_percent=True)
        self.assertEquals("Na60.7Cl39.3", flat.extract_data(value))

        # Mole percent, no units, base element=Na
        flat = CompositionPrinterFlattener(location=[], mole_percent=True, base_element='Na')
        self.assertEquals("Na-39.3Cl", flat.extract_data(value))

        # Mole percent, units, base element=Na
        flat = CompositionPrinterFlattener(location=[], mole_percent=True, base_element='Na', print_units=True)
        self.assertEquals("Na-39.3at%Cl", flat.extract_data(value))

        # Test on example record
        test_doc = xmltodict.parse(open(os.path.join('test-files', '1971jac2-Figure10-0.xml')))
        flat = CompositionPrinterFlattener(location=['literature-data', 'material', 'nominal-composition'],
                                           base_element='U', mole_percent=False, print_units=True)
        self.assertEquals('U-4.5wt%Nb', flat.extract_data(test_doc))


    def test_multiple_tags_aging(self):
        test_xml = xmltodict.parse(open(os.path.join('test-files', '1971jac2-Figure10-0.xml')))

        flat = PhysicalQuantityExtractorFlattener(
            location=['literature-data', 'material', 'processing', ('step', 'name', 'Aging'), 'ageing', 'time'],
            units='min'
        )

        self.assertEquals(60, flat.extract_data(test_xml))