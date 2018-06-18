# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-05-30 13:53:46
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-06-12 18:46:39

from __future__ import print_function, division, absolute_import
from cthreepo.utils.input import read_schema_from_sql
from cthreepo.core.exceptions import CthreepoError
import six
import abc
import sys
import inspect
import contextlib


CORE_VARS = ['ivar', 'std', 'mask', 'wave']


@contextlib.contextmanager
def mix(self, mixin):
    ''' Context manager to look up which mixin is being accessed '''

    # check for mixing and if mixin is not a core variable
    if mixin and mixin not in CORE_VARS:
        assert mixin.lower() in MIXINS.keys(), 'mixin must be one of {0}'.format(MIXINS.keys())
        mix_obj = MIXINS[mixin]
        yield mix_obj
    else:
        mix_bases = [obj for obj in self.__class__.__bases__ if 'Mixin' in obj.__name__]
        if len(mix_bases) == 1:
            yield mix_bases[0]
        else:
            raise ValueError('Mixin ambiguity.  Please specify one of {0}!'.format(MIXINS.keys()))


def check_mixins(cls, **kwargs):
    ''' Check a class's keyword args against all Mixins bases '''
    mixin = list_mixins()
    for mix in mixin:
        mixtype = mix.__name__.split('Mix')[0].lower()
        haskwargs = mix.check_kwargs(**kwargs)
        if haskwargs:
            assert mix in cls.__bases__, 'Must have appropriate mixin {0} to use {1} keywords'.format(mix.__name__, mixtype)


def list_mixins():
    ''' Get a list of all Mixin classes '''
    mixin = MIXINS.values()
    return mixin


class BaseMixin(six.with_metaclass(abc.ABCMeta, object)):

    def __new__(cls, *args, **kwargs):
        setattr(cls, '_core_vars', CORE_VARS)
        mixins = [obj for obj in cls.__bases__ if 'Mixin' in obj.__name__]
        if len(mixins) > 1:
            for core in CORE_VARS:
                assert core not in args, 'Multiple mixins found. {0} is too ambiguous'.format(core)

        return super(BaseMixin, cls).__new__(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        pass

    @classmethod
    @abc.abstractmethod
    def check_kwargs(cls, **kwargs):
        pass

    @abc.abstractmethod
    def _full(self):
        ''' Display the full name '''

    @abc.abstractmethod
    def _ivar(self):
        pass

    @abc.abstractmethod
    def _std(self):
        pass

    @abc.abstractmethod
    def _mask(self):
        pass

    @abc.abstractmethod
    def _wave(self):
        pass

    def full(self, mixin=None, **kwargs):
        with mix(self, mixin) as m:
            return m._full(self, **kwargs)

    def has_ivar(self, mixin=None):
        with mix(self, mixin) as m:
            return m._ivar(self)

    def has_std(self, mixin=None):
        with mix(self, mixin) as m:
            return m._std(self)

    def has_mask(self, mixin=None):
        with mix(self, mixin) as m:
            return m._mask(self)

    def has_wave(self, mixin=None):
        with mix(self, mixin) as m:
            return m._wave(self)


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

    def _full(self, ext=None):
        dbnames = [self.db_name, self.db_schema, self.db_table, self.db_extension(ext=ext)]
        self._db_full = '.'.join([d for d in dbnames if d])
        return self._db_full

    @property
    def db_column(self):
        return self._db_column

    @classmethod
    def load_from_sql(cls, sqlfile):
        ''' Create a DataModel from a sql file '''
        from cthreepo.core.lists import BaseList
        assert issubclass(cls, BaseList), 'Can only use method on [Object]List classes'
        tables = read_schema_from_sql(sqlfile)

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

    def db_extension(self, ext=None):
        """Returns the DB extension name."""

        assert ext is None or ext in self._core_vars, 'invalid extension'

        if ext is None:
            return self._db_column

        elif ext == 'ivar':
            if not self.has_ivar('db'):
                raise CthreepoError('no ivar extension for object {0!r}'.format(self._full()))
            return self._db_ivar

        elif ext == 'mask':
            if not self.has_mask('db'):
                raise CthreepoError('no mask extension for object {0!r}'.format(self._full()))
            return self._db_mask

        elif ext == 'std':
            if not self.has_std('db'):
                raise CthreepoError('no std extension for object {0!r}'.format(self._full()))
            return self._db_std

        elif ext == 'wave':
            if not self.has_wave('db'):
                raise CthreepoError('no wave extension for object {0!r}'.format(self._full()))
            return self._db_wave

    def _ivar(self):
        """Returns True is the datacube has an ivar extension."""

        return self._db_ivar is not None

    def _mask(self):
        """Returns True is the datacube has an mask extension."""

        return self._db_mask is not None

    def _std(self):
        """Returns True is the datacube has an std extension."""

        return self._db_std is not None

    def _wave(self):
        """Returns True is the datacube has an wave extension."""

        return self._db_wave is not None


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

    def _full(self, **kwargs):
        """Returns the name string."""

        return self._extension_name.lower() if self._extension_name else ''

    def _ivar(self):
        """Returns True is the datacube has an ivar extension."""

        return self._extension_ivar is not None

    def _mask(self):
        """Returns True is the datacube has an mask extension."""

        return self._extension_mask is not None

    def _std(self):
        """Returns True is the datacube has an std extension."""

        return self._extension_std is not None

    def _wave(self):
        """Returns True is the datacube has an wave extension."""

        return self._extension_wave is not None

    def fits_extension(self, ext=None):
        """Returns the FITS extension name."""

        assert ext is None or ext in self._core_vars, 'invalid extension'

        if ext is None:
            return self._extension_name.upper()

        elif ext == 'ivar':
            if not self.has_ivar('fits'):
                raise CthreepoError('no ivar extension for object {0!r}'.format(self._full()))
            return self._extension_ivar.upper()

        elif ext == 'mask':
            if not self.has_mask('fits'):
                raise CthreepoError('no mask extension for object {0!r}'.format(self._full()))
            return self._extension_mask

        elif ext == 'std':
            if not self.has_std('fits'):
                raise CthreepoError('no std extension for object {0!r}'.format(self._full()))
            return self._extension_std.upper()

        elif ext == 'wave':
            if not self.has_wave('fits'):
                raise CthreepoError('no wave extension for object {0!r}'.format(self._full()))
            return self._extension_wave.upper()

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

