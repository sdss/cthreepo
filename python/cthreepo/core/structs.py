# !/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Filename: structs.py
# Project: core
# Author: Brian Cherinka
# Created: Monday, 18th March 2019 9:40:38 am
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2019 Brian Cherinka
# Last Modified: Wednesday, 15th May 2019 2:42:00 pm
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import
from collections import OrderedDict

import six
import inspect

from fuzzywuzzy import fuzz as fuzz_fuzz
from fuzzywuzzy import process as fuzz_proc


def get_best_fuzzy(value, choices, min_score=75, scorer=fuzz_fuzz.WRatio, return_score=False):
    """Returns the best match in a list of choices using fuzzywuzzy."""

    if not isinstance(value, six.string_types):
        raise ValueError('invalid value. Must be a string.')

    if len(value) < 3:
        raise ValueError('your fuzzy search value must be at least three characters long.')

    # If the value contains _ivar or _mask this is probably and incorrect use
    # of the fuzzy feature. We raise an error.
    if '_ivar' in value:
        raise ValueError('_ivar not allowd in search value.')
    elif '_mask' in value:
        raise ValueError('_mask not allowd in search value.')

    bests = fuzz_proc.extractBests(value, choices, scorer=scorer, score_cutoff=min_score)

    if len(bests) == 0:
        best = None
    elif len(bests) == 1:
        best = bests[0]
    else:
        if bests[0][1] == bests[1][1]:
            best = None
        else:
            best = bests[0]

    if best is None:
        raise ValueError('cannot find a good match for {0!r}. '
                         'Your input value is too ambiguous.'.format(value))

    return best if return_score else best[0]


class FuzzyDict(OrderedDict):
    """A dotable dictionary that uses fuzzywuzzy to select the key."""

    def __getattr__(self, value):
        if '__' in value:
            return super(FuzzyDict, self).__getattr__(value)
        return self.__getitem__(value)

    def __getitem__(self, value):

        if not isinstance(value, six.string_types):
            return self.values()[value]

        if value in self.keys():
            return dict.__getitem__(self, value)

        best = get_best_fuzzy(value, self.keys())

        return dict.__getitem__(self, best)

    def __dir__(self):

        return list(self.keys())


class FuzzyList(list):
    """A list that uses fuzzywuzzy to select the item.
    Parameters:
        the_list (list):
            The list on which we will do fuzzy searching.
        use_fuzzy (function):
            A function that will be used to perform the fuzzy selection
    """

    def __init__(self, the_list, use_fuzzy=None):

        self.use_fuzzy = use_fuzzy if use_fuzzy else get_best_fuzzy

        list.__init__(self, the_list)

    def mapper(self, item):
        """The function that maps each item to the querable string."""

        return str(item)

    def __eq__(self, value):

        self_values = [self.mapper(item) for item in self]

        try:
            best = self.use_fuzzy(value, self_values)
        except ValueError:
            # Second pass, using underscores.
            best = self.use_fuzzy(value.replace(' ', '_'), self_values)

        return self[self_values.index(best)]

    def __contains__(self, value):

        if not isinstance(value, six.string_types):
            return super(FuzzyList, self).__contains__(value)

        try:
            self.__eq__(value)
            return True
        except ValueError:
            return False

    def __getitem__(self, value):

        if isinstance(value, six.string_types):
            return self == value
        else:
            return list.__getitem__(self, value)

    def __getattr__(self, value):

        self_values = [super(FuzzyList, self).__getattribute__('mapper')(item)
                       for item in self]

        if value in self_values:
            return self[value]

        return super(FuzzyList, self).__getattribute__(value)

    def __dir__(self):
        ''' override the dir to only show new methods and items in the list '''
        # get all original members of the FuzzyList
        class_members = set(list(zip(*inspect.getmembers(self.__class__)))[0])
        # subtract out members from original list object
        members = list(set(class_members) - set(dir(list)))
        # get parameters in list
        params = [self.mapper(item) for item in self]
        return members + params


class OrderedDefaultDict(FuzzyDict):

    def __init__(self, default_factory=None, *args, **kwargs):
        OrderedDict.__init__(self, *args, **kwargs)
        self.default_factory = default_factory

    def __missing__(self, key):
        result = self[key] = self.default_factory()
        return result
