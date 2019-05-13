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
from cthreepo.core.structs import FuzzyDict, FuzzyList
from cthreepo.core.models import generate_models
from cthreepo.core.products import generate_products
from cthreepo.utils.yaml import get_yaml_files, read_yaml


class DataModel(object):
    survey = None

    def __new__(cls, *args, **kwargs):
        cls._segment = cls._get_segment()
        datamodel_dir = os.environ['CTHREEPO_DIR'] / pathlib.Path(cls._segment)
        cls._products_file = get_yaml_files(datamodel_dir, get='products')
        cls._model_files = get_yaml_files(datamodel_dir, get='models')
        return super(DataModel, cls).__new__(cls, *args, **kwargs)

    def __init__(self):
        self._classes = []
        self.models = self._generate_models()
        self.products = generate_products(self._products_file, models=self.models)

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
            models = generate_models(data)
            self._classes.append(models[0].__class__)
            fd[file.stem] = models
        return FuzzyDict(fd)


class SDSSDataModelList(FuzzyList):
    def mapper(self, item):
        return str(item.survey.lower())


from .manga import dm as mdm
from .simple import dm as sdm
dm = SDSSDataModelList([mdm, sdm])
