# !/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Filename: objects.py
# Project: cthreepo
# Author: Brian Cherinka
# Created: Saturday, 16th March 2019 10:15:16 pm
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2019 Brian Cherinka
# Last Modified: Friday, 22nd March 2019 3:05:03 pm
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import

import yaml
import pathlib
from marshmallow import Schema, fields, post_load
from cthreepo.core.structs import FuzzyList

p = pathlib.Path('../etc/')
files = p.glob('**/*.yaml')

#
# examples
#

with open('../etc/manga/bintypes.yaml', 'r') as f:
    e = yaml.load(f)


class Bintype(object):

    def __init__(self, name=None, description=None, binned=None, n=None):
        self.name = name
        self.description = description
        self.binned = binned
        self.n = n

    def __repr__(self):
        return f'<Bintype({self.name}, binned={self.binned})>'


class BintypeSchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    binned = fields.Boolean(missing=True, default=True)
    n = fields.Integer()

    @post_load
    def make_bintype(self, data):
        return Bintype(**data)


# Bintype = type(e['schema']['name'], (object,), e['schema'])


with open('../etc/manga/templates.yaml', 'r') as f:
    e = yaml.load(f)


class Template(object):
    
    def __init__(self, name=None, description=None, n=None):
        self.name = name
        self.description = description
        self.n = n

    def __repr__(self):
        return f'<Template({self.name})>'


class TemplateSchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    n = fields.Integer()

    @post_load
    def make_object(self, data):
        return Template(**data)

#
# generic
#


class BaseClass(object):
    def __new__(cls, *args, **kwargs):
        pass


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

    # get the attributes to add to the repr
    added_fields = [a for a, vals in data['attributes'].items() if vals.get('add_to_repr', None)]

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
    return obj


def create_field(data):
    ''' creates a marshmallow.fields '''
    kind = data['kind'].title()
    params = {}
    if hasattr(fields, kind):
        field = fields.__getattribute__(kind)
        params['required'] = data.get('required', False)
        if 'default' in data:
            params['missing'] = data.get('default', None)
            params['default'] = data.get('default', None)
        return field(**params)


class BaseSchema(Schema):
    ''' Base class for schema validation '''
    class Meta:
        ordered = True

    @post_load
    def make_object(self, data):
        ''' this function serializes a schema to a class object '''
        return self._class(**data)


def create_schema(data):
    ''' creates a new class for schema validation '''
    name = data['name']
    if 'attributes' in data:
        attrs = {}
        for attr, values in data['attributes'].items():
            attrs[attr] = create_field(values)
    else:
        attrs = {}

    class_obj = create_class(data)
    attrs['_class'] = class_obj

    objSchema = type(name + 'Schema', (BaseSchema,), attrs)
    return objSchema

    
def generate_models(data, make_fuzzy=True):
    ''' generate a list of vdatamodel types '''
    schema = create_schema(data['schema'])
    models = schema().load(data['objects'], many=True)
    if make_fuzzy:
        models = FuzzyList(models)
    return models


def read_yaml(ymlfile):
    ''' opens and reads a yaml datamodel file '''
    with open(ymlfile, 'r') as f:
        data = yaml.load(f)

    if 'datamodel' not in ymlfile.parts and 'products' not in ymlfile.parts:
        assert 'schema' in data, 'datamodel file must contain a schema section'
        assert 'objects' in data, 'datamodel file must contain an objects section'

    return data


def merge_datamodels(user, default):
    """Merges datamodel files 
    alternative - try hiyapyco package or yamlload for merging purposes
    """

    if isinstance(user, dict) and isinstance(default, dict):
        for kk, vv in default.items():
            if kk not in user:
                user[kk] = vv
            else:
                user[kk] = merge_datamodels(user[kk], vv)
    elif isinstance(user, list) and isinstance(default, list):
        for item in default:
            if item not in user:
                user.append(item)

    return user
