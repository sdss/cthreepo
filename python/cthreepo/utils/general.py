# !/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Filename: general.py
# Project: utils
# Author: Brian Cherinka
# Created: Saturday, 22nd December 2018 1:58:01 pm
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2018 Brian Cherinka
# Last Modified: Sunday, 13th January 2019 8:25:04 pm
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import
import six
import abc
from astropy.io import fits
from cthreepo.core.structs import FuzzyList


def _indent(s):
    ''' indent a string '''
    return ' ' * 4 + s


def _check_fits(data):
    ''' Check the input for proper FITS file name or object '''
    if not isinstance(data, fits.hdu.hdulist.HDUList):
        assert isinstance(data, six.string_types), 'input must be string filename or a FITS HDUList '
        data = fits.open(data)
    return data


def compute_changelog(file1, file2, full=False, versions=['v2', 'v1'], split=None):
    ''' Compute the changelog between two FITS files '''

    # start the diff report
    diffreport = 'Version: {0} to {1}\n'.format(*versions)
    #diffreport += '-' * (len(diffreport) - 1) + '\n'

    hdulist = _check_fits(file1)
    hdulist2 = _check_fits(file2)

    # HDU diffs
    n_hdus = len(hdulist)
    n_hdu2s = len(hdulist2)
    delta_nhdu = abs(n_hdus - n_hdu2s)

    n_hdu_diffs = (n_hdus, n_hdu2s)
    hdu_names = [n.name for n in hdulist]
    hdu2_names = [n.name for n in hdulist2]

    added = list(set(hdu_names) - set(hdu2_names))
    removed = list(set(hdu2_names) - set(hdu_names))

    diffreport += 'Changes in HDU number: {0}\n'.format(delta_nhdu)
    if delta_nhdu > 0:
        diffreport += 'Added HDUs: {0}\n'.format(', '.join(added))
        diffreport += 'Removed HDUs: {0}\n\n'.format(', '.join(removed))

    # primary header diffs
    hd = fits.HDUDiff(hdulist['PRIMARY'], hdulist2['PRIMARY'],
                      ignore_comments=['*'], rtol=10.0)
    diff_keycount = hd.diff_headers.diff_keyword_count
    added_kwargs = removed_kwargs = []
    diffreport += 'Primary Header Differences:\n'
    if diff_keycount:
        added_kwargs = hd.diff_headers.diff_keywords[0]
        removed_kwargs = hd.diff_headers.diff_keywords[1]
        diffreport += 'Added Keywords: {0}\n'.format(', '.join(added_kwargs))
        diffreport += 'Removed Keywords: {0}\n'.format(', '.join(removed_kwargs))

    # use Astropy FITSDiff to compute a complete diff
    if full:
        fd = fits.FITSDiff(hdulist, hdulist2)
        fullreport = fd.report()

        diffreport += '\nFull Report:\n'
        diffreport += fullreport

    # split the report
    if split:
        diffreport = diffreport.split('\n')

    return diffreport


class ChangeLog(FuzzyList):
    ''' Class that holds the change log for a FITS file type 
    
    TODO - improve the repr and Fuzzylist

    '''

    def __init__(self, the_list, **kwargs):
        super(ChangeLog, self).__init__(the_list, **kwargs)


class FileDiff(abc.ABC, object):
    ''' Class that holds the difference between two files '''

    def __init__(self, file1, file2, versions=['v2', 'v1'], diff_type=None):
        self.diff_type = diff_type
        self.versions = versions

    def __repr__(self):
        return f"<FileDiff (versions='{','.join(self.versions)}', diff_type='{self.diff_type}')>"

    @abc.abstractclassmethod
    def report(self):
        ''' Print a report '''
        pass


class FitsDiff(FileDiff):
    ''' Difference in two FITS files '''

    def __init__(self, file1, file2, full=None, versions=None):
        super(FitsDiff, self).__init__(file1, file2, diff_type='fits', versions=versions)

        # get the HDU lists
        self.hdulist = _check_fits(file1)
        self.hdulist2 = _check_fits(file2)

        # HDU differences
        n_hdus = len(self.hdulist)
        n_hdu2s = len(self.hdulist2)
        self.delta_nhdu = abs(n_hdus - n_hdu2s)

        self.n_hdu_diffs = (n_hdus, n_hdu2s)
        hdu_names = [n.name for n in self.hdulist]
        hdu2_names = [n.name for n in self.hdulist2]

        self.added_hdus = list(set(hdu_names) - set(hdu2_names))
        self.removed_hdus = list(set(hdu2_names) - set(hdu_names))

        # PRIMARY header differences
        hd = fits.HDUDiff(self.hdulist['PRIMARY'], self.hdulist2['PRIMARY'],
                          ignore_comments=['*'], rtol=10.0)
        self.diff_keycount = hd.diff_headers.diff_keyword_count
        self.added_kwargs = hd.diff_headers.diff_keywords[0] if self.diff_keycount else []
        self.removed_kwargs = hd.diff_headers.diff_keywords[1] if self.diff_keycount else []

        # get the full report
        self.astropy_diff = self.get_astropy_diff() if full else None

    def _check_fits(self, data):
        ''' Check the input for proper FITS file name or object '''
        if not isinstance(data, fits.hdu.hdulist.HDUList):
            assert isinstance(
                data, six.string_types), 'input must be string filename or a FITS HDUList '
            data = fits.open(data)
        return data

    def get_astropy_diff(self):
        return fits.FITSDiff(self.hdulist, self.hdulist2)

    def report(self, split=None):
        ''' Print the FITS Difference report '''

        diffreport = 'Version: {0} to {1}\n'.format(*self.versions)

        # print the HDU differences
        diffreport += 'Changes in HDU number: {0}\n'.format(self.delta_nhdu)
        if self.delta_nhdu > 0:
            diffreport += 'Added HDUs: {0}\n'.format(', '.join(self.added_hdus))
            diffreport += 'Removed HDUs: {0}\n\n'.format(', '.join(self.removed_hdus))

        # print the PRIMARY header differences
        diffreport += 'Primary Header Differences:\n'
        if self.diff_keycount:
            diffreport += 'Added Keywords: {0}\n'.format(', '.join(self.added_kwargs))
            diffreport += 'Removed Keywords: {0}\n'.format(', '.join(self.removed_kwargs))

        # print the Astropy FITS difference report
        if self.astropy_diff:
            fullreport = self.astropy_diff.report()
            diffreport += '\nFull Report:\n'
            diffreport += fullreport

        # split the report
        if split:
            diffreport = diffreport.split('\n')

        return diffreport

