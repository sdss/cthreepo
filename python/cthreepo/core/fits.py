# !/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Filename: fits.py
# Project: core
# Author: Brian Cherinka
# Created: Saturday, 1st December 2018 6:20:08 am
# License: <<licensename>>
# Copyright (c) 2018 Brian Cherinka
# Last Modified: Friday, 12th April 2019 9:58:58 am
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import
import os
import six
import pathlib
from io import StringIO
from astropy.io import fits
from sdss_access.path import Path
from cthreepo.utils.general import compute_change


class BaseObject(object):

    def __init__(self, product=None, version=None, **kwargs):
        self.product = product
        self.version = version
        
    def __repr__(self):
        return f'<Object(name={self.product},version={self.version})>'


class FileObject(BaseObject):
    
    def __init__(self, inputs=None, filename=None, **kwargs):
        super(FileObject, self).__init__(self, **kwargs)
        self.path = Path()
        self.filename = filename
        self.path_name = kwargs.pop('path_name', None)
        self.parent = kwargs.pop('parent', None)
        self.version = kwargs.pop('version', None)
        self._info = None
        self._changes = None

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

    @classmethod
    def from_example(cls, example, version=None):
        ''' Instantiates a file from an example filepath'''

        path = pathlib.Path(os.path.expandvars('$SAS_BASE_DIR')) / example
        # if not path.is_file():
        #     raise ValueError(f'Example provided does seem to exist!  Check again.')
        return cls(path, version=version)

    def compute_changelog(self, otherfile=None):

        assert otherfile is not None, ('You must specify another file to view '
                                       'the changlog with this file.  Otherise '
                                       'use the changlog from the datamodel to '
                                       'see the full changelog')

        if not self._changes:
            name = str(self.fullpath)
            self._changes = compute_change(name, otherfile, change='fits')

        return self._changes


class Fits(FileObject):

    def __init__(self, inputs=None, filename=None, **kwargs):
        super(Fits, self).__init__(inputs=inputs, filename=filename, **kwargs)

        # open the file if it exists
        if self.file_exists:
            self._read_file()

    def __repr__(self):
        return (f'Fits(name={self.filename}, version={self.version or "unknown"}, '
                f'exists={self.file_exists})')
    
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

