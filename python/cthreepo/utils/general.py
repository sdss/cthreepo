# !/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Filename: general.py
# Project: utils
# Author: Brian Cherinka
# Created: Saturday, 22nd December 2018 1:58:01 pm
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2018 Brian Cherinka
# Last Modified: Monday, 13th May 2019 9:47:19 pm
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import
import six
import abc
from astropy.io import fits
from cthreepo.core.structs import FuzzyList
from cthreepo.misc import log


def _indent(s):
    ''' indent a string '''
    return ' ' * 4 + s


def _check_fits(data):
    ''' Check the input for proper FITS file name or object '''
    if not isinstance(data, fits.hdu.hdulist.HDUList):
        assert isinstance(data, six.string_types), 'input must be string filename or a FITS HDUList '
        data = fits.open(data)
    return data


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
        pass


class FitsDiff(FileDiff):
    ''' Difference in two FITS files '''

    def __init__(self, file1, file2, full=None, versions=None):
        super(FitsDiff, self).__init__(file1, file2, diff_type='fits', versions=versions)

        # get the HDU lists
        self.hdulist = _check_fits(self.file1)
        self.hdulist2 = _check_fits(self.file2)

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


# def _replace_version(name, version):
#     ''' Check if a version is a string, or tuple of versions '''

#     # check version format
#     islist = isinstance(version, (list, tuple))
#     allstrings = all([isinstance(v, six.string_types) for v in sum(version, ())])
#     assert islist and allstrings, 'Version must be in the proper format'

#     # do string replacement
#     for ver in version:
#         oldv, newv = ver
#         name = name.replace(oldv, newv)

#     return name


# def _format_versions(versions):
#     ''' orient the versions into the proper format '''

#     if isinstance(versions, dict):
#         versions = versions.values()
#     versions = list(versions)
#     # wrap string version in a tuple
#     versions = [(v,) if isinstance(v, six.string_types) else v for v in versions]
#     # create list of tuples of (v1, v2)
#     versions = list(zip(versions[:-1], versions[1:]))
#     # reformat the versions into tuples of by version column
#     versions = [tuple(zip(*v)) for v in versions]
#     return versions


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

    # compute file difference
    fd = diffobj(name, other_name, versions=versions)

    return fd


def compute_changelog(items):
    zipped = list(zip(items[:-1], items[1:]))
    fds = []
    for item in zipped:
        v1 = str(item[0].version)
        v2 = str(item[1].version)
        exist1 = item[0].file_exists
        exist2 = item[1].file_exists
        if exist1 and exist2:
            fds.append(compute_diff(str(item[0].fullpath), str(
                item[1].fullpath), versions=[v1, v2]))
        else:
            log.warning('One or more files does not exist.  Cannot compute changelog '
                        f'for this changeset. Version {v1}: exists={exist1}; '
                        f'Version {v2}: exists={exist2}')
    return ChangeLog(fds)

# def compute_changelog(obj, change='fits'):
#     ''' compute a changelog for all available versions of the FITS '''

#     # check if object has any versions set
#     if not hasattr(obj, 'versions'):
#         print('No versions found.  Cannot compute changelog')
#         return None

#     # check the type of file
#     if change == 'fits':
#         diffobj = FitsDiff

#     name = obj.fullpath
#     fds = []

#     # reverse the releases
#     rev = {v: k for k, v in obj.versions.items()}
#     # reformat the versions
#     versions = _format_versions(obj.versions.values())

#     for vers in versions:
#         rel1, rel2 = [rev[v] for v in list(zip(*vers))]
#         new_name = _replace_version(name, vers)
#         try:
#             fd = diffobj(name, new_name, versions=[rel1, rel2])
#         except FileNotFoundError:
#             print(f'No file found for {new_name}')
#         else:
#             name = new_name
#             fds.append(fd)

#     # for rel in releases[:-1]:
#     #     idx = releases.index(rel)
#     #     v1 = obj.versions[rel]
#     #     v2 = obj.versions[releases[idx + 1]]


#     #     name1 = name
#     #     name2 = (name1.replace(v1, v2))
#     #     fd = diffobj(name1, name2, versions=[v1, v2])
#     #     name = name2
#     #     fds.append(fd)

#     return ChangeLog(fds)


# def reverse_parse(pattern, template):
#     ''' reverse parse an example filepath into sdss_access keyword components '''

#     import os
#     import re
#     # expand the environment variable
#     pattern = os.path.expandvars(pattern)
#     # handle special functions; perform a drop in replacement
#     if re.match('%spectrodir', pattern):
#         pattern = re.sub('%spectrodir', os.environ['BOSS_SPECTRO_REDUX'], pattern)
#     elif re.search('%platedir', pattern):
#         pattern = re.sub('%platedir', '(.*)/{plateid:0>6}', pattern)
#     elif re.search('%definitiondir', pattern):
#         pattern = re.sub('%definitiondir', '{designid:0>6}', pattern)
#     if re.search('%plateid6', pattern):
#         pattern = re.sub('%plateid6', '{plateid:0>6}', pattern)
        
#     # check if pattern has any brackets
#     haskwargs = re.search('[{}]', pattern)
#     if not haskwargs:
#         return None

#     # escape the envvar $ and any dots
#     subpatt = pattern.replace('$', '\\$').replace('.', '\\.')
#     # define search pattern; replace all template keywords with regex "(.*)" group
#     research = re.sub('{(.*?)}', '(.*)', subpatt)
#     # look for matches in pattern and template
#     pmatch = re.search(research, pattern)
#     tmatch = re.search(research, template)
    
#     path_dict = {}
#     # if template match extract keys and values from the match groups
#     if pmatch and tmatch:
#         values = tmatch.groups(0)
#         keys = pmatch.groups(0)
#         assert len(keys) == len(values), 'pattern and template matches must have same length'
#         parts = zip(keys, values)
#         # parse into dictionary
#         for part in parts:
#             value = part[1]
#             if re.findall('{(.*?)}', part[0]):
#                 # get the key name inside the brackets
#                 keys = re.findall('{(.*?)}', part[0])
#                 # remove the type : designation
#                 keys = [k.split(':')[0] for k in keys]
#                 # handle double bracket cases
#                 if len(keys) > 1:
#                     if keys[0] == 'dr':
#                         drval = re.match('^DR[1-9][0-9]', value).group(0)
#                         otherval = value.split(drval)[-1]
#                         pdict = {keys[0]: drval, keys[1]: otherval}
#                     elif keys[0] in ['rc', 'br', 'filter', 'camrow']:
#                         pdict = {keys[0]: value[0], keys[1]: value[1:]}
#                     else:
#                         raise ValueError('This case has not yet been accounted for.')
#                     path_dict.update(pdict)
#                 else:
#                     path_dict[keys[0]] = value
#     return path_dict

