# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-05-30 11:31:19
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-05-31 00:23:04

from __future__ import print_function, division, absolute_import
from collections import OrderedDict
import six
import copy as copy_mod
import abc


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

