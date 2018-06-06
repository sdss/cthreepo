# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-05-30 13:53:46
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-05-30 18:03:42

from __future__ import print_function, division, absolute_import


class DbMixin(object):

    def __init__(self):
        pass


class FileMixin(object):

    def __init__(self):
        pass


class ImageMixin(FileMixin):

    def __init__(self):
        pass


class CatalogMixin(FileMixin):

    def __init__(self):
        pass


class FitsMixin(FileMixin):

    def __init__(self):
        pass
