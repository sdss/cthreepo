# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-06-18 17:23:07
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-09-20 18:51:08

from __future__ import print_function, division, absolute_import
from cthreepo.core.datamodel import DataModelList, BaseDataModel
from sdss_access.path import Path

path = Path()
fullfile = path.templates['allwise']


class AllWiseDataModel(BaseDataModel):

    def __repr__(self):
        return '<AllWiseDataModel release={0}, n_properties={1}>'.format(self.release, len(self.properties))

    def __eq__(self, value):

        prop_names = [prop.name for prop in self.properties]

        if value in prop_names:
            return self.properties[prop_names.index(value)]

        try:
            prop_best_match = self.properties[value]
        except ValueError:
            prop_best_match = None

        if prop_best_match is None:
            raise ValueError('too ambiguous input {!r}'.format(value))
        else:
            return prop_best_match

        return prop_best_match


class AllWiseDataModelList(DataModelList):
    """A dictionary of DRP datamodels."""

    base = {'AllWiseDataModel': AllWiseDataModel}


awdm = AllWiseDataModel.load_from_sql('/Users/Brian/Work/python/sdss/catalogdb_allwise.sql', db='sdss5db',
                                      from_file='catalog')


datamodel = AllWiseDataModelList([awdm])

