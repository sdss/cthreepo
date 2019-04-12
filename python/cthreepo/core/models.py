# !/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Filename: models.py
# Project: core
# Author: Brian Cherinka
# Created: Friday, 12th April 2019 10:17:04 am
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2019 Brian Cherinka
# Last Modified: Friday, 12th April 2019 10:30:33 am
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
    ''' Base class for schema validation '''
    _class = None

    class Meta:
        ordered = True

    @post_load
    def make_object(self, data):
        ''' this function deserializes a schema to a class object '''
        return self._class(**data)


class ObjectField(fields.Field):
    ''' custom object field '''

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
    ''' Get an attribute from a class object '''
    if hasattr(obj, name):
        return obj.__getattribute__(name)
    else:
        return None


def create_class(data):
    ''' creates a new datamodel object class '''

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
    obj = type(data['name'], (object,), {})
    obj.__init__ = new_init
    obj.__repr__ = new_rep
    obj.__str__ = new_str
    return obj


def parse_kind(value):
    ''' parse the kind value '''
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
    ''' Get a Marshmallow Fields type '''
    if hasattr(fields, value):
        field = fields.__getattribute__(value)
        return field
    elif value == 'Objects':
        return ObjectField(key)
    else:
        raise ValueError(f'Marshmallow Fields does not have {value}')


def create_field(data, key=None, required=None, nodefault=None):
    ''' creates a marshmallow.fields '''

    # parse the kind of input
    kind = data['kind'].title()
    kind, subkind = parse_kind(kind)
    # get the field
    field = get_field(kind)

    # create params
    params = {}
    params['required'] = data.get('required', False) if required is None else required
    if 'default' in data and not nodefault:
        params['missing'] = data.get('default', None)
        params['default'] = data.get('default', None)

    # create any args for sub-fields
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

    return field(*args, **params)


def create_schema(data):
    ''' creates a new class for schema validation '''
    name = data['name']
    if 'attributes' in data:
        attrs = {}
        for attr, values in data['attributes'].items():
            attrs[attr] = create_field(values, key=attr)
    else:
        attrs = {}

    class_obj = create_class(data)
    attrs['_class'] = class_obj

    objSchema = type(name + 'Schema', (BaseSchema,), attrs)
    class_obj._schema = objSchema()
    return objSchema


def generate_models(data, make_fuzzy=True):
    ''' generate a list of datamodel types '''
    schema = create_schema(data['schema'])
    models = schema().load(data['objects'], many=True)
    if make_fuzzy:
        models = FuzzyList(models)
    return models

