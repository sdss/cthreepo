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

# define the datamodel path to here
here = pathlib.Path(__file__).resolve()
dm_idx = str(here).find('datamodel')
segment = str(here)[dm_idx:].rsplit('/', 1)[0]

# this is an example of reading in and instantiating the datamodel objects for manga
datamodel_dir = os.environ['CTHREEPO_DIR'] / pathlib.Path(segment)
files = [i for i in datamodel_dir.rglob('*.yaml') if i.stem not in ['datamodel', 'products']]

# create the datamodel structures, e.g. bintypes, templates, versions, etc
for file in files:
    data = read_yaml(file)
    locals()[file.stem] = generate_models(data)
