#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for `kylie` module.
"""

import unittest

from kylie import Model, Attribute, Relation


def complex_unpack(d):
    return complex(d['real'], d['imaginary'])


def complex_pack(c):
    return {
        'real': c.real,
        'imaginary': c.imag
    }


class SpanishInquisitionModel(Model):
    inquisition_id = Attribute('id')
    expected = Attribute(python_type=bool, serialized_type=int)


class PersonModel(Model):
    name = Attribute()


class BobModel(Model):
    bob_id = Attribute("id")
    entry_fee = Attribute()
    is_happy = Attribute(python_type=bool, serialized_type=int)
    complex_type = Attribute(python_type=complex_unpack,
                             serialized_type=complex_pack)
    spanish_inquisition = Relation(
        SpanishInquisitionModel, 'spanishInquisition')
    null = Attribute()
    people = Relation(PersonModel, sequence=True)


class TestDeserialization(unittest.TestCase):
    def setUp(self):
        self.data = {
            'id': 123456,
            'entry_fee': 12,
            'is_happy': 0,
            'spanishInquisition': {
                'expected': 1, 'id': 5678
            },
            'complex_type': {
                'real': 2,
                'imaginary': 1,
            },
            'people': [
                {
                    'name': 'Alice'
                },
                {
                    'name': 'Sue'
                }
            ],
            'null': None,
        }
        self.bob = BobModel.deserialize(self.data)

    def test_attr_mapping(self):
        self.assertEqual(self.bob.bob_id, 123456)

    def test_no_mapping(self):
        self.assertEqual(self.bob.entry_fee, 12)

    def test_type_conversion(self):
        self.assertEqual(self.bob.is_happy, False)

    def test_relation_load(self):
        self.assertEqual(self.bob.spanish_inquisition.inquisition_id, 5678)

    def test_custom_unpack(self):
        self.assertEqual(self.bob.complex_type, complex(2, 1))

    def test_null_value(self):
        self.assertEqual(self.bob.null, None)


class TestConstruction(unittest.TestCase):
    def test_empty_init(self):
        inquisition = SpanishInquisitionModel()
        self.assertEqual(inquisition.inquisition_id, None)
        self.assertEqual(inquisition.expected, None)

    def test_positional_params(self):
        self.assertRaises(TypeError, lambda: SpanishInquisitionModel(12, True))

    def test_named_params(self):
        inquisition = SpanishInquisitionModel(
            inquisition_id=12, expected=False)
        self.assertEqual(inquisition.inquisition_id, 12)
        self.assertEqual(inquisition.expected, False)


class TestSerialization(unittest.TestCase):
    def setUp(self):
        inquisition = SpanishInquisitionModel(
            inquisition_id=10, expected=False)
        bob = BobModel(
            bob_id=42,
            entry_fee=7,
            is_happy=True,
            spanish_inquisition=inquisition,
            complex_type=complex(4, 7),
            people=[
                PersonModel(name='Alice'),
                PersonModel(name='Sue'),
            ]
        )

        self.data = bob.serialize()

    def test_attr_mapping(self):
        self.assertEqual(self.data['id'], 42)

    def test_no_mapping(self):
        self.assertEqual(self.data['entry_fee'], 7)

    def test_type_conversion(self):
        self.assertEqual(self.data['is_happy'], 1)

    def test_relation_load(self):
        inquisition_data = self.data.get('spanishInquisition')
        self.assertNotEqual(inquisition_data, None)
        self.assertEqual(inquisition_data['id'], 10)
        self.assertEqual(inquisition_data['expected'], 0)

    def test_custom_pack(self):
        self.assertEqual(self.data['complex_type'], {
            'real': 4, 'imaginary': 7,
        })

    def test_null_value(self):
        self.assertEqual(self.data['null'], None)


if __name__ == '__main__':
    unittest.main()
