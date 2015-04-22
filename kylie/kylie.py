# -*- coding: utf-8 -*-

"""
kylie.kylie - Internal implementation of the `kylie` package.

You probably want to use the `kylie` package directly, instead of this on, as
that is the public interface.
"""

from __future__ import print_function


def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""
    # This function was pasted from the `six` library.
    #
    # This requires a bit of explanation: the basic idea is to make a dummy
    # metaclass for one level of class instantiation that replaces itself with
    # the actual metaclass.
    class MetaClass(meta):
        """ Indirection for the provided metaclass. """
        def __new__(cls, name, this_bases, d):
            return meta(name, bases, d)
    return type.__new__(MetaClass, 'temporary_class', (), {})


def identity(d):
    """
    The identity function, because functional programmers hate `if` statements.
    """
    return d


class Attribute(object):
    """
    Define a persistent attribute on a Model subclass.

    By default the attribute will use the attribute's name on the Model as the
    key in the serialized dict. If ``struct_name`` is provided, that will be
    used as the dict key.

    ``python_type``, if provided should be a function that takes the serialized
    value and converts it to the type that will be stored on the
    Model instance. This parameter is the usually used with, and is the
    opposite of ``serialized_type``.

    ``serialized_type``, if provided, should be a function that takes the
    value stored on the Model instance and returns a value that should be
    stored in the serialized dict. This parameter is the usually used with, and
    is the opposite of ``python_type``.
    """
    def __init__(
            self,
            struct_name=None,
            python_type=None,
            serialized_type=None,
    ):
        self._struct_name = struct_name
        # Set by metaclass:
        self.attr_name = None
        self.python_type_converter = python_type if python_type else identity
        self.serialized_type_converter = \
            serialized_type if serialized_type else identity

    def _apply_model(self, attr_name, model_class):
        # Currently not storing model_class, but may need for complex
        # multi-attribute serialization/deserialization.
        self.attr_name = attr_name

    def unpack(self, instance, element):
        """
        Unpack the data item, provided as element, and store on the instance.
        """
        setattr(instance, self.attr_name, self.python_type_converter(element))

    def pack(self, instance, d):
        """
        Store the attribute on the provided dictionary, `d`.
        """
        attr_value = getattr(instance, self.attr_name)
        d[self.struct_name] = self.serialized_type_converter(attr_value)

    @property
    def struct_name(self):
        """
        The name of the attribute when it is persisted.

        This is either calculated from the attribute's name on the Model it is
        assigned to, or provided by the constructor's
        ``struct_name`` parameter.
        """
        if self._struct_name is None:
            result = self.attr_name
        else:
            result = self._struct_name
        return result


class Relation(Attribute):
    """
    An Attribute that links to another Model.
    """
    def __init__(self, relation_class, struct_name=None, sequence=False):
        super(Relation, self).__init__(struct_name=struct_name)
        self.relation_class = relation_class
        self.sequence = sequence

    def unpack(self, instance, element):
        """
        Create a new instance of the `relation_class` and deserialize the
        provided element into it.
        """
        if self.sequence:
            unpacked = [
                self.relation_class.deserialize(item) for item in element
            ]
        else:
            unpacked = self.relation_class.deserialize(element)
        setattr(instance, self.attr_name, unpacked)

    def pack(self, instance, d):
        """
        Serialize the provided `instance` and store in the provided dict `d`.
        """
        if self.sequence:
            model_seq = getattr(instance, self.attr_name)
            d[self.struct_name] = [
                model.serialize() for model in model_seq
            ]
        else:
            d[self.struct_name] = getattr(instance, self.attr_name).serialize()


class MetaModel(type):
    """
    A metaclass to complete initialization of Attributes defined on a Model.
    """
    def __init__(cls, name, bases, cls_dict):
        super(MetaModel, cls).__init__(name, bases, cls_dict)

        # Gather and configure all Attributes defined on the Model class:
        model_attributes = []
        for attr_name, attr_value in cls_dict.items():
            if isinstance(attr_value, Attribute):
                attr_value._apply_model(attr_name, cls)

                model_attributes.append(attr_value)
        # Remove the Attributes from the class to avoid accidental fallbacks
        # to the Attribute definition:
        for attr in model_attributes:
            delattr(cls, attr.attr_name)
        # Store the list of Attributes on the class:
        cls._model_attributes = model_attributes


class Model(with_metaclass(MetaModel, object)):
    """
    A parent class that provides the ability to map to and from JSON
    data structures.
    """

    _model_attributes = None

    def __init__(self, *args, **kwargs):
        cls = self.__class__

        if args:
            # Ordering of attributes is not guaranteed, so we can't use
            # positional params:
            raise TypeError("Model does not support positional parameters")

        # Set everything to None:
        for attr in cls._model_attributes:
            setattr(self, attr.attr_name, None)

        # Set named params:
        for attr_name, value in kwargs.items():
            setattr(self, attr_name, value)

    @classmethod
    def deserialize(cls, d):
        """
        Extract the data stored in the dict `d` into this Model instance.
        """
        result = cls()
        for attr in cls._model_attributes:
            attr.unpack(result, d[attr.struct_name])
        return result

    def serialize(self):
        """
        Extract this model's Attributes into a dict.
        """
        cls = self.__class__
        d = {}
        for attr in cls._model_attributes:
            attr.pack(self, d)
        return d
