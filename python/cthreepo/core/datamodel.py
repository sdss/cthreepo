# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-05-30 11:31:19
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-09-20 18:50:56

from __future__ import print_function, division, absolute_import
from collections import OrderedDict
import six
import copy as copy_mod
import abc
from cthreepo.utils.input import read_schema_from_sql


class MetaDataModel(type):
    ''' MetaClass to construct a new DataModelList class '''
    def __new__(cls, name, parents, dict):
        if 'base' in dict:
            item = list(dict['base'].items())[0]
            dict['base_name'] = item[0].strip()
            dict['base_model'] = item[1]
        return super(MetaDataModel, cls).__new__(cls, name, parents, dict)


class DataModelList(six.with_metaclass(MetaDataModel, OrderedDict)):
    ''' Base Class for a list of DataModels '''

    def __init__(self, models=None):

        if models is not None:
            assert all([isinstance(model, self.base_model) for model in models]), \
                'values must be {0} instances.'.format(self.base_name)
            OrderedDict.__init__(self, ((model.release, model) for model in models))
        else:
            OrderedDict.__init__(self, {})

    def __setitem__(self, key, value):
        """Sets a new datamodel."""

        assert isinstance(value, self.base_model), 'value must be a {0}'.format(self.base_name)

        super(DataModelList, self).__setitem__(key, value)

    def __getitem__(self, release):
        """Returns model based on release and aliases."""

        if release in self.keys():
            return super(DataModelList, self).__getitem__(release)

        for model in self.values():
            if release in model.aliases:
                return model

        raise KeyError('cannot find release or alias {0!r}'.format(release))

    def __contains__(self, value):
        ''' Returns True based on release/aliases using getitem '''
        try:
            dm = self[value]
            return True
        except KeyError as e:
            return False

    def __repr__(self):

        return repr([xx for xx in self.values()])

    def add_datamodel(self, dm):
        """Adds a new datamodel. Uses its release as key."""

        assert isinstance(dm, self.base_model), 'value must be a {0}'.format(self.base_name)

        self[dm.release] = dm


class BaseDataModel(six.with_metaclass(abc.ABCMeta, object)):
    ''' Base DataModel '''

    def __init__(self, release, aliases=[], bitmasks=None):
        self.release = release
        self.aliases = aliases
        self.bitmasks = bitmasks if bitmasks is not None else {}

    @abc.abstractmethod
    def __repr__(self):
        return ('<DataModel release={0!r}>'.format(self.release))

    def copy(self):
        """Returns a copy of the datamodel."""

        return copy_mod.deepcopy(self)

    @abc.abstractmethod
    def __eq__(self, value):
        """Uses fuzzywuzzy to return the closest property match."""
        pass

    def __contains__(self, value):

        try:
            match = self.__eq__(value)
            if match is None:
                return False
            else:
                return True
        except ValueError:
            return False

    def __getitem__(self, value):
        return self == value

    @classmethod
    def load_from_sql(cls, sqlfile, db=None, release='1.0', aliases=None, from_file=None, fullfile=None):
        ''' Create a DataModel from a sql file '''

        from cthreepo.core.mixins import DbMixin, CatalogMixin, FitsMixin
        from cthreepo.core.objects import Property
        from cthreepo.core.lists import PropertyList

        assert from_file in [None, 'catalog', 'fits'], 'from_file can only be catalog or fits'

        # get mixin classes
        if from_file:
            filemixin = CatalogMixin if from_file == 'catalog' else FitsMixin
            classes = (Property, DbMixin, filemixin,)
        else:
            classes = (Property, DbMixin,)

        db = 'sdss5b' if not db else db
        tables = read_schema_from_sql(sqlfile)

        propclass = type(cls.__name__, classes, {})
        properties = []
        for col in tables['columns']:
            prop = propclass(col, db_name=db, db_schema=tables['schema'], db_table=tables['table'])
            properties.append(prop)
        cls.properties = PropertyList(properties)
        return cls(release, aliases=aliases, fullfile=fullfile)

    def dump_to_sql(self):
        ''' Dump DataModel to a sql file '''
        pass

    @classmethod
    def load_from_models(cls, modelsfile):
        ''' Create a DataModel from a db models file '''
        pass

    def dump_to_models(self):
        ''' Dump DataModel to a models file '''
        pass

