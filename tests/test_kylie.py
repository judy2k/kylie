#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for `kylie` module.
"""

import unittest

from kylie import (
    Model, Attribute, BaseModelChoice, Relation, MappedModelChoice,
    DeserializationError,
)


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


class DeserializationTestCase(unittest.TestCase):
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


class ConstructionTestCase(unittest.TestCase):
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


class SerializationTestCase(unittest.TestCase):
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


class OverwriteModel(Model):
    item = Attribute()

    def post_serialize(self, d):
        d['item'] = 'overwritten'


class PostSerializeTestCase(unittest.TestCase):
    def test_post_serialize(self):
        overwrite = OverwriteModel(item='item')
        d = overwrite.serialize()
        self.assertEqual(d['item'], 'overwritten')


class TypedModel(Model):
    model_type = None

    def post_serialize(self, d):
        d['__type__'] = self.model_type


class Cow(TypedModel):
    model_type = 'cow'


class Dog(TypedModel):
    model_type = 'dog'
    wagging = Attribute()


class PetOwner(Model):
    cow_or_dog = Relation(MappedModelChoice({
        'cow': Cow,
        'dog': Dog
    }))


class BaseModelChoiceTestCase(unittest.TestCase):
    def test_choose_model_is_abstract(self):
        """
        BaseModelChoice.choose_model should raise NotImplementedError
        """
        choice = BaseModelChoice()

        self.assertRaises(
            NotImplementedError,
            lambda: choice.choose_model('anything')
        )


class MappedModelTestCase(unittest.TestCase):
    def test_basic_type_switching(self):
        pet_owner = PetOwner.deserialize({
            'cow_or_dog': {'__type__': 'cow'}
        })
        self.assertTrue(isinstance(pet_owner.cow_or_dog, Cow))

    def test_switch_loads_attributes_properly(self):
        pet_owner = PetOwner.deserialize({
            'cow_or_dog': {'__type__': 'dog', 'wagging': True}
        })
        self.assertTrue(isinstance(pet_owner.cow_or_dog, Dog))
        self.assertTrue(pet_owner.cow_or_dog.wagging)

    def test_no_type(self):
        self.assertRaises(
            DeserializationError,
            lambda: PetOwner.deserialize(
                {'cow_or_dog': {'missing_type': True}}
            )
        )


if __name__ == '__main__':
    unittest.main()
