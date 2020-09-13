# !/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Filename: products.py
# Project: core
# Author: Brian Cherinka
# Created: Friday, 12th April 2019 10:17:11 am
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2019 Brian Cherinka
# Last Modified: Wednesday, 29th May 2019 10:53:39 am
# Modified By: Brian Cherinka

from __future__ import print_function, division, absolute_import

import re
import six
import copy

from marshmallow import Schema, fields, validate
from cthreepo.core.fits import Fits, BaseObject, Catalog
from cthreepo.io.general import compute_changelog
from cthreepo.io.yaml import read_yaml, expand_yaml
from cthreepo.io.datamodel import find_datamodels
from cthreepo.core.models import BaseSchema, create_field, _get_attr, ObjectField
from cthreepo import log
from fuzzy_types.fuzzy import FuzzyList

# core classes


class ObjectList(FuzzyList):
    def mapper(self, item):
        return str(item.version).lower()


class ProductList(FuzzyList):
    def mapper(self, item):
        return str(item.name.lower())

    @property
    def choices(self):
        return [self.mapper(item) for item in self]


class BaseProduct(object):
    _changes = None
    _expanded = None

    def expand_product(self):

        if self._expanded is not None:
            return self._expanded

        files = []
        self._base_attrs = set(self._schema.fields.keys()) - {'changelog', 'versions'}
        example = getattr(self, 'example', None)
        example_ver = _find_in_example(example, self.versions) if example else None
        for version in self.versions:
            inst = self._create_datatype(version, example_ver=example_ver)
            files.append(inst)
        return ObjectList(files)

    def compute_changelog(self, versions=None, refresh=None):

        # force a refresh
        if refresh:
            self._changes = None

        if not self._changes:
            # get expanded products
            if not self._expanded:
                self._expanded = self.expand_product()

            # limit to only the specified versions
            if versions:
                assert all([i in self._expanded for i in versions]), 'All versions must be available in the product list'
                verlist = [i for i in self._expanded if str(i.version) in versions]
            else:
                verlist = self._expanded

            # only get changes for files that exist
            exists = [i for i in verlist if i.file_exists]
            rev_list = list(reversed(exists))
            if len(exists) != len(verlist):
                log.warning('One or more product files do not exist. Changelog will be incomplete')

            self._changes = compute_changelog(rev_list, change=self.datatype)
        return self._changes

    def _create_datatype(self, version, example_ver=None):
        ''' create a datatype object '''

        # update the attributes dictionary
        attrs = {a: getattr(self, a, None) for a in self._base_attrs if hasattr(self, a)}
        attrs.update({'version': version, '_parent': self})
        if hasattr(self, 'changelog') and str(version) in self.changelog:
            attrs.update(self.changelog[str(version)])

        # need to assert version is a string or class instance; does not work yet
        assert isinstance(version, (six.string_types, object)
                         ), 'version can only be a string or an instance object'
        example = attrs.pop('example', None)
        if example:
            if not example_ver:
                example_ver = _find_in_example(example, self.versions)
            example = _replace_version(example, example_ver, version)

        # expansion scenarios - attributes needed
        # versions + example
        # versions + path_name + example
        # versions + path_name + path_kwargs

        # handle some keywords
        attrs['path_name'] = attrs.get('path_name', None)
        attrs['product'] = self.name
        attrs['parent'] = _update_parent(self, attrs)

        # generate the datatype
        # TODO - clean this up
        datatype = attrs.pop('datatype')
        if datatype == 'fits':
            if example and not attrs['path_name']:
                inst = Fits.from_example(example, **attrs)
            elif attrs['path_name']:
                # assert example or 'path_kwargs' in attrs, ('Must have an example or path_kwargs set'
                #                                            ' to expand products using path_name')
                if not example and 'path_kwargs' not in attrs:
                    log.warning('No example path or path_kwargs found in product yaml definition. '
                                'Cannot expand Fits product. Defaulting to base Object.')
                    inst = BaseObject(product=self.name, version=version)
                    return inst
                name = attrs.pop('path_name')
                inst = Fits.from_path(name, example=example, **attrs)
            else:
                log.warning('No example path or path_kwargs found in product yaml definition. '
                            'Cannot expand Fits product. Defaulting to base Object.')
                inst = BaseObject(product=self.name, version=version)
        elif datatype == 'catalog':
            if example and not attrs['path_name']:
                inst = Catalog.from_example(example, **attrs)
            elif attrs['path_name']:
                # assert example or 'path_kwargs' in attrs, ('Must have an example or path_kwargs set'
                #                                            ' to expand products using path_name')
                if not example and 'path_kwargs' not in attrs:
                    log.warning('No example path or path_kwargs found in product yaml definition. '
                                'Cannot expand Fits product. Defaulting to base Object.')
                    inst = BaseObject(product=self.name, version=version)
                    return inst
                name = attrs.pop('path_name')
                inst = Catalog.from_path(name, example=example, **attrs)
            else:
                log.warning('No example path or path_kwargs found in product yaml definition. '
                            'Cannot expand Fits product. Defaulting to base Object.')
                inst = BaseObject(product=self.name, version=version)
        else:
            inst = BaseObject(product=self.name, version=version)

        return inst


# main/helper functions
def _update_parent(parent, attrs):
    ''' copy the parent and update any attributes '''
    new_parent = copy.deepcopy(parent)
    for key, value in attrs.items():
        #if hasattr(new_parent, key):
        setattr(new_parent, key, value)
    return new_parent


def _find_version(example, version):
    ''' find a version value in an example '''

    # need to assert version is a string or class instance; does not work yet
    assert isinstance(version, (six.string_types, object)
                      ), 'version can only be a string or an instance object'

    # version is a string
    if isinstance(version, six.string_types):
        values = [version]
    else:
        # version is a class instance; dump the schema and grab values
        values = version._schema.dump(version).values()

    # only use unique values
    values = list(set(values))
    # perform regex search on example string
    joined_vals = '|'.join(i for i in values if i)
    found_vals = re.findall(joined_vals, example)

    # if not found_vals:
    #     raise ValueError('No version found.  Change this to warning.  Using given example file')

    # convert to a list of tuples
    #found_vals = list(tuple(found_vals))
    return found_vals


def _find_in_example(example, versions):
    ''' find a version tag within an example file string '''

    # for a list of versions that is a string
    vers = [v for v in versions if _find_version(example, v)]
    vers = list(set(vers))

    if len(vers) > 1:
        # more than two versions found
        ver = vers[0]
    elif vers:
        ver = vers[0]
    else:
        ver = None
        raise ValueError('No version found.  Using given example file')
    return ver


def _replace_version(example, oldver, newver):
    ''' replace the old version with the new in example '''

    if isinstance(oldver, six.string_types):
        assert isinstance(newver, six.string_types), 'newver must also be a string'
        example = example.replace(oldver, newver)
    else:
        assert type(oldver) == type(newver), 'version classes must be of same type'
        odict = oldver._schema.dump(oldver)
        ndict = newver._schema.dump(newver)
        vers = list(zip(odict.values(), ndict.values()))
        for ver in vers:
            if all(ver):
                oldv, newv = ver
                example = example.replace(oldv, newv)
    return example


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
        # set the docstring
        self.__doc__ = (self.short + '\n\n' + self.description).replace(' \n', '\n')

    # create the new class and add the new methods
    obj = type("Product", (BaseProduct,), {})
    obj.__init__ = new_init
    obj.__repr__ = new_rep
    return obj


def get_product_attrs(data, required=None, nodefault=None):
    if 'schema' in data:
        attrs = {}
        for attr, values in data['schema'].items():
            attrs[attr] = create_field(values, key=attr, required=required, nodefault=nodefault)
    else:
        attrs = {}
    return attrs


def create_product_schema(data, required=None, models=None):
    ''' create a product schema class '''

    # get the attributes
    attrs = get_product_attrs(data, required=required)

    # create the product class
    class_obj = create_product(data)
    attrs['_class'] = class_obj

    # add the datamodel models
    ObjectField.models = models

    # create the changelog schema and modify the changelog attribute
    if 'changelog' in attrs:
        clattrs = get_product_attrs(data, required=False, nodefault=True)
        __ = clattrs.pop('changelog')
        cl = type('ChangeLogSchema', (Schema,), clattrs)
        versions = get_versions(models, data['schema'])
        if not versions:
            clkey = fields.String
        else:
            clkey = fields.String(validate=validate.OneOf(versions))
        attrs['changelog'] = fields.Dict(keys=clkey, values=fields.Nested(cl))

    objSchema = type('ProductSchema', (BaseSchema,), attrs)
    class_obj._schema = objSchema()
    return objSchema


def get_versions(models, schema):
    ''' Get a list of versions from a models schema '''
    if 'versions' in models:
        versions = [str(v) for v in models.versions]
    elif 'versions' in schema:
        # this pulls the versions datamodel attribute dictionary; is this what we want?
        #versions = schema['versions']
        return None
    else:
        return None
    return versions


def validate_products(data, schema):
    ''' validate the products definition against the datamodel schema '''
    data = expand_yaml(data)
    for prodname, content in data.items():
        prodkeys = set(content.keys())
        dmkeys = set(schema['schema'].keys())
        notallowed = ', '.join(prodkeys - dmkeys)
        assert prodkeys.issubset(
            dmkeys), f'product "{prodname}" contains unallowed keys ({notallowed}) in datamodel schema'
    return data


def generate_products(ymlfile, name=None, make_fuzzy=True, models=None):
    ''' generate a list of datamodel types '''

    assert ymlfile.stem == 'products', 'can only load products.yaml files'

    # generate the full datamodel schema
    dmschema = find_datamodels(ymlfile)
    schema = create_product_schema(dmschema, models=models)
    data = read_yaml(ymlfile)

    # validate the products
    data = validate_products(data, dmschema)

    # get the products data
    many = False if name else True
    objects = data.get(name, None) if name else data.values()

    # check validation on changelog attribute
    if 'changelog' in schema._declared_fields:
        key = schema._declared_fields['changelog']
        if not key.key_field.validators:
            versions = list(objects)[0]['versions']
            key.key_field = fields.String(validate=validate.OneOf(versions))
            schema._declared_fields['changelog'] = key

    # deserialize the object
    models = schema(many=many).load(objects, many=many)

    if make_fuzzy and isinstance(models, list):
        models = ProductList(models)
    return models

