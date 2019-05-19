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
import re
import pathlib
import copy
from itertools import groupby
from cthreepo.core.structs import FuzzyDict, FuzzyList
from cthreepo.core.models import generate_models
from cthreepo.core.products import generate_products
from cthreepo.utils.yaml import get_yaml_files, read_yaml


class DataModel(object):
    survey = None
    _mixed_models = {}

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
        assert cls.survey is not None, 'survey must be specified in new DataModel'
        here = pathlib.Path(__file__).resolve()
        dm_idx = str(here).find('datamodel')
        segment = str(here)[dm_idx:].rsplit('/', 1)[0]
        if not segment.endswith(cls.survey.lower()):
            addon = pathlib.Path(cls.survey.lower()) if cls.survey else ''
            segment = pathlib.Path(segment) / addon
        return str(segment)

    # def _check_for_mixin(self):
    #     ''' check if a mixin exists for model '''

    def _generate_models(self):
        fd = {}
        mixin = None
        assert isinstance(self._mixed_models, dict), 'mix_models must be a dict'
        keys = '|'.join(self._mixed_models.keys()) if self._mixed_models else None
        for file in self._model_files:
            # check for mixin model
            if keys:
                mixmatch = re.search(keys, str(file))
                if mixmatch:
                    mixin = self._mixed_models[mixmatch.group()]
            data = read_yaml(file)
            models = generate_models(data, mixin=mixin)
            self._classes.append(models[0].__class__)
            fd[file.stem] = models
        return FuzzyDict(fd)

    def _get_all_versions(self):
        ''' get all versions in this datamodel '''
        if 'versions' in self.models:
            allversions = self.models['versions']
        else:
            verdict = {}
            for prod in self.products:
                verdict.update({v: [] for v in prod.versions})
            allversions = list(verdict.keys())
        return allversions

    def organize_by_version(self, public=None):
        ''' organize the datamodel by version number '''
        versions = self._get_all_versions()
        releases = []
        pclass = type(self.products)
        for k in versions:
            if public and 'DR' not in str(k):
                continue
            prods = []
            for prod in self.products:
                # reset changelog and expanded products
                if prod._changes is not None or prod._expanded is not None:
                    prod._changes = None
                    prod._expanded = None
                # replicate the product
                if k in prod.versions:
                    newprod = copy.deepcopy(prod)
                    newprod.versions = [prod.versions[prod.versions.index(k)]]
                    prods.append(newprod)
            releases.append(VDataModel(k, survey=self.survey, products=pclass(prods)))
        return VDataModelList(releases)


class VDataModel(object):

    def __init__(self, release, products=None, survey=None):
        self.release = release
        self.products = products
        self.survey = survey

    def __repr__(self):
        return f'<{self.survey.title()}DataModel({self.release}, n_products={len(self.products)})'


class VDataModelList(FuzzyList):
    def mapper(self, item):
        version = str(item.release).lower().replace('.', '_')
        return version
    
    @property
    def releases(self):
        return [str(item.release) for item in self]


class SDSSDataModelList(FuzzyList):
    def mapper(self, item):
        return str(item.survey.lower())
    
    def organize_by_release(self, public=None):
        ''' organize the datamodel by release '''
        # TODO - fix the return object 
        # create the data
        data = []
        for item in self:
            data += item.organize_by_version(public=public)
        data = sorted(data, key=lambda x: str(x.release))

        releases = {k: list(g) for k, g in groupby(data, key=lambda x: str(x.release))}
        return releases


from .manga import dm as mdm
from .simple import dm as sdm
dm = SDSSDataModelList([mdm, sdm])
