# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-05-30 18:03:36
# @Last modified by:   Brian
# @Last Modified time: 2018-06-12 01:11:29

from __future__ import print_function, division, absolute_import
import os
import pathlib
from cthreepo.core.structs import FuzzyDict
from cthreepo.core.objects import generate_models, read_yaml, generate_products


def get_yaml_files(path, get='products'):
    ''' '''
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


class DataModel(object):
    survey = None

    def __new__(cls, *args, **kwargs):
        cls._segment = cls._get_segment()
        datamodel_dir = os.environ['CTHREEPO_DIR'] / pathlib.Path(cls._segment)
        cls._products_file = get_yaml_files(datamodel_dir, get='products')
        cls._model_files = get_yaml_files(datamodel_dir, get='models')
        return super(DataModel, cls).__new__(cls, *args, **kwargs)

    def __init__(self):
        self.products = generate_products(self._products_file, base=self._segment)
        self.models = self._generate_models()

    def __repr__(self):
        return f'<{self.survey.title()}DataModel(n_products={len(self.products)})'

    @classmethod
    def _get_segment(cls):
        ''' get the datamodel segment '''
        here = pathlib.Path(__file__).resolve()
        dm_idx = str(here).find('datamodel')
        segment = str(here)[dm_idx:].rsplit('/', 1)[0]
        if not segment.endswith(cls.survey.lower()):
            addon = pathlib.Path(cls.survey.lower()) if cls.survey else ''
            segment = pathlib.Path(segment) / addon
        return str(segment)

    def _generate_models(self):
        fd = {}
        for file in self._model_files:
            data = read_yaml(file)
            #setattr(self, file.stem, generate_models(data))
            fd[file.stem] = generate_models(data)
        return FuzzyDict(fd)
