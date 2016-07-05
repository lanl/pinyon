import unittest
from powerwall.extract.mdcs import *
import xmltodict
import os


class TestMDCSUtilities(unittest.TestCase):
    test_xml = xmltodict.parse(open(os.path.join('test-files', '1971jac2-0.xml')))

    def test_extractor(self):
        flat = ExtractorFlattener(['HardnessMeasurement', 'Hardness', 'measurement-type'], \
                                  name='HardnessType', description="Hi Logan!")
        val = flat.extract_data(self.test_xml)
        self.assertEquals('rockwell a', val)
        self.assertEquals('HardnessType', flat.name)
        self.assertEquals('Hi Logan!', flat.description)

    def test_physical_value_extractor(self):
        # No unit conversion
        flat = PhysicalQuantityExtractorFlattener(['HardnessMeasurement', 'AgingCondition', 'temperature'])
        self.assertEquals(25, flat.extract_data(self.test_xml))

        # With unit conversion
        flat = PhysicalQuantityExtractorFlattener(['HardnessMeasurement', 'AgingCondition', 'temperature'], units='kelvin')
        self.assertEquals(25+273.15, flat.extract_data(self.test_xml))

    def test_element_fraction(self):
        # Make the sample value
        value = dict(
            quantityUnit='mole fraction',
            constituent=[
                dict(element='Na', amount=0.5),
                dict(element='Cl', amount=0.5),
            ]
        )

        # mole percent
        flat = ElementFractionFlattener([], element='Na', mass=False, fraction=False)
        self.assertAlmostEqual(50, flat.extract_data(value), 2)

        # mole fraction
        flat = ElementFractionFlattener([], element='Na', mass=False, fraction=True)
        self.assertAlmostEqual(0.5, flat.extract_data(value), 2)

        # mass fraction
        flat = ElementFractionFlattener([], element='Na', mass=True, fraction=True)
        self.assertAlmostEqual(0.393372, flat.extract_data(value), 4)

        # mole fraction, but assuming that data is in mass fraction
        value['quantityUnit'] = 'mass percent'
        value['constituent'][0]['amount'] = 50
        value['constituent'][1]['amount'] = 50
        flat = ElementFractionFlattener([], element='Na', mass=False, fraction=False)
        self.assertAlmostEqual(60.6628, flat.extract_data(value), 4)

        # Test out on the test_xml
        flat = ElementFractionFlattener(['HardnessMeasurement', 'NominalComposition'], 'Nb')
        self.assertAlmostEqual(4.5, flat.extract_data(self.test_xml), 2)

    def test_composition_printer(self):
        # Make the sample value
        value = dict(
            quantityUnit='mass fraction',
            constituent=[
                dict(element='Na', amount=0.5),
                dict(element='Cl', amount=0.5),
            ]
        )

        # Mass percent, no units, no base element
        flat = CompositionPrinterFlattener([], mole_percent=False)
        self.assertEquals("Na50.0Cl50.0", flat.extract_data(value))

        # Mole percent, no units, no base element
        flat = CompositionPrinterFlattener([], mole_percent=True)
        self.assertEquals("Na60.7Cl39.3", flat.extract_data(value))

        # Mole percent, no units, base element=Na
        flat = CompositionPrinterFlattener([], mole_percent=True, base_element='Na')
        self.assertEquals("Na-39.3Cl", flat.extract_data(value))

        # Mole percent, units, base element=Na
        flat = CompositionPrinterFlattener([], mole_percent=True, base_element='Na', print_units=True)
        self.assertEquals("Na-39.3at%Cl", flat.extract_data(value))

        # Test on example record
        flat = CompositionPrinterFlattener(['HardnessMeasurement', 'NominalComposition'],
                                           base_element='U', mole_percent=False, print_units=True)
        self.assertEquals('U-4.5wt%Nb', flat.extract_data(self.test_xml))