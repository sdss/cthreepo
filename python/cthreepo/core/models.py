# !/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Filename: models.py
# Project: core
# Author: Brian Cherinka
# Created: Friday, 12th April 2019 10:17:04 am
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2019 Brian Cherinka
# Last Modified: Tuesday, 21st May 2019 6:00:37 pm
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import
import re
import six
from marshmallow import Schema, fields, post_load
from cthreepo.core.structs import FuzzyList


# core classes


class BaseClass(object):
    def __new__(cls, *args, **kwargs):
        pass


class BaseSchema(Schema):
    ''' Base class to use for all new Schema objects '''
    _class = None

    class Meta:
        ordered = True

    @post_load
    def make_object(self, data):
        ''' this function deserializes a schema to a class object '''
        return self._class(**data)


class ObjectField(fields.Field):
    ''' custom marshmallow object field

    This is a custom marshmallow Field class used to indicate that an attribute
    should be represented by a custom model object type, rather than a string or integer. It
    contains special methods for custom serialization and deserialization of model datatypes.
    For example, the yaml string representation 'LOG' for a log-linear wavelength will get
    deserialized into an instance Wavelength('LOG'). Custom fields are described at
    https://marshmallow.readthedocs.io/en/3.0/custom_fields.html.
    
    '''

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return ''
        return value.release if hasattr(value, 'release') else value.name if hasattr(value, 'name') else ''

    def _deserialize(self, value, attr, data, **kwargs):
        name = self.default
        assert isinstance(value, six.string_types), f'{value} must be a string'
        data = self.models.get(name, None)
        return data[value] if data and value in data else value

# main/helper functions


def _get_attr(obj, name):
    ''' Get an attribute from a class object
    
    Attempts to retrieve an attribute from a class object
    
    Parameters:
        obj (object):
            A class object to access
        name (str):
            The attribute name to access
    Returns:
        a class attribute
    '''
    if hasattr(obj, name):
        return obj.__getattribute__(name)
    else:
        return None


def create_class(data, mixin=None):
    ''' creates a new datamodel object class

    Constructs a Python class object based on a model "schema" dictionary.
    Converts a model yaml file, 'versions.yaml' into a Python Version class object,
    which is used for instantiating the designated "objects" in the yaml section.

    Parameters:
        data (dict):
            The schema dictonary section of a yaml file
        mixin (object):
            A custom model class to mixin with base model

    Returns:
        A new Python class object
    '''

    # define custom repr
    def new_rep(self):
        reprstr = f'<{data["name"]}({self._repr_fields})>'
        return reprstr

    # define custom str
    def new_str(self):
        name = _get_attr(self, 'name') or _get_attr(self, 'release') or ''
        return name

    # get the attributes to add to the repr
    if 'attributes' in data:
        added_fields = [a for a, vals in data['attributes'].items()
                        if vals.get('add_to_repr', None)]

    # define a new init
    def new_init(self, **kwargs):
        repr_fields = ''
        # loop for attributes
        for key, value in list(kwargs.items()):
            self.__setattr__(key, value)
            # create a repr field string
            if key in added_fields:
                repr_fields += f', {key}={value}'
        # create a string of the repr fields
        name = _get_attr(self, 'name') or _get_attr(self, 'release') or ''
        self._repr_fields = f'{name}' + repr_fields

    # create the new class and add the new methods
    bases = (mixin, object,) if mixin else (object,)
    obj = type(data['name'], bases, {})
    obj.__init__ = new_init
    obj.__repr__ = new_rep
    obj.__str__ = new_str
    return obj


def parse_kind(value):
    ''' parse the kind value into a kind and subkind

    Parses the schema "kind" attribute into a kind and subkind if
    kind contain paranetheses, i.e. kind(subkind).  For example,
    list(objects) return kind=list, subkind=objects.
    
    Parameters:
        value (str):
            The type of field
    
    Returns:
        A tuple of the field type and any sub-type
    '''
    subkind = re.search(r'\((.+?)\)', value)
    if subkind:
        kind = value.split('(', 1)[0]
        subkind = subkind.group(1)
    else:
        kind = value
        # set default list or tuple subfield to string
        if kind.lower() == 'list':
            subkind = 'string'
        elif kind.lower() == 'tuple':
            subkind = 'string'

    return kind, subkind


def get_field(value, key=None):
    ''' Get a Marshmallow Fields type
    
    Using the model schema attribute "kind" parameter, determines the
    appropriate marshmallow field type.  If the value is "Objects"
    then it uses a custom ObjectField definition.     

    Parameters:
        value (str):
            The kind of field to retrieve, e.g. string
        key (str):
            The name of the attribute for the field
            
    Returns:
        a marshmallow field class
    '''
    if hasattr(fields, value):
        field = fields.__getattribute__(value)
        return field
    elif value == 'Objects':
        return ObjectField(key)
    else:
        raise ValueError(f'Marshmallow Fields does not have {value}')


def create_field(data, key=None, required=None, nodefault=None):
    ''' creates a marshmallow.fields object
    
    Parameters:
        data (dict):
            A values dictionary for a given model attribute
        key (str):
            The name of the attribute
        required (bool):
            If True, sets the field as a required one. Default is False.
        nodefault (bool):
            If True, turns off any defaults specified for fields.  Default is False.

    Returns:
        A marshmallow field instance to attach to a schema
    '''
    # parse the kind of input
    kind = data['kind'].title()
    kind, subkind = parse_kind(kind)
    # get the marshmallow field
    field = get_field(kind)

    # create a parameters dictionary to pass into the fields object
    params = {}
    params['required'] = data.get('required', False) if required is None else required
    if 'default' in data and not nodefault:
        params['missing'] = data.get('default', None)
        params['default'] = data.get('default', None)

    # set key to use the model indicated if use_model is set
    key = data['use_model'] if 'use_model' in data else key

    # create any arguments for sub-fields
    args = []
    if subkind:
        skinds = subkind.split(',')
        subfields = [get_field(i.title(), key=key) for i in skinds]
        # differentiate args for lists and tuples
        if kind == 'List':
            assert len(subfields) == 1, 'List can only accept one subfield type.'
            args.extend(subfields)
        elif kind == 'Tuple':
            args.append(subfields)

    # instantiate the fields object with the relevant args and parameters
    return field(*args, **params)


def create_schema(data, mixin=None):
    ''' creates a new class for schema validation
    
    Constructs a marshmallow schema class object used to validate
    the creation of new Python objects for this class.  Takes a
    model "schema" dictionary and builds new Python classes to represent
    the model Object and an Object Schema for purposes of validation.
    See https://marshmallow.readthedocs.io/en/3.0/quickstart.html for a guide on
    deserializing data using marshmallow schema validation.

    Parameters:
        data (dict):
            The schema dictonary section of a yaml file
        mixin (object):
            A custom model class to mixin with base model
    
    Returns:
        A marshmallow schema class object
    '''
    # create a dictionary of class attributes from the schema
    name = data['name']
    if 'attributes' in data:
        attrs = {}
        # create marshmallow schema fields for each attribute
        for attr, values in data['attributes'].items():
            attrs[attr] = create_field(values, key=attr)
    else:
        attrs = {}

    # create the base object class
    class_obj = create_class(data, mixin=mixin)

    # add the object class to the schema attributes to allow
    # for object deserialization from yaml representation.  See BaseSchema for use.
    attrs['_class'] = class_obj
    # create the new schema class object
    objSchema = type(name + 'Schema', (BaseSchema,), attrs)

    # add the schema class instance to the object class for accessibility
    class_obj._schema = objSchema()
    return objSchema


def generate_models(data, make_fuzzy=True, mixin=None):
    ''' Generate a list of datamodel types
    
    Converts a models yaml file, e.g. manga/versions.yaml, into a list of Python instances.
    A model Schema class is created using the "schema" section of the yaml file.  The schema
    class is used to validate and instantiate the list of objects defined in the "objects"
    section.
    
    Parameters:
        data (dict):
            A yaml loaded data structure
        make_fuzzy (bool):
            If True, returns a Fuzzy list of models
        mixin (object):
            A custom model class to mixin with base model
    Returns:
        A list of instantiated models
    '''

    # create the schema class object
    schema = create_schema(data['schema'], mixin=mixin)

    # validate and deserialize the model data in Python objects
    models = schema().load(data['objects'], many=True)

    # optionally make the model list fuzzy
    if make_fuzzy:
        models = FuzzyList(models)
    return models

