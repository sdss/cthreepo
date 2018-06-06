# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-05-30 22:08:31
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-06-01 11:28:32

from __future__ import print_function, division, absolute_import

from cthreepo.core.datamodel import DataModelList, BaseDataModel
from cthreepo.core.objects import DataCubeList, SpectrumList


class DRPDataModel(BaseDataModel):
    """A class representing a DRP datamodel, with datacubes and spectra, etc."""

    def __init__(self, release, aliases=[], bitmasks=None, datacubes=[], spectra=[]):

        super(DRPDataModel, self).__init__(release, aliases=aliases, bitmasks=bitmasks)

        self.datacubes = DataCubeList(datacubes, parent=self)
        self.spectra = SpectrumList(spectra, parent=self)

    def __repr__(self):

        return ('<DRPDataModel release={0!r}, n_datacubes={1}, n_spectra={2}>'
                .format(self.release, len(self.datacubes), len(self.spectra)))

    def __eq__(self, value):
        """Uses fuzzywuzzy to return the closest property match."""

        datacube_names = [datacube.name for datacube in self.datacubes]
        spectrum_names = [spectrum.name for spectrum in self.spectra]

        if value in datacube_names:
            return self.datacubes[datacube_names.index(value)]
        elif value in spectrum_names:
            return self.spectra[spectrum_names.index(value)]

        try:
            datacube_best_match = self.datacubes[value]
        except ValueError:
            datacube_best_match = None

        try:
            spectrum_best_match = self.spectra[value]
        except ValueError:
            spectrum_best_match = None

        if ((datacube_best_match is None and spectrum_best_match is None) or
                (datacube_best_match is not None and spectrum_best_match is not None)):
            raise ValueError('too ambiguous input {!r}'.format(value))
        elif datacube_best_match is not None:
            return datacube_best_match
        elif spectrum_best_match is not None:
            return spectrum_best_match


class DRPDataModelList(DataModelList):
    """A dictionary of DRP datamodels."""

    base = {'DRPDataModel': DRPDataModel}

