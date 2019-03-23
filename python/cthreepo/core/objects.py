# !/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Filename: objects.py
# Project: cthreepo
# Author: Brian Cherinka
# Created: Saturday, 16th March 2019 10:15:16 pm
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2019 Brian Cherinka
# Last Modified: Saturday, 23rd March 2019 5:22:22 pm
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import

import os
import re
import yaml
import pathlib
from marshmallow import Schema, fields, post_load
from cthreepo.core.structs import FuzzyList
from cthreepo.misc import log

p = pathlib.Path('../../../datamodel/')
files = p.glob('**/*.yaml')

#
# examples
#

# with open('../../../datamodel/manga/bintypes.yaml', 'r') as f:
#     e = yaml.load(f)


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


# with open('../../../datamodel/manga/templates.yaml', 'r') as f:
#     e = yaml.load(f)


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
    if 'attributes' in data:
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


def get_field(value):
    ''' Get a Marshmallow Fields type '''
    if hasattr(fields, value):
        field = fields.__getattribute__(value)
        return field
    else:
        raise ValueError(f'Marshmallow Fields does not have {value}')


def create_field(data):
    ''' creates a marshmallow.fields '''

    # parse the kind of input
    kind = data['kind'].title()
    kind, subkind = parse_kind(kind)
    # get the field
    field = get_field(kind)
    
    # create params
    params = {}
    params['required'] = data.get('required', False)
    if 'default' in data:
        params['missing'] = data.get('default', None)
        params['default'] = data.get('default', None)

    # create any args for sub-fields
    args = []
    if subkind:
        skinds = subkind.split(',')
        subfields = [get_field(i.title()) for i in skinds]
        # differentiate args for lists and tuples 
        if kind == 'List':
            assert len(subfields) == 1, 'List can only accept one subfield type.'
            args.extend(subfields)
        elif kind == 'Tuple':
            args.append(subfields)

    return field(*args, **params)


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

    if isinstance(ymlfile, str):
        ymlfile = pathlib.Path(ymlfile)

    with open(ymlfile, 'r') as f:
        data = yaml.load(f)

    if ymlfile.stem not in ['datamodel', 'products']:
        assert 'schema' in data, 'datamodel file must contain a schema section'
        assert 'objects' in data, 'datamodel file must contain an objects section'

    # validate the products
    if ymlfile.stem == 'products':
        dm = find_datamodels(ymlfile)
        for prodname, content in data.items():
            prodkeys = set(content.keys())
            dmkeys = set(dm['schema'].keys())
            notallowed = ', '.join(prodkeys - dmkeys)
            assert prodkeys.issubset(dmkeys), f'{prodname} contains unallowed keys ({notallowed}) in datamodel schema' 

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


def find_datamodels(path):
    ''' find all datamodel.yaml files up to a given path '''

    path = path.resolve()
    path = path.parent if path.is_file() else path

    datamodel_dir = os.environ['CTHREEPO_DIR'] / pathlib.Path('datamodel')
    datamodel = {}
    for dirs, subdirs, files in os.walk(datamodel_dir):
        if 'datamodel.yaml' in files and dirs in path.as_posix():
            ymlfile = (pathlib.Path(dirs) / 'datamodel.yaml')
            ymldata = read_yaml(ymlfile)
            datamodel = merge_datamodels(ymldata, datamodel)
        if dirs == path.as_posix():
            break
    return datamodel
    
####
## testing here


class Product(object):
    def __init__(self, name=None, description=None, datatype=None, sdss_access=None,
                 example=None, versions=None):
        self.name = name
        self.description = description
        self.datatype = datatype
        self.sdss_access = sdss_access
        self.example = example
        self.versions = versions

    def __repr__(self):
        return f'<Product({self.name})>'


class ProductSchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    datatype = fields.Str(required=True)
    sdss_access = fields.Str(required=True)
    example = fields.Str(required=True)
    versions = fields.List(fields.Str, required=True)

    @post_load
    def make_object(self, data):
        return Product(**data)


def create_product(data):
    ''' create a product class '''
    # define custom repr
    def new_rep(self):
        reprstr = f'<Product({self._repr_fields})>'
        return reprstr

    # get the attributes to add to the repr
    added_fields = [a for a, vals in data['schema'].items() if vals.get('add_to_repr', None)]

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
    obj = type("Product", (object,), {})
    obj.__init__ = new_init
    obj.__repr__ = new_rep
    return obj


def create_product_schema(data):
    ''' create a product schema class '''
    if 'schema' in data:
        attrs = {}
        for attr, values in data['schema'].items():
            attrs[attr] = create_field(values)
    else:
        attrs = {}
        
    class_obj = create_product(data)
    attrs['_class'] = class_obj
    
    objSchema = type('ProductSchema', (BaseSchema,), attrs)
    return objSchema


def generate_products(ymlfile, name=None, make_fuzzy=True):
    ''' generate a list of vdatamodel types '''

    # generate the full datamodel schema
    dmschema = find_datamodels(ymlfile)
    schema = create_product_schema(dmschema)
    data = read_yaml(ymlfile)
    
    # get the products data 
    many = False if name else True
    objects = data.get(name, None) if name else data 

    # serialize the object     
    models = schema().load(objects, many=many)

    if make_fuzzy and isinstance(models, list):
        models = FuzzyList(models)
    return models

