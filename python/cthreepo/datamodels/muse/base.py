# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-06-08 15:03:25
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-06-08 15:07:15

from __future__ import print_function, division, absolute_import

from cthreepo.core.datamodel import DataModelList, BaseDataModel
from cthreepo.core.lists import DataCubeList


class MuseDataModel(BaseDataModel):
    """A class representing a Muse datamodel, with datacubes and spectra, etc."""

    def __init__(self, release, aliases=[], bitmasks=None, datacubes=[], spectra=[]):

        super(MuseDataModel, self).__init__(release, aliases=aliases, bitmasks=bitmasks)

        self.datacubes = DataCubeList(datacubes, parent=self)

    def __repr__(self):

        return ('<MuseDataModel release={0!r}, n_datacubes={1}>'
                .format(self.release, len(self.datacubes)))

    def __eq__(self, value):
        """Uses fuzzywuzzy to return the closest property match."""

        datacube_names = [datacube.name for datacube in self.datacubes]

        if value in datacube_names:
            return self.datacubes[datacube_names.index(value)]

        try:
            datacube_best_match = self.datacubes[value]
        except ValueError:
            datacube_best_match = None

        if datacube_best_match is None:
            raise ValueError('too ambiguous input {!r}'.format(value))
        elif datacube_best_match is not None:
            return datacube_best_match


class MuseDataModelList(DataModelList):
    """A dictionary of Muse datamodels."""

    base = {'MuseDataModel': MuseDataModel}
