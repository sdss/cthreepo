# !/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Filename: mixins.py
# Project: manga
# Author: Brian Cherinka
# Created: Sunday, 19th May 2019 4:13:27 pm
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2019 Brian Cherinka
# Last Modified: Sunday, 19th May 2019 4:34:01 pm
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import
import re


# custom Channel model class
class Channel(object):
    ''' Extends the Channel class for the MaNGA DataModel '''

    def to_string(self, mode='string'):
        """Return a string representation of the channel."""

        if mode == 'latex':
            if 'latex' in self.formats:
                latex = self.formats['latex']
                latex = re.sub(r'forb{(.+)}', r'lbrack\\textrm{\1}\\rbrack', latex)
            else:
                latex = self.to_string().replace(' ', '\\ ')
            return latex
        elif mode is not None and mode in self.formats:
            return self.formats[mode]
        else:
            return self.name
