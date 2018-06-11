# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-06-08 19:38:46
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-06-08 19:43:00

from __future__ import print_function, division, absolute_import
from astropy import units as u


# This file defines any custom Units used by multiple datamodels

spaxel_unit = u.Unit('spaxel', represents=u.pixel, doc='A spectral pixel', parse_strict='silent')
