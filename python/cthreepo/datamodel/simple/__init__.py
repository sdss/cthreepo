# !/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Filename: __init__.py
# Project: simple
# Author: Brian Cherinka
# Created: Wednesday, 27th March 2019 11:47:22 am
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2019 Brian Cherinka
# Last Modified: Friday, 29th March 2019 1:09:54 pm
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import
from cthreepo.datamodel import DataModel


class SimpleDataModel(DataModel):
    survey = 'simple'


# create the manga datamodel
dm = SimpleDataModel()

