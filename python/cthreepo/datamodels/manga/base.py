# !/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Filename: base.py
# Project: manga
# Author: Brian Cherinka
# Created: Saturday, 1st December 2018 9:03:33 am
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2018 Brian Cherinka
# Last Modified: Sunday, 13th January 2019 8:28:28 pm
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import

from cthreepo.core.fits import Fits

versions = {'DR15': ('v2_4_3', '2.2.1'),
            'MPL-7': ('v2_4_3', '2.2.1'),
            'MPL-6': ('v2_3_1', '2.1.3'),
            'MPL-5': ('v2_0_1', '2.0.2'),
            'MPL-4': ('v1_5_1', '1.1.1')}


class LogCube(Fits):
    """ A MaNGA DataCube

    This is 3d spectral datacube, with two spatial dimensions and one spectral dimension.
    
    The MaNGA DRP provides regularly-gridded cubes (with both logarithmic and linear wavelength 
    solutions) that combine information from all exposures of a given galaxy.  The cubes are 
    three-dimensional arrays in which the first and second dimensions are spatial (with regular 0.5 
    arcsec square spaxels) and the third dimension represents wavelength.

    """
    pathname = 'mangacube'
    name = "LOGCUBE"
    example = 'mangawork/manga/spectro/redux/v2_4_3/8485/stack/manga-8485-1901-LOGCUBE.fits.gz'
    versions = versions.copy()
    public = False


class LogRSS(Fits):
    """ A MaNGA Row-Stacked spectra

    This is row-stacked spectra

    """
    pathname = 'mangarss'
    name = "LOGRSS"
    example = 'mangawork/manga/spectro/redux/v2_4_3/8485/stack/manga-8485-1901-LOGRSS.fits.gz'
    versions = versions.copy()
    public = False


class Maps(Fits):
    """ A MaNGA Maps object

    This is a DAP MAPS object

    """
    name = "MAPS"
    example = ('mangawork/manga/spectro/analysis/v2_4_3/2.2.1/HYB10-GAU-MILESHC/8485/1901'
               '/manga-8485-1901-MAPS-HYB10-GAU-MILESHC.fits.gz')
    versions = {k: v for k, v in versions.items() if k != 'MPL-4'}
    public = False
