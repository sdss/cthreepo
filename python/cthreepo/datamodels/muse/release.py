# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-06-08 15:11:48
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-06-08 19:40:25

from __future__ import print_function, division, absolute_import
from astropy import units as u

from cthreepo.core.units import spaxel_unit
from cthreepo.core.objects import DataCube
from cthreepo.core.mixins import FitsMixin
from cthreepo.datamodels.muse.base import MuseDataModel, MuseDataModelList


class MuseDataCube(DataCube, FitsMixin):
    pass


muse_datacubes = [
    MuseDataCube('flux', extension_name='FLUX', extension_std='STAT',
                 unit=u.erg / u.s / (u.cm ** 2) / u.Angstrom / spaxel_unit,
                 scale=1e-20, formats={'string': 'Flux'},
                 description='3D rectified cube')
]

DR1 = MuseDataModel('DR1', aliases=['DR1', 'v1_0_0'], datacubes=muse_datacubes)

datamodel = MuseDataModelList([DR1])

