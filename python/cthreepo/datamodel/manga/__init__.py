# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-05-30 18:26:43
# @Last modified by:   Brian
# @Last Modified time: 2018-06-12 01:11:29

from __future__ import print_function, division, absolute_import

import os
import pathlib
from cthreepo.core.objects import generate_models, read_yaml

print(pathlib.Path(__file__).resolve())

# this is an example of reading in and instantiating the bintype datamodel objects
datamodel_dir = os.environ['CTHREEPO_DIR'] / pathlib.Path('datamodel')
files = [i for i in datamodel_dir.rglob('*.yaml') if i.stem not in ['datamodel', 'products']]

data = read_yaml(files[-1])
bintypes = generate_models(data)
