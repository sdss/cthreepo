# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-05-30 13:53:46
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-06-20 09:37:14

from __future__ import print_function, division, absolute_import
from cthreepo.utils.input import read_schema_from_sql
from cthreepo.core.exceptions import CthreepoError
import six
import abc
import sys
import inspect
from functools import wraps
from collections import defaultdict


CORE_VARS = ['ivar', 'std', 'mask', 'wave']


def check_mixins(cls, **kwargs):
    ''' Check a class's keyword args against all Mixins bases '''
    mixin = list_mixins()
    for mix in mixin:
        mixtype = mix.__name__.split('Mix')[0].lower()
        haskwargs = mix.check_kwargs(**kwargs)
        if haskwargs:
            assert mix in cls.__bases__, 'Must have appropriate mixin {0} to use {1} keywords'.format(mix.__name__, mixtype)


def list_mixins(by_name=None):
    ''' Get a list of all Mixin classes '''
    mixin = MIXINS.values()
    if by_name:
        mixin = [_get_mixin_type(mix) for mix in mixin]
    return mixin


def _flatten(l):
    ''' Flatten a nested list '''
    res = []
    for item in l:
        if isinstance(item, list):
            res.extend(_flatten(item))
        else:
            res.append(item)
    return res


def _get_mixin_type(mixin):
    return mixin.__name__.lower().split('mixin')[0]


def mixable(func):
    '''Decorator that checks if ..'''

    @wraps(func)
    def wrapper(*args, **kwargs):
        name = func.__name__.split('_')[1] if 'has_' in func.__name__ else func.__name__
        inst = args[0]
        value = args[1] if len(args) > 1 else None
        # get the mixin bases from the instance
        mix_bases = [obj for obj in inst.__class__.__bases__ if 'Mixin' in obj.__name__]

        if value:
            # flatten the list
            res = _flatten(value)
            # the first value should be the mixin key
            mix_key = res.pop(0)

            # the input value is not a valid mixin
            assert mix_key is None or mix_key.lower() in MIXINS.keys(),\
                ('Input value {0} must be one of valid {1}'.format(mix_key, list(MIXINS.keys())))

            # check if mixin key is an available class
            if mix_key and mix_key.lower() in MIXINS.keys():
                if MIXINS[mix_key] in mix_bases:
                    # find the appropriate index in the bases list
                    mix_idx = mix_bases.index(MIXINS[mix_key])
                    if res:
                        value = res[mix_idx]
                else:
                    # the input Mixin value is not one of the instance bases
                    raise ValueError('Requested mixin {0} is not available for {1}'.format(mix_key, name))
            elif mix_key is None:
                # there is no mixin key present as input
                if len(res) == 1:
                    value = res[0]
                else:
                    if name in CORE_VARS:
                        value = any(res) or None
                    else:
                        value = res

        args = (inst, value)
        return func(*args, **kwargs)
    return wrapper


def _make_defaultdict(base, keys):
    dd = defaultdict(base)
    __ = [dd[key] for key in keys]
    return dd


class MixMeta(abc.ABCMeta):

    def __call__(cls, *args, **kwargs):

        coredict = _make_defaultdict(dict, CORE_VARS)
        setattr(cls, '_core_vars', coredict)
        mixins = [obj for obj in cls.__bases__ if 'Mixin' in obj.__name__]
        newclass = super(MixMeta, cls).__call__(*args, **kwargs)
        #kwargs['name'] = args[0]
        if len(mixins) > 1:
            assert 'name' not in kwargs, 'Multiple mixins found.  name is too ambiguous'
            assert 'ivar' not in kwargs, 'Multiple mixins found.  ivar is too ambiguous'
            for mix in mixins:
                mixname = mix.__name__.lower().split('mixin')[0]
                setattr(newclass, '{0}_extension'.format(mixname), mix(**kwargs)._extension)
        elif len(mixins) == 1:
            print('mixmeta', cls, args, kwargs)
            mix = mixins[0]
            setattr(newclass, 'extension', mix(**kwargs)._extension)

        return newclass


class BaseMixin(six.with_metaclass(abc.ABCMeta, object)):

    def __new__(cls, *args, **kwargs):
        setattr(cls, '_core_vars', CORE_VARS)
        mixins = [obj for obj in cls.__bases__ if 'Mixin' in obj.__name__]
        if len(mixins) > 1:
            for core in CORE_VARS:
                assert core not in args, 'Multiple mixins found. {0} is too ambiguous'.format(core)

        return super(BaseMixin, cls).__new__(cls)

    def __init__(self, *args, **kwargs):
        pass

    @classmethod
    @abc.abstractmethod
    def check_kwargs(cls, **kwargs):
        pass

    @mixable
    @abc.abstractmethod
    def full(self, value=None):
        return value

    @mixable
    @abc.abstractmethod
    def has_ivar(self, value=None):
        return value is not None

    @mixable
    @abc.abstractmethod
    def has_std(self, value=None):
        return value is not None

    @mixable
    @abc.abstractmethod
    def has_mask(self, value=None):
        return value is not None

    @mixable
    @abc.abstractmethod
    def has_wave(self, value=None):
        return value is not None

    @abc.abstractmethod
    def _extension(self, ext=None, name=None, ivar=None, std=None, mask=None, wave=None):

        assert ext is None or ext in self._core_vars, 'invalid extension'

        if ext is None:
            return name
        elif ext == 'ivar':
            if not self.has_ivar():
                raise CthreepoError('no ivar extension for object {0!r}'.format(self.name))
            return ivar
        elif ext == 'std':
            if not self.has_std():
                raise CthreepoError('no std extension for object {0!r}'.format(self.name))
            return std
        elif ext == 'mask':
            if not self.has_mask():
                raise CthreepoError('no mask extension for object {0!r}'.format(self.name))
            return mask
        elif ext == 'wave':
            if not self.has_wave():
                raise CthreepoError('no wave extension for object {0!r}'.format(self.name))
            return wave


class DbMixin(BaseMixin):

    def __init__(self, db_full=None, db_name=None, db_schema=None, db_table=None,
                 db_ivar=None, db_mask=None, db_std=None, db_wave=None, **kwargs):
        super(DbMixin, self).__init__(**kwargs)
        self.db_name = db_name
        self.db_schema = db_schema
        self.db_table = db_table
        self._db_full = db_full
        self._db_column = None
        self._db_column_type = None

        self._db_ivar = db_ivar or kwargs.get('ivar', None)
        self._db_mask = db_mask or kwargs.get('mask', None)
        self._db_std = db_std or kwargs.get('std', None)
        self._db_wave = db_wave or kwargs.get('mask', None)

        assert db_full or any([db_name, db_table, db_schema]), 'Must specify at least one db_ parameter'
        self._set_names()

    @classmethod
    def check_kwargs(cls, **kwargs):
        return any(['db_' in k for k in kwargs.keys()])

    def full(self, value=None):
        dbnames = [self.db_name, self.db_schema, self.db_table, self.db_column]
        self._db_full = '.'.join([d for d in dbnames if d])
        return super(DbMixin, self).full([value, self._db_full])

    @property
    def db_column(self):
        return self._db_column

    # @classmethod
    # def load_from_sql(cls, sqlfile):
    #     ''' Create a DataModel from a sql file '''
    #     from cthreepo.core.lists import BaseList
    #     assert issubclass(cls, BaseList), 'Can only use method on [Object]List classes'
    #     tables = read_schema_from_sql(sqlfile)

    # def dump_to_sql(self):
    #     ''' Dump DataModel to a sql file '''
    #     pass

    # @classmethod
    # def load_from_models(cls, modelsfile):
    #     ''' Create a DataModel from a db models file '''
    #     pass

    # def dump_to_models(self):
    #     ''' Dump DataModel to a models file '''
    #     pass

    def _set_names(self):
        ''' Set the database naming conventions '''
        if self._db_full:
            ndot = self._db_full.count('.')
            dbsplit = self._db_full.split('.')
            if ndot == 0:
                self._db_column = self._db_full
            elif ndot == 1:
                self.db_table, self._db_column = dbsplit
            elif ndot == 2:
                self.db_schema, self.db_table, self._db_column = dbsplit
            elif ndot == 3:
                self.db_name, self.db_schema, self.db_table, self._db_column = dbsplit

        # set the db column if not set already
        if not self._db_column and hasattr(self, 'name'):
            self._db_column = self.name

    def _extension(self, ext=None, **kwargs):
        ''' Return the DB extension nmae '''
        return super(DbMixin, self)._extension(ext=ext, name=self._db_full, ivar=self._db_ivar,
                                               std=self._db_std, mask=self._db_mask, wave=self._db_wave)

    def has_ivar(self, value=None):
        return super(DbMixin, self).has_ivar([value, self._db_ivar])

    def has_std(self, value=None):
        return super(DbMixin, self).has_std([value, self._db_std])

    def has_mask(self, value=None):
        return super(DbMixin, self).has_mask([value, self._db_mask])

    def has_wave(self, value=None):
        return super(DbMixin, self).has_wave([value, self._db_wave])


class FileMixin(BaseMixin):

    def __init__(self, **kwargs):
        super(FileMixin, self).__init__(**kwargs)
        self.fullfile = None
        self.filename = None
        self.filepath = None
        self.filetype = None


class ImageMixin(FileMixin):

    def __init__(self, **kwargs):
        super(ImageMixin, self).__init__(**kwargs)

    @classmethod
    def check_kwargs(cls, **kwargs):
        return any(['image' in k for k in kwargs.keys()])


class CatalogMixin(FileMixin):

    def __init__(self, **kwargs):
        super(CatalogMixin, self).__init__(**kwargs)

    @classmethod
    def check_kwargs(cls, **kwargs):
        return any(['catalog' in k for k in kwargs.keys()])


class FitsMixin(FileMixin):

    def __init__(self, extension_name=None, extension_wave=None, extension_ivar=None,
                 extension_mask=None, extension_std=None, **kwargs):
        super(FitsMixin, self).__init__(**kwargs)
        self._extension_name = extension_name or kwargs.get('name', None)
        self._extension_wave = extension_wave or kwargs.get('wave', None)
        self._extension_std = extension_std or kwargs.get('std', None)
        self._extension_ivar = extension_ivar or kwargs.get('ivar', None)
        self._extension_mask = extension_mask or kwargs.get('mask', None)

        assert any([extension_name, extension_ivar, extension_std]), 'Must specify at least one extension_ parameter'

    @classmethod
    def check_kwargs(cls, **kwargs):
        return any(['extension' in k for k in kwargs.keys()])

    def __str__(self):

        return self._full.lower()

    def full(self, value=None):
        name = self._extension_name.lower() if self._extension_name else ''
        return super(FitsMixin, self).full([value, name])

    def has_ivar(self, value=None):
        return super(FitsMixin, self).has_ivar([value, self._extension_ivar])

    def has_std(self, value=None):
        return super(FitsMixin, self).has_std([value, self._extension_std])

    def has_mask(self, value=None):
        return super(FitsMixin, self).has_mask([value, self._extension_mask])

    def has_wave(self, value=None):
        return super(FitsMixin, self).has_wave([value, self._extension_wave])

    def _extension(self, ext=None, **kwargs):
        ''' Returns the FITS extension name'''

        return super(FitsMixin, self)._extension(ext=ext, name=self._extension_name,
                                                 ivar=self._extension_ivar, std=self._extension_std,
                                                 mask=self._extension_mask, wave=self._extension_wave)

    @classmethod
    def load_from_fits(cls, fitsfile):
        ''' Create a DataModel from a FITS file '''
        from cthreepo.core.lists import BaseList
        assert issubclass(cls, BaseList), 'Can only use method on [Object]List classes'

    def dump_to_fits(self):
        ''' Dump DataModel to a FITS file '''
        pass


MIXINS = {name.lower().split('mixin')[0]: obj for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass)
          if 'Mixin' in name and 'Base' not in name}

