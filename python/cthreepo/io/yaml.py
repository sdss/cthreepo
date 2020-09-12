# !/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Filename: yaml.py
# Project: utils
# Author: Brian Cherinka
# Created: Friday, 29th March 2019 1:46:58 pm
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2019 Brian Cherinka
# Last Modified: Friday, 5th April 2019 6:37:00 am
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import
import pathlib
import re
import os
import yaml


def get_yaml_files(path: str, get: str = 'products') -> list:
    ''' Find valid yaml files

    Parameters:
        path : str
            A filepath to a yaml datamodel
        get : str
            A name of the yaml file to find

    Returns:
        A list of all available yaml files
    '''
    assert get in ['datamodel', 'products', 'models']
    datamodel_dir = os.environ['CTHREEPO_DIR'] / pathlib.Path(path)
    if get in ['products', 'datamodel']:
        files = list(datamodel_dir.rglob(f'*{get}*.yaml'))
        assert len(list(files)) == 1, f'there can only be one {get} file'
        return files[0]
    elif get == 'models':
        files = []
        for file in datamodel_dir.rglob('*.yaml'):
            if file.stem not in ['datamodel', 'products']:
                files.append(file)
        return files


def read_yaml(ymlfile: str) -> dict:
    ''' Opens and reads a yaml datamodel file

    Parameters:
        ymlfile : str

    Returns:
        dictionary contents of yaml file
    '''

    if isinstance(ymlfile, str):
        ymlfile = pathlib.Path(ymlfile)

    with open(ymlfile, 'r') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)

    if ymlfile.stem not in ['datamodel', 'products']:
        assert 'schema' in data, 'datamodel file must contain a schema section'
        assert 'objects' in data, 'datamodel file must contain an objects section'

    return data


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
    assert version in versions, f'{version} not in allowed list of versions'

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


def expand_yaml(data: dict) -> dict:
    ''' Expand the yaml with version substitution '''

    # loop over the objects
    for key, value in data.items():
        changelog = value.get('changelog', None)
        versions = value.get('versions', None)
        assert versions is not None, f'Must have a "versions" key set for object: {key}'
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

