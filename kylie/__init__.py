# -*- coding: utf-8 -*-

"""kylie - A module for mapping between JSON and Python classes."""

from .kylie import (
    Attribute,
    BaseModelChoice,
    DeserializationError,
    MappedModelChoice,
    Model,
    Relation,
)

__all__ = (
    'Attribute',
    'BaseModelChoice',
    'DeserializationError',
    'MappedModelChoice',
    'Model',
    'Relation',
)

__author__ = 'Mark Smith'
__email__ = 'mark.smith@practicalpoetry.co.uk'
__version__ = '0.3.0'
