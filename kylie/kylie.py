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
        # pylint: disable=unused-argument
        def __new__(cls, name, this_bases, attribs):
            return meta(name, bases, attribs)

    return type.__new__(MetaClass, 'temporary_class', (), {})


def identity(value):
    """The identity function.

    Because functional programmers hate `if` statements.
    """
    return value


class DeserializationError(Exception):

    """Error indicating deserialization failed."""

    pass


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
            optional=False,
    ):
        self._struct_name = struct_name
        # Set by metaclass:
        self.attr_name = None
        self.python_type_converter = python_type if python_type else identity
        self.serialized_type_converter = \
            serialized_type if serialized_type else identity
        self.optional = optional

    def unpack(self, instance, value):
        """Unpack the data item and store on the instance."""
        setattr(instance, self.attr_name, self.python_type_converter(value))

    def pack(self, instance, record):
        """Store the attribute on the provided dictionary, `record`."""
        attr_value = getattr(instance, self.attr_name)
        record[self.struct_name] = self.serialized_type_converter(attr_value)

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

    Params:
        deserializable (Model, BaseModelChoice): The Model or BaseModelChoice
            subclass that will be deserialized into this attribute.
        struct_name (str, optional): The name of the key that will be used
            when serializing this attribute into a dict. Defaults to the
            name of the attribute on the host Model.
        sequence (bool, optional): Indicates that this attribute will store
            a sequence of ``deserializables``, which will be serialized to a
            list.
    """

    def __init__(self, deserializable, struct_name=None, sequence=False, optional=False):
        super(Relation, self).__init__(struct_name=struct_name, optional=optional)
        self.deserializable = deserializable
        self.sequence = sequence

    def unpack(self, instance, value):
        """Unpack an embedded, serialized Model.

        Create a new instance of the `relation_class` and deserialize the
        provided value into it.
        """
        if self.sequence:
            unpacked = [
                self.deserializable.deserialize(item) for item in value
            ]
        else:
            unpacked = self.deserializable.deserialize(value)
        setattr(instance, self.attr_name, unpacked)

    def pack(self, instance, record):
        """Serialize the provided `instance` into the provided dict `record`."""
        if self.sequence:
            model_seq = getattr(instance, self.attr_name)
            serialized = [
                model.serialize() for model in model_seq
            ]
        else:
            serialized = getattr(instance, self.attr_name).serialize()
        record[self.struct_name] = serialized


class BaseModelChoice(object):

    """
    Abstract class for providing Model class choice on deserialization.

    If records contain an attribute that specify the class of the serialized
    object, then you should probably use ``MappedModelChoice`` instead.
    If your logic is more complex then subclass ``BaseModelChoice`` and
    and implement ``choose_model``.

    Instances of BaseModelChoice can be passed to the ``Attribute`` constructor
    in place of a Model class.
    """

    def choose_model(self, value):
        """
        Return a Model class suitable for deserializing the given `value`.

        Params:
            value: A data item.

        Return: An object (or class, usually a Model) with a deserialize method
            that can deserialize the given `value`
        """
        raise NotImplementedError('Concrete subclasses of BaseModelChoice must'
                                  ' implement choose_model.')

    def deserialize(self, value):
        """Deserialize ``value`` into a dynamically chosen ``Model``.

        The chosen Model is specified by the abstract method ``choose_model``.
        """
        return self.choose_model(value).deserialize(value)


class MappedModelChoice(BaseModelChoice):
    def __init__(self, type_map, attribute_name='__type__'):
        """
        Used for Relation attributes which may map to one of a set of Models.

        Params:
            type_map (dict): A dictionary keyed with possible values of the
                special attribute, stored against the associated Model class.
            attribute_name (str, optional): The name of the special attribute
                that is used to determine the Model that should be chosen for
                deserialization.
        """
        self.type_map = type_map
        self.attribute_name = attribute_name

    def choose_model(self, value):
        """Choose a ``Model`` for deserialization.

        This implementation chooses a Model based on the value of the
        attribute specified by the ``attribute_name`` this
        ``MappedModelChoice`` was instantiated with. The value of this
        attribute is looked up in this instance's ``type_map`` and the
        resulting ``Model`` class is returned.

        If the value of the special attribute is not found in ``type_map``,
        a ``DeserializationError`` is raised.
        """
        if self.attribute_name in value:
            return self.type_map[value.get(self.attribute_name)]
        else:
            raise DeserializationError(
                "Missing {attr_name} key in {record}".format(
                    attr_name=self.attribute_name,
                    record=value,
                ))


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
    def deserialize(cls, record):
        """Extract the data from a dict into this Model instance."""
        result = cls()
        for attr in cls._model_attributes:
            if attr.optional:
                attr.unpack(result, record.get(attr.struct_name, None))
            else:
                attr.unpack(result, record[attr.struct_name])
        return result

    def serialize(self):
        """Extract this model's Attributes into a dict."""
        record = {}
        for attr in self._model_attributes:
            attr.pack(self, record)

        if hasattr(self, 'post_serialize'):
            self.post_serialize(record)

        return record
