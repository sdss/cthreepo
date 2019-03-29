# !/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Filename: objects.py
# Project: cthreepo
# Author: Brian Cherinka
# Created: Saturday, 16th March 2019 10:15:16 pm
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2019 Brian Cherinka
# Last Modified: Friday, 29th March 2019 10:04:16 am
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import

import os
import re
import yaml
import pathlib
from marshmallow import Schema, fields, post_load
from cthreepo.core.structs import FuzzyList
from cthreepo.misc import log
import cthreepo.datamodel as dm

p = pathlib.Path('../../../datamodel/')
files = p.glob('**/*.yaml')

#
# examples
#

# with open('../../../datamodel/manga/bintypes.yaml', 'r') as f:
#     e = yaml.load(f)


class ObjectField(fields.Field):
    ''' custom object field '''
    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return ''
        return value.release if hasattr(value, 'release') else value.name if hasattr(value, 'name') else ''

    def _deserialize(self, value, attr, data, **kwargs):
        name = self.default
        data = globals().get(name, None)
        return data[value] if data else value


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

    # define custom str
    def new_str(self):
        name = _get_attr(self, 'name') or _get_attr(self, 'release') or ''
        return name

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


def create_field(data, key=None, required=None):
    ''' creates a marshmallow.fields '''

    # parse the kind of input
    kind = data['kind'].title()
    kind, subkind = parse_kind(kind)
    # get the field
    field = get_field(kind)
    
    # create params
    params = {}
    params['required'] = data.get('required', False) if required is None else required
    if 'default' in data:
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
            attrs[attr] = create_field(values, key=attr)
    else:
        attrs = {}

    class_obj = create_class(data)
    attrs['_class'] = class_obj

    objSchema = type(name + 'Schema', (BaseSchema,), attrs)
    return objSchema

    
def generate_models(data, make_fuzzy=True):
    ''' generate a list of datamodel types '''
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
        data = expand_yaml(data)
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


def validate_datamodel(data):
    ''' Validate the base datamodel schema '''

    assert 'required_keys' in data, 'datamodel must contain a list of valid keys'
    assert 'schema' in data, 'datamodel must have a schema entry'
    keys = data['required_keys']
    for key, value in data['schema'].items():
        itemkeys = value.keys()
        assert set(keys).issubset(set(itemkeys)), (f'datamodel attribute {key} must '
                                                   f'contain the following keys: {",".join(keys)}')


def find_datamodels(path):
    ''' find all datamodel.yaml files up to a given path and merge them '''

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

    validate_datamodel(datamodel)
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


def create_product_schema(data, base=None, required=None):
    ''' create a product schema class '''
    if 'schema' in data:
        attrs = {}
        for attr, values in data['schema'].items():
            check_base(base, attr)
            attrs[attr] = create_field(values, key=attr, required=required)
    else:
        attrs = {}
        
    class_obj = create_product(data)
    attrs['_class'] = class_obj
    
    objSchema = type('ProductSchema', (BaseSchema,), attrs)
    return objSchema


def generate_products(ymlfile, name=None, make_fuzzy=True, base=None):
    ''' generate a list of vdatamodel types '''

    # generate the full datamodel schema
    dmschema = find_datamodels(ymlfile)
    schema = create_product_schema(dmschema, base=base)
    data = read_yaml(ymlfile)
    
    # get the products data
    many = False if name else True
    objects = data.get(name, None) if name else data.values()

    # serialize the object
    models = schema().load(objects, many=many)

    if make_fuzzy and isinstance(models, list):
        models = FuzzyList(models)
    return models


def check_base(base, key):
    ''' retrieve base module level and set an attribute into globals
    TODO this needs replacing; and a better solution
    '''
    import importlib

    if not base:
        return

    base = 'cthreepo.' + base.replace('/', '.')
    try:
        basemod = importlib.import_module(base)
    except ModuleNotFoundError:
        basemod = None
    else:
        keyobj = getattr(basemod, key, None)
        if keyobj:
            globals()[key] = keyobj
        

def parse_value(key, value, data, versions):
    ''' parse a value for versions '''

    if not isinstance(value, str):
        return value

    value = value.replace(' ', '')

    # check if the value has a version in it
    version_patt = r'^(?:{0})'.format('|'.join(versions))
    has_vers = re.search(version_patt, value)
    if not has_vers:
        assert '+=' not in value, f'{value} cannot have a += operator'
        assert '-=' not in value, f'{value} cannot have a -= operator'
        return value

    # check format of string value
    word_patt = r'([+-]=\[?\w+-?,?\w+\]?)+'
    pattern = r'{0}{1}'.format(version_patt, word_patt)
    match = re.search(pattern, value)
    if not match:
        raise ValueError('Syntax does not match the correct syntax: [ver] += XXX -= XXX')
    
    # split the value on +=, -=
    content = re.split(r'(\+=|\-=)', value)
    version, modifiers = content[0], content[1:]
    assert version in versions, f'{versions} not in allowed list of versions'
    
    # get the data for this version
    rel_data = data[version]
    assert key in rel_data, f'{key} not found in this release data'
    
    # get the original value content for the key
    orig_data = rel_data[key].copy()

    # loop over the modifiers by 2
    for mod in modifiers[1::2]:
        idx = modifiers.index(mod)
        islist = re.search(r'\[(.*?)\]', mod)
        # convert the string into a list
        if islist:
            modeval = islist.group(1).split(',')
        else:
            modeval = [mod]

        # modify the original list of values
        if modifiers[idx - 1] == '+=':
            orig_data = list(set(orig_data) | set(modeval))
        elif modifiers[idx - 1] == '-=':
            orig_data = list(set(orig_data) - set(modeval))

    return orig_data


def expand_yaml(data):
    '''expand the yaml with version substitution'''

    # loop over the objects
    for key, value in data.items():
        changelog = value.get('changelog', None)
        versions = value.get('versions', None)
        assert versions is not None, f'Must have a versions key set for object {key}'
        if changelog and isinstance(changelog, dict):
            for ver in versions:
                if ver in changelog:
                    # perform any parameter substitution
                    verdata = changelog[ver]
                    for k, v in verdata.items():
                        new = parse_value(k, v, changelog, versions)
                        changelog[ver][k] = new
                else:
                    # handle a version not in the changelog explicitly; use the defaults
                    defaults = data[key].get('defaults', None)
                    changelog[ver] = defaults

            # remove the defaults keyword after expansion
            __ = data[key].pop('defaults', None)

            # remove any lingering NULL versions
            changelog = {k: v for k, v in changelog.items() if v is not None}
            data[key]['changelog'] = changelog

    return data
