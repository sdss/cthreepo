# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-05-30 13:53:46
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-06-08 08:26:51

from __future__ import print_function, division, absolute_import
from cthreepo.utils.input import read_schema_from_sql
from cthreepo.core.exceptions import CthreepoError
import six
import abc
import sys
import inspect


def check_mixins(cls, **kwargs):
    ''' Check a class keyword args against all Mixins bases '''
    mixin = list_mixins()
    for mix in mixin:
        mixtype = mix.__name__.split('Mix')[0].lower()
        haskwargs = mix.check_kwargs(**kwargs)
        if haskwargs:
            assert mix in cls.__mro__, 'Must have appropriate mixin {0} to use {1} keywords'.format(mix.__name__, mixtype)


def list_mixins():
    ''' Get a list of all Mixin classes '''
    mixin = [obj for name, obj in inspect.getmembers(sys.modules[__name__])
             if inspect.isclass(obj) and 'Mixin' in obj.__name__ and 'Base' not in obj.__name__]
    return mixin


class BaseMixin(six.with_metaclass(abc.ABCMeta, object)):

    @classmethod
    @abc.abstractmethod
    def check_kwargs(cls, **kwargs):
        pass


class DbMixin(BaseMixin):

    def __init__(self, db_name=None, db_table=None, db_schema=None, **kwargs):
        print('init dbmixin')
        super(DbMixin, self).__init__(**kwargs)
        self.db_name = db_name
        self.db_schema = db_schema
        self.db_table = db_table
        self._db_column = None
        self._db_column_type = None

    @classmethod
    def check_kwargs(cls, **kwargs):
        return any(['db_' in k for k in kwargs.keys()])

    @property
    def db_column(self):
        return self._db_column

    @classmethod
    def load_from_sql(cls, sqlfile):
        ''' Create a DataModel from a sql file '''
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


class FileMixin(BaseMixin):

    def __init__(self, **kwargs):
        print('init filemixin')
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
        print('init fitsmixin')
        super(FitsMixin, self).__init__(**kwargs)
        self._extension_name = extension_name
        self._extension_wave = extension_wave
        self._extension_std = extension_std
        self._extension_ivar = extension_ivar
        self._extension_mask = extension_mask

    @classmethod
    def check_kwargs(cls, **kwargs):
        return any(['extension' in k for k in kwargs.keys()])

    def __str__(self):

        return self.full.lower()

    def full(self):
        """Returns the name string."""

        return self._extension_name.lower() if self._extension_name else ''

    def has_ivar(self):
        """Returns True is the datacube has an ivar extension."""

        return self._extension_ivar is not None

    def has_mask(self):
        """Returns True is the datacube has an mask extension."""

        return self._extension_mask is not None

    def has_std(self):
        """Returns True is the datacube has an std extension."""

        return self._extension_std is not None

    def has_wave(self):
        """Returns True is the datacube has an wave extension."""

        return self._extension_wave is not None

    def fits_extension(self, ext=None):
        """Returns the FITS extension name."""

        assert ext is None or ext in ['std', 'wave', 'ivar', 'mask'], 'invalid extension'

        if ext is None:
            return self._extension_name.upper()

        elif ext == 'ivar':
            if not self.has_ivar():
                raise CthreepoError('no ivar extension for datacube {0!r}'.format(self.full()))
            return self._extension_ivar.upper()

        elif ext == 'mask':
            if not self.has_mask():
                raise CthreepoError('no mask extension for datacube {0!r}'.format(self.full()))
            return self._extension_mask

        elif ext == 'std':
            if not self.has_std():
                raise CthreepoError('no std extension for spectrum {0!r}'.format(self.full()))
            return self._extension_std.upper()

        elif ext == 'wave':
            if not self.has_wave():
                raise CthreepoError('no wave extension for spectrum {0!r}'.format(self.full()))
            return self._extension_wave.upper()

