# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-06-01 16:28:21
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-06-01 17:49:41

from __future__ import print_function, division, absolute_import

from .base import DAPDataModelList
from .MPL4 import MPL4

# Defines the list of datamodels.
datamodel = DAPDataModelList([MPL4])
