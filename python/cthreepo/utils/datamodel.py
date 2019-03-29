# !/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Filename: datamodels.py
# Project: utils
# Author: Brian Cherinka
# Created: Friday, 29th March 2019 1:48:16 pm
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2019 Brian Cherinka
# Last Modified: Friday, 29th March 2019 2:00:53 pm
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import
import os
import pathlib
from cthreepo.utils.yaml import read_yaml, expand_yaml


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


def validate_products(ymlfile):
    ''' validate the products yaml file against the dm '''

    # read the yaml
    data = read_yaml(ymlfile)

    # validate the products
    if ymlfile.stem == 'products':
        dm = find_datamodels(ymlfile)
        data = expand_yaml(data)
        for prodname, content in data.items():
            prodkeys = set(content.keys())
            dmkeys = set(dm['schema'].keys())
            notallowed = ', '.join(prodkeys - dmkeys)
            assert prodkeys.issubset(
                dmkeys), f'product "{prodname}" contains unallowed keys ({notallowed}) in datamodel schema'
    return data

