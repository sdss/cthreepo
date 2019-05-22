# !/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Filename: fits.py
# Project: core
# Author: Brian Cherinka
# Created: Saturday, 1st December 2018 6:20:08 am
# License: <<licensename>>
# Copyright (c) 2018 Brian Cherinka
# Last Modified: Wednesday, 22nd May 2019 2:53:40 pm
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import
import os
import re
import six
import pathlib
from io import StringIO
from astropy.io import fits, ascii as astropy_ascii
from sdss_access.path import Path
from cthreepo.utils.general import compute_diff


class BaseObject(object):

    def __init__(self, product=None, version=None):
        self.product = product
        self.version = version
        
    def __repr__(self):
        return f'<Object(name={self.product}, version={self.version})>'


class FileObject(BaseObject):
    path = Path()

    def __init__(self, inputs=None, filename=None, **kwargs):
        product = kwargs.pop('product', None)
        version = kwargs.pop('version', None)
        super(FileObject, self).__init__(product=product, version=version)
        self.path.replant_tree(str(version))
        self.filename = filename
        self.path_name = kwargs.pop('path_name', None)
        self.parent = kwargs.pop('parent', None)
        self._info = None
        self._stats = None
        self._changes = None
        self.loaded = False

        # check inputs and produce filename
        self._determine_inputs(inputs, **kwargs)
        self._parse_filename()

    def _determine_inputs(self, inputs, **kwargs):
        ''' Determine the input '''

        # use filename if found instead of inputs
        if inputs is None and self.filename:
            return

        # no input at all
        if not inputs and self.path_name is None:
            raise ValueError('No input has been provided to determine a valid file')

        # check if inputs is a pathlib.Path
        if isinstance(inputs, pathlib.Path):
            inputs = str(inputs)

        assert isinstance(inputs, six.string_types), 'input must be a string'

        # check if input is an sdss_access Path
        if inputs in self.path.lookup_names():
            self.path_name = inputs
            keys = self.path.lookup_keys(inputs)
            missing = set(keys) - set(kwargs.keys())
            if missing:
                raise KeyError('Input sdss_access name missing '
                               'necessary kwargs: {0}'.format(', '.join(missing)))

            # get the full path
            self.filename = self.path.full(inputs, **kwargs)
        else:
            # assume it is a filename
            self.filename = inputs

    def _parse_filename(self):
        ''' Parse a filename into components '''

        path = pathlib.Path(self.filename)
        self.filepath = path.parent
        self.filename = path.name
        self.fullpath = self.filepath / self.filename

        self.file_exists = self.path.exists('', full=self.fullpath)
        # if not self.file_exists:
        #     raise NameError('{0} not a valid file'.format(self.fullpath))

    @staticmethod
    def _get_example(example, replace=None):
        ''' set the example '''
        ex_regex = r'^(\w+work|dr\d{1,2})'
        assert re.match(ex_regex,
                        example), 'example must start work xxxwork or drxx'
        if replace and 'dr' in str(replace).lower():
            example = re.sub(ex_regex, str(replace).lower(), example)
        path = pathlib.Path(os.path.expandvars('$SAS_BASE_DIR')) / example
        return path

    @classmethod
    def from_example(cls, example, **kwargs):
        ''' Instantiates a file from an example filepath'''

        version = kwargs.get('version', None)
        path = cls._get_example(example, replace=version)
        # if not path.is_file():
        #     raise ValueError(f'Example provided does seem to exist!  Check again.')
        return cls(path, **kwargs)

    @classmethod
    def from_path(cls, path_name, example=None, **kwargs):
        ''' Instantiates a file from an sdss_access path definition '''
        path_kwargs = kwargs.pop('path_kwargs', None)
        version = kwargs.get('version', None)
        cls.path.replant_tree(str(version) if version else None)
        
        if example:
            path = cls._get_example(example, replace=version)
            args = cls.path.extract(path_name, path)
            kwargs.update(args)
        elif path_kwargs:
            # to handle sdss_access path kwargs and versioning issues
            # TODO cleanup version handling to better handle path_kwarg inputs
            args = path_kwargs.copy()
            missing = set(cls.path.lookup_keys(path_name)) - set(args.keys())
            if version:
                if isinstance(version, six.string_types):
                    version_kwarg = dict.fromkeys(missing, version)
                else:
                    version_kwarg = version.__dict__
                args.update(version_kwarg)
            kwargs.update(args)
        else:
            raise ValueError('no example string or sdss_access path kwargs found.  Cannot construct object.')

        return cls(path_name, **kwargs)

    def compute_changelog(self, otherfile=None):

        assert otherfile is not None, ('You must specify another file to view '
                                       'the changlog with this file.  Otherwise '
                                       'use the changlog from the datamodel to '
                                       'see the full changelog')

        if not self._changes:
            name = str(self.fullpath)
            self._changes = compute_diff(name, otherfile, change='fits')

        return self._changes


class Fits(FileObject):

    def __init__(self, inputs=None, filename=None, **kwargs):
        super(Fits, self).__init__(inputs=inputs, filename=filename, **kwargs)

        # open the file if it exists
        if self.file_exists:
            self._read_file()

    def __repr__(self):
        return (f'Fits(name={self.filename}, version={self.version or "unknown"}, '
                f'exists={self.file_exists}, loaded={self.loaded})')
    
    def _read_file(self):
        ''' Open and read the FITS file '''

        try:
            hdulist = fits.open(self.fullpath)
        except Exception:
            raise ValueError('Filename does not appear to be a FITS file')
        else:
            self.hdulist = hdulist
            self.hdulist.verify()
            self._get_info()
            self.loaded = True
    
    def _get_info(self):
        if not self._info:
            s = StringIO()
            self.hdulist.info(output=s)
            s.seek(0)
            self._info = ''.join(s.readlines())
            s.close()

    def info(self):
        ''' prints the info from the file '''
        print(self._info)

    def load(self):
        if not self.loaded and self.file_exists:
            self._read_file()


class Catalog(FileObject):

    def __init__(self, inputs=None, filename=None, **kwargs):
        super(Catalog, self).__init__(inputs=inputs, filename=filename, **kwargs)

        # open the file if it exists
        if self.file_exists:
            self._read_file()

    def __repr__(self):
        return (f'Catalog(name={self.filename}, version={self.version or "unknown"}, '
                f'exists={self.file_exists}, loaded={self.loaded})')

    def _read_file(self):
        ''' Open and read the catalog file '''

        try:
            table = astropy_ascii.read(self.fullpath)
        except Exception:
            raise ValueError('Filename does not appear to be a FITS file')
        else:
            self.table = table
            self._get_info()
            self._get_stats()
            self.loaded = True

    def _get_info(self):
        if not self._info:
            s = StringIO()
            self.table.info(out=s)
            s.seek(0)
            self._info = ''.join(s.readlines())
            s.close()

    def _get_stats(self):
        if not self._stats:
            s = StringIO()
            self.table.info('stats', out=s)
            s.seek(0)
            self._stats = ''.join(s.readlines())
            s.close()
            
    def info(self, option=None):
        ''' prints the info from the file '''
        if option == 'stats':
            print(self._stats)
        else:
            print(self._info)

    def load(self):
        if not self.loaded and self.file_exists:
            self._read_file()
