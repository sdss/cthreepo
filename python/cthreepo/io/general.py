# !/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Filename: general.py
# Project: utils
# Author: Brian Cherinka
# Created: Saturday, 22nd December 2018 1:58:01 pm
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2018 Brian Cherinka
# Last Modified: Wednesday, 22nd May 2019 4:06:00 pm
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import
import six
import abc
from io import StringIO
from astropy.io import fits, ascii as astropy_ascii
from astropy.table import Table
from fuzzy_types.fuzzy import FuzzyList
from cthreepo import log
import matplotlib
try:
    from astropy.utils.diff import report_diff_values
except ImportError:
    report_diff_values = None


def settex():
    ''' Configure matplotlib settings to use full latex syntax '''
    usetex = matplotlib.rcParams['text.usetex']
    if not usetex:
        matplotlib.rc('text', usetex=True)


def _indent(s):
    ''' indent a string '''
    return ' ' * 4 + s


class ChangeLog(FuzzyList):
    ''' Class that holds the change log for a FITS file type

    TODO - improve the repr and Fuzzylist
    TODO - fix the dir to contain everything

    '''

    def __init__(self, the_list, **kwargs):
        super(ChangeLog, self).__init__(the_list, **kwargs)

    def mapper(self, item):
        return 'diff_' + '_'.join(item.versions).lower()

    def generate_report(self, split=None, insert=True):
        ''' generate a string report '''
        full_report = [] if split else ''
        for item in self:
            lines = item.report(split=split)
            if split:
                if insert:
                    full_report.append('---------------------')
                full_report.extend(lines)
            else:
                if insert:
                    full_report += '\n---------------------\n'
                full_report += lines
        return full_report


class FileDiff(abc.ABC, object):
    ''' Class that holds the difference between two files '''

    def __init__(self, file1, file2, versions=None, diff_type=None):
        self.diff_type = diff_type
        self.versions = versions or ['A', 'B']
        self.file1 = str(file1)
        self.file2 = str(file2)

    def __repr__(self):
        return f"<FileDiff (versions='{','.join(self.versions)}', diff_type='{self.diff_type}')>"

    @abc.abstractclassmethod
    def report(self):
        ''' Print a report '''


class FitsDiff(FileDiff):
    ''' Difference in two FITS files '''

    def __init__(self, file1, file2, full=None, versions=None):
        super(FitsDiff, self).__init__(file1, file2, diff_type='fits', versions=versions)

        # get the HDU lists
        self.hdulist = self._check_fits(self.file1)
        self.hdulist2 = self._check_fits(self.file2)

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

    @staticmethod
    def _check_fits(data):
        ''' Check the input for proper FITS file name or object '''
        if not isinstance(data, fits.hdu.hdulist.HDUList):
            assert isinstance(
                data, six.string_types), 'input must be string filename or a FITS HDUList '
            assert '.fits' in data, 'No .fits suffix found.  Is this a proper FITS file?'
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


class CatalogDiff(FileDiff):
    ''' Difference between two catalog files '''

    def __init__(self, file1, file2, full=None, versions=None):
        super(CatalogDiff, self).__init__(file1, file2, diff_type='catalog', versions=versions)

        # get the catalog tables
        self.table = self._check_catalog(self.file1)
        self.table2 = self._check_catalog(self.file2)

        # Table row differences
        n_rows = len(self.table)
        n_row2s = len(self.table2)
        self.delta_rows = abs(n_rows - n_row2s)
        self.n_row_diffs = (n_rows, n_row2s)

        # Table column differences
        col_names = self.table.colnames
        col2_names = self.table2.colnames
        self.delta_cols = len(set(col_names) ^ set(col2_names))
        self.added_cols = list(set(col_names) - set(col2_names))
        self.removed_cols = list(set(col2_names) - set(col_names))

        # get the full report
        self.astropy_diff = self.get_astropy_diff() if full else None

    @staticmethod
    def _check_catalog(data):
        ''' Check the input for proper Catalog file name or object '''
        if not isinstance(data, Table):
            assert isinstance(
                data, six.string_types), 'input must be string filename or a Table '
            assert '.csv' in data, 'No .csv suffix found.  Is this a proper catalog file?'
            data = astropy_ascii.read(data)
        return data

    def get_astropy_diff(self):
        report = None
        if report_diff_values:
            s = StringIO()
            same = report_diff_values(self.table, self.table2, s)
            if not same:
                s.seek(0)
                report = ''.join(s.readlines())
                s.close()
        return report

    def report(self, split=None, full=None):
        ''' Print the Catalog Different report '''

        diffreport = 'Version: {0} to {1}\n'.format(*self.versions)

        # print the column differences
        diffreport += 'Changes in row number: {0}\n'.format(self.delta_rows)
        diffreport += 'Changes in column number: {0}\n'.format(self.delta_cols)
        if self.delta_cols > 0:
            diffreport += 'Added Columns: {0}\n'.format(', '.join(self.added_cols))
            diffreport += 'Removed Columns: {0}\n\n'.format(', '.join(self.removed_cols))

        # print the Astropy Table difference report
        if self.astropy_diff or full:
            fullreport = self.astropy_diff or self.get_astropy_diff()
            diffreport += '\nFull Report:\n'
            diffreport += fullreport

        # split the report
        if split:
            diffreport = diffreport.split('\n')

        return diffreport


def compute_diff(oldfile, otherfile, change='fits', versions=None):
    ''' new changelog - produce a single changelog between two files '''

    import pathlib

    # check old filename
    name = pathlib.Path(oldfile)
    assert name.exists(), f'{name} must exist'

    # check other filename
    other_name = pathlib.Path(otherfile)
    assert other_name.exists(), f'{otherfile} must exist'

    # check the type of file
    if change == 'fits':
        diffobj = FitsDiff
    elif change == 'catalog':
        diffobj = CatalogDiff

    # compute file difference
    fd = diffobj(name, other_name, versions=versions)

    return fd


def compute_changelog(items, change=None):
    zipped = list(zip(items[:-1], items[1:]))
    fds = []
    for item in zipped:
        v1 = str(item[0].version)
        v2 = str(item[1].version)
        exist1 = item[0].file_exists
        exist2 = item[1].file_exists
        if exist1 and exist2:
            fds.append(compute_diff(str(item[0].fullpath), str(
                item[1].fullpath), versions=[v1, v2], change=change))
        else:
            log.warning('One or more files does not exist.  Cannot compute changelog '
                        f'for this changeset. Version {v1}: exists={exist1}; '
                        f'Version {v2}: exists={exist2}')
    return ChangeLog(fds)
