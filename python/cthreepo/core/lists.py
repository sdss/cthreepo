# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-06-08 10:02:14
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-06-08 10:03:54

from __future__ import print_function, division, absolute_import
import os
import copy as copy_mod
import six

from cthreepo.core.structs import FuzzyList
from cthreepo.core.datamodel import MetaDataModel
from cthreepo.core.objects import DataCube, Spectrum
import astropy.table as table


class BaseList(six.with_metaclass(MetaDataModel, FuzzyList)):
    """Creates a list containing models and their representation."""

    def __init__(self, the_list, parent=None):

        self.parent = parent
        self.base_name = self.base_name.lower()

        super(BaseList, self).__init__([])

        for item in the_list:
            self.append(item, copy=True)

    def mapper(self, value):
        """Helper method for the fuzzy list to match on the datacube name."""

        return value.name

    def append(self, value, copy=True):
        """Appends with copy."""

        append_obj = value if copy is False else copy_mod.deepcopy(value)
        append_obj.parent = self.parent

        if isinstance(append_obj, self.base_model):
            super(BaseList, self).append(append_obj)
        else:
            raise ValueError('invalid {!r} of type {!r}'.format(self.base_name, type(append_obj)))

    def list_names(self):
        """Returns a list with the names of the datacubes in this list."""

        return [item.name for item in self]

    def write_csv(self, filename=None, path=None, overwrite=None, **kwargs):
        ''' Write the datamodel to a CSV '''

        release = self.parent.release.lower().replace('-', '')

        if not filename:
            filename = '{0}_dm_{1}.csv'.format(self.base_name, release)

        if not path:
            path = os.path.join(os.getenv("CTHREEPO_DIR"), 'docs', 'sphinx', '_static')
            if not os.path.isdir(path):
                os.makedirs(path)

        fullpath = os.path.join(path, filename)
        table = self.to_table(**kwargs)
        table.write(fullpath, format='csv', overwrite=overwrite)


class DataCubeList(BaseList):
    base = {'DataCube': DataCube}

    def to_table(self, pprint=False, description=False, max_width=1000):
        """Returns an astropy table with all the datacubes in this datamodel.

        Parameters:
            pprint (bool):
                Whether the table should be printed to screen using astropy's
                table pretty print.
            description (bool):
                If ``True``, an extra column with the description of the
                datacube will be added.
            max_width (int or None):
                A keyword to pass to ``astropy.table.Table.pprint()`` with the
                maximum width of the table, in characters.

        Returns:
            result (``astropy.table.Table``):
                If ``pprint=False``, returns an astropy table containing
                the name of the datacube, whether it has ``ivar`` or
                ``mask``, the units, and a description (if
                ``description=True``)..

        """

        datacube_table = table.Table(
            None, names=['name', 'ivar', 'mask', 'unit', 'description',
                         'db_table', 'db_column', 'fits_extension'],
            dtype=['S20', bool, bool, 'S20', 'S500', 'S20', 'S20', 'S20'])

        if self.parent:
            datacube_table.meta['release'] = self.parent.release

        for datacube in self:
            unit = datacube.unit.to_string()

            datacube_table.add_row((datacube.name,
                                    datacube.has_ivar(),
                                    datacube.has_mask(),
                                    unit,
                                    datacube.description,
                                    datacube.db_table,
                                    datacube.db_column(),
                                    datacube.fits_extension()))

        if not description and 'description' in datacube_table.columns:
            datacube_table.remove_column('description')

        if pprint:
            datacube_table.pprint(max_width=max_width, max_lines=1e6)
            return

        return datacube_table


class SpectrumList(BaseList):
    base = {'Spectrum': Spectrum}

    def to_table(self, pprint=False, description=False, max_width=1000):
        """Returns an astropy table with all the spectra in this datamodel.

        Parameters:
            pprint (bool):
                Whether the table should be printed to screen using astropy's
                table pretty print.
            description (bool):
                If ``True``, an extra column with the description of the
                spectrum will be added.
            max_width (int or None):
                A keyword to pass to ``astropy.table.Table.pprint()`` with the
                maximum width of the table, in characters.

        Returns:
            result (``astropy.table.Table``):
                If ``pprint=False``, returns an astropy table containing
                the name of the spectrum, whether it has ``ivar`` or
                ``mask``, the units, and a description (if
                ``description=True``)..

        """

        spectrum_table = table.Table(
            None, names=['name', 'std', 'unit', 'description',
                         'db_table', 'db_column', 'fits_extension'],
            dtype=['S20', bool, 'S20', 'S500', 'S20', 'S20', 'S20'])

        if self.parent:
            spectrum_table.meta['release'] = self.parent.release

        for spectrum in self:
            unit = spectrum.unit.to_string()

            spectrum_table.add_row((spectrum.name,
                                    spectrum.has_std(),
                                    unit,
                                    spectrum.description,
                                    spectrum.db_table,
                                    spectrum.db_column(),
                                    spectrum.fits_extension()))

        if not description:
            spectrum_table.remove_column('description')

        if pprint:
            spectrum_table.pprint(max_width=max_width, max_lines=1e6)
            return

        return spectrum_table


