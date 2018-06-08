# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-06-08 15:32:00
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-06-08 16:19:56

from __future__ import print_function, division, absolute_import

import pytest
from cthreepo.core.mixins import DbMixin, FitsMixin
from cthreepo.core.objects import DataCube


class TestMixin(object):

    @pytest.mark.parametrize('base',
                             [((DataCube,)),
                              ((DataCube, DbMixin)),
                              ((DataCube, FitsMixin)),
                              ((DataCube, DbMixin, FitsMixin)),
                              ((DataCube, FitsMixin, DbMixin))],
                             ids=['base', 'db', 'fits', 'both', 'flip'])
    def test_bases(self, base):
        TestCube = type('TestCube', base, {})
        assert TestCube.__bases__ == base

    @pytest.mark.parametrize('base, meths',
                             [((DataCube,), ['to_string']),
                              ((DataCube, DbMixin), ['load_from_sql']),
                              ((DataCube, FitsMixin), ['fits_extension']),
                              ((DataCube, DbMixin, FitsMixin), ['fits_extension', 'load_from_sql']),
                              ((DataCube, FitsMixin, DbMixin), ['fits_extension', 'load_from_sql'])],
                             ids=['base', 'db', 'fits', 'both', 'flip'])
    def test_methods(self, base, meths):
        TestCube = type('TestCube', base, {})
        for meth in meths:
            assert hasattr(TestCube, meth)

    @pytest.mark.parametrize('base, kwarg, err',
                             [((DataCube, DbMixin), 'extension_name', 'Must have appropriate mixin FitsMixin'),
                              ((DataCube, FitsMixin), 'db_schema', 'Must have appropriate mixin DbMixin')],
                             ids=['nofits', 'nodb'])
    def test_fail(self, base, kwarg, err):
        TestCube = type('TestCube', base, {})
        with pytest.raises(AssertionError) as cm:
            tc = TestCube('test', **{kwarg: 'test'})
        assert err in str(cm.value)


