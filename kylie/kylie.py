# -*- coding: utf-8 -*-

"""Internal implementation of the `kylie` package.

You probably want to use the `kylie` package directly, instead of this.
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

        """Indirection for the provided metaclass."""

        def __new__(cls, name, this_bases, d):
            return meta(name, bases, d)

    return type.__new__(MetaClass, 'temporary_class', (), {})


def identity(d):
    """The identity function.

    Because functional programmers hate `if` statements.
    """
    return d


class Attribute(object):

    """Used to define a persistent attribute on a Model subclass.

    Args:
        struct_name (str, optional): The dict key to be used when serializing
            this attribute. Defaults to the name the attribute's name on its
            host ``Model``.
        python_type (function, optional): A function that takes the serialized
            value and converts it to the type that will be stored on the
            Model instance. This parameter is the usually used with, and is the
            opposite of ``serialized_type``.

        serialized_type (function, optional): A function that takes the
            value stored on the Model instance and returns the value that
            should be stored in the serialized dict. This parameter is the
            usually used with, and is the opposite of ``python_type``.
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

    def unpack(self, instance, element):
        """Unpack the data item and store on the instance."""
        setattr(instance, self.attr_name, self.python_type_converter(element))

    def pack(self, instance, d):
        """Store the attribute on the provided dictionary, `d`."""
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

    """An Attribute that embeds to another Model.

    Args:
        relation_class (Model): The Model subclass that will be
            deserialized into this attribute.
        struct_name (str, optional): The name of the key that will be used
            when serializing this attribute into a dict. Defaults to the
            name of the attribute on the host Model.
        sequence (bool, optional): Indicates that this attribute will store
            a sequence of ``relation_class``, which will be serialized to a
            list.
    """

    def __init__(self, relation_class, struct_name=None, sequence=False):
        super(Relation, self).__init__(struct_name=struct_name)
        # TODO: Rename relation_class and class_chooser
        self.class_chooser = relation_class
        self.sequence = sequence

    def unpack(self, instance, element):
        """Unpack an embedded, serialized Model.

        Create a new instance of the `relation_class` and deserialize the
        provided element into it.
        """
        # TODO: Rename element
        if self.sequence:
            unpacked = [
                self.class_chooser.deserialize(item) for item in element
            ]
        else:
            unpacked = self.class_chooser.deserialize(element)
        setattr(instance, self.attr_name, unpacked)

    def pack(self, instance, d):
        """Serialize the provided `instance` into the provided dict `d`."""
        if self.sequence:
            model_seq = getattr(instance, self.attr_name)
            d[self.struct_name] = [
                model.serialize() for model in model_seq
            ]
        else:
            d[self.struct_name] = getattr(instance, self.attr_name).serialize()


class BaseModelSwitcher(object):
    def choose_model(self, element):
        """
        Return a Model class suitable for deserializing the given `element`.
        Params:
            element: A data item.

        Return: An object (or class, usually a Model) with a deserialize method
            that can deserialize the given `element`
        """

    def deserialize(self, element):
        return self.choose_model(element).deserialize(element)


class DeserializationError(Exception):
    pass


class AttributeSwitcher(BaseModelSwitcher):
    def __init__(self, type_map, attribute_name='__type__'):
        self.type_map = type_map
        self.attribute_name = attribute_name

    def choose_model(self, element):
        if self.attribute_name in element:
            return element.get(self.attribute_name)
        else:
            raise DeserializationError("Missing {attr_name} key in ")


class MetaModel(type):

    """A metaclass to complete initialization of Attributes defined on a Model.

    On initialization, MetaModel iterates through any ``Attribute``s assigned
    to the Model class and sets their ``attr_name`` attribute, so they know
    how they are defined on the Model. This information is required for
    serialization and deserialization.
    """

    def __init__(cls, name, bases, cls_dict):
        super(MetaModel, cls).__init__(name, bases, cls_dict)

        # Gather and configure all Attributes defined on the Model class:
        model_attributes = []
        for attr_name, attr_instance in cls_dict.items():
            if isinstance(attr_instance, Attribute):
                attr_instance.attr_name = attr_name

                model_attributes.append(attr_instance)
        # Remove the Attributes from the class to avoid accidental fallbacks
        # to the Attribute definition:
        for attr in model_attributes:
            delattr(cls, attr.attr_name)
        # Store the list of Attributes on the class:
        cls._model_attributes = model_attributes


class Model(with_metaclass(MetaModel, object)):

    """A parent class that can map to and from JSON-style data structures."""

    _model_attributes = None

    def __init__(self, *args, **kwargs):
        if args:
            # Ordering of attributes is not guaranteed, so we can't use
            # positional params:
            raise TypeError("Model does not support positional parameters")

        # Set everything to None:
        for attr in self._model_attributes:
            setattr(self, attr.attr_name, None)

        # Set named params:
        for attr_name, value in kwargs.items():
            setattr(self, attr_name, value)

    @classmethod
    def deserialize(cls, d):
        """Extract the data from a dict into this Model instance."""
        result = cls()
        for attr in cls._model_attributes:
            attr.unpack(result, d[attr.struct_name])
        return result

    def serialize(self):
        """Extract this model's Attributes into a dict."""
        d = {}
        for attr in self._model_attributes:
            attr.pack(self, d)

        if hasattr(self, 'post_serialize'):
            self.post_serialize(d)

        return d
