# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-06-01 14:19:23
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-06-13 00:49:30

from __future__ import print_function, division, absolute_import
from astropy import units as u

from cthreepo.core.units import spaxel_unit
from cthreepo.core.objects import DataCube, Spectrum
from cthreepo.core.mixins import DbMixin, FitsMixin
from cthreepo.datamodels.manga.drp.base import DRPDataModel, DRPDataModelList
from cthreepo.datamodels.manga.maskbit import get_maskbits

db_schema = 'mangadb.mangadatadb'


class MangaDataCube(DataCube, DbMixin, FitsMixin):
    pass


class MangaSpectrum(Spectrum, DbMixin, FitsMixin):
    pass


class TestSpectrum(Spectrum, DbMixin):
    pass


class TestFSpectrum(Spectrum, FitsMixin):
    pass


MPL4_datacubes = [
    MangaDataCube('flux', extension_name='FLUX', extension_wave='WAVE', extension_ivar='IVAR',
                  extension_mask='MASK', unit=u.erg / u.s / (u.cm ** 2) / u.Angstrom / spaxel_unit,
                  scale=1e-17, formats={'string': 'Flux'},
                  description='3D rectified cube', db_full=db_schema + '.spaxel.flux')
]

MPL4_spectra = [
    MangaSpectrum('spectral_resolution', extension_name='SPECRES', extension_wave='WAVE', extension_std='SPECRESD',
                  unit=u.Angstrom, scale=1, formats={'string': 'Median spectral resolution'},
                  description='Median spectral resolution as a function of wavelength '
                              'for the fibers in this IFU', db_full=db_schema + '.cube.specres')
]

MPL6_datacubes = [
    MangaDataCube('dispersion', extension_name='DISP', extension_wave='WAVE', extension_ivar=None,
                  extension_mask='MASK', unit=u.Angstrom, db_full=db_schema + '.spaxel.disp',
                  scale=1, formats={'string': 'Dispersion'},
                  description='Broadened dispersion solution (1sigma LSF)'),
    MangaDataCube('dispersion_prepixel', extension_name='PREDISP', extension_wave='WAVE', extension_ivar=None,
                  extension_mask='MASK', unit=u.Angstrom, db_full=db_schema + '.spaxel.predisp',
                  scale=1, formats={'string': 'Dispersion pre-pixel'},
                  description='Broadened pre-pixel dispersion solution (1sigma LSF)')

]

MPL6_spectra = [
    MangaSpectrum('spectral_resolution_prepixel', extension_name='PRESPECRES', extension_wave='WAVE',
                  extension_std='PRESPECRESD', unit=u.Angstrom, scale=1, db_full=db_schema + '.cube.prespecres',
                  formats={'string': 'Median spectral resolution pre-pixel'},
                  description='Median pre-pixel spectral resolution as a function of '
                              'wavelength for the fibers in this IFU'),
]


MPL4 = DRPDataModel('MPL-4', aliases=['MPL4', 'v1_5_1'],
                    datacubes=MPL4_datacubes,
                    spectra=MPL4_spectra,
                    bitmasks=get_maskbits('MPL-4'))

MPL5 = DRPDataModel('MPL-5', aliases=['MPL5', 'v2_0_1'],
                    datacubes=MPL4_datacubes,
                    spectra=MPL4_spectra,
                    bitmasks=get_maskbits('MPL-5'))

MPL6 = DRPDataModel('MPL-6', aliases=['MPL6', 'v2_3_1'],
                    datacubes=MPL4_datacubes + MPL6_datacubes,
                    spectra=MPL4_spectra + MPL6_spectra,
                    bitmasks=get_maskbits('MPL-6'))

MPL7 = DRPDataModel('MPL-7', aliases=['MPL7', 'v2_4_3', 'DR15'],
                    datacubes=MPL4_datacubes + MPL6_datacubes,
                    spectra=MPL4_spectra + MPL6_spectra,
                    bitmasks=get_maskbits('MPL-7'))

datamodel = DRPDataModelList([MPL4, MPL5, MPL6, MPL7])
