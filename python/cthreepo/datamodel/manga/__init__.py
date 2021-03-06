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
from cthreepo.datamodel import DataModel
from cthreepo.datamodel.manga.mixins import Channel


class MaNGADataModel(DataModel):
    survey = 'manga'
    _mixed_models = {'channels': Channel}


# create the manga datamodel
dm = MaNGADataModel()


