# !/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Filename: fits.py
# Project: core
# Author: Brian Cherinka
# Created: Saturday, 1st December 2018 6:20:08 am
# License: <<licensename>>
# Copyright (c) 2018 Brian Cherinka
# Last Modified: Monday, 1st April 2019 2:31:46 pm
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import
import os
import six
import pathlib
from io import StringIO
from astropy.io import fits
from sdss_access.path import Path
from cthreepo.utils.general import compute_changelog, ChangeLog, FitsDiff


class Fits(object):

    def __init__(self, inputs=None, filename=None, **kwargs):
        self.path = Path()
        self.filename = filename
        self.path_name = kwargs.pop('path_name', None)
        self._info = None
        
        # check inputs and produce filename
        self._determine_inputs(inputs, **kwargs)
        self._parse_filename()
        
        # open the file
        self._read_file()

    def __repr__(self):
        return (f'Fits(name={self.filename}, exists={self.file_exists})')
    
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
        if not self.file_exists:
            raise NameError('{0} not a valid file'.format(self.fullpath))

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

    @classmethod
    def from_example(cls, example):
        ''' Instantiates a FITS from an example file'''

        path = pathlib.Path(os.path.expandvars('$SAS_BASE_DIR')) / example
        if not path.is_file():
            raise ValueError(f'Example provided does seem to exist!  Check again.')
        return cls(path)

    
    # def __init__(self, input=None, filename=None, **kwargs):
    #     self.path = Path()
    #     self.filename = filename
    #     self._info = None
    #     self._determine_inputs(input, **kwargs)
    #     self._parse_filename(filename)
    #     self._changes = None

    #     # open the file
    #     self._read_file()
            
    # def __repr__(self):
    #     return ('Fits(name={name}, exists={exists})'.format(name=self.filename, 
    #             exists=self.file_exists))

    # def _determine_inputs(self, input, **kwargs):
    #     ''' Determine the input '''

    #     # no input at all
    #     if not input and not hasattr(self, 'pathname'):
    #         raise ValueError('No input has been provided to determine a valid file')

    #     assert isinstance(input, six.string_types), 'input must be a string'

    #     # check if input is an sdss_access Path
    #     if input in self.path.lookup_names():
    #         keys = self.path.lookup_keys(input)
    #         missing = set(keys) - set(kwargs.keys())
    #         if missing:
    #             raise KeyError('Input sdss_access name missing necessary kwargs: {0}'.format(', '.join(missing)))
            
    #         # get the full path
    #         self.filename = self.path.full(input, **kwargs)
    #     else:
    #         # assume it is a filename
    #         self.filename = input

    # def _check_for_example(self, filename):
    #     ''' Checks for example file on class attribute '''

    #     filename = filename or self.filename
    #     if filename:
    #         return filename

    #     if hasattr(self, 'example'):
    #         return os.path.join(os.environ.get("SAS_BASE_DIR"), self.example)
    #     else:
    #         raise NameError('No input or filename could be found')

    # def _parse_filename(self, filename):
    #     ''' Parse a filename into components '''

    #     filename = self._check_for_example(filename)
    #     self.filepath = os.path.dirname(filename)
    #     self.filename = os.path.basename(filename)
    #     self.fullpath = os.path.join(self.filepath, self.filename)

    #     self.file_exists = self.path.exists('', full=self.fullpath)
    #     if not self.file_exists:
    #         raise NameError('{0} not a valid file'.format(self.fullpath))

    # def _read_file(self):
    #     ''' Open and read the FITS file '''

    #     try:
    #         hdulist = fits.open(self.fullpath)
    #     except Exception:
    #         raise ValueError('Filename does not appear to be a FITS file')
    #     else:
    #         self.hdulist = hdulist
    #         self.hdulist.verify()
    #         self._get_info()

    # def _get_info(self):
    #     if not self._info:
    #         s = StringIO()
    #         self.hdulist.info(output=s)
    #         s.seek(0)
    #         self._info = ''.join(s.readlines())
    #         s.close()

    # def info(self):
    #     ''' prints the info from the file '''
    #     print(self._info)

    # @classmethod
    # def from_example(cls):
    #     ''' Instantiates a FITS from an example file'''
        
    #     if hasattr(cls, 'example'):
    #         path = os.path.join(os.environ.get("SAS_BASE_DIR"), cls.example)
    #         return cls(path)

    # @property
    # def changelog(self):
    #     if not self._changes:
    #         self._changes = compute_changelog(self, change='fits')
    #     return self._changes

