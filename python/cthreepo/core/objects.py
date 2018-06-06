# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-06-01 11:19:50
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-06-01 18:15:21

from __future__ import print_function, division, absolute_import
import os
import copy as copy_mod
import re
import six

from cthreepo.core.structs import FuzzyList, get_best_fuzzy
from cthreepo.core.datamodel import BaseDataModel
from cthreepo.core.exceptions import CthreepoError

import astropy.table as table
from astropy import units as u


class DataCubeList(FuzzyList):
    """Creates a list containing models and their representation."""

    def __init__(self, the_list, parent=None):

        self.parent = parent

        super(DataCubeList, self).__init__([])

        for item in the_list:
            self.append(item, copy=True)

    def mapper(self, value):
        """Helper method for the fuzzy list to match on the datacube name."""

        return value.name

    def append(self, value, copy=True):
        """Appends with copy."""

        append_obj = value if copy is False else copy_mod.deepcopy(value)
        append_obj.parent = self.parent

        if isinstance(append_obj, DataCube):
            super(DataCubeList, self).append(append_obj)
        else:
            raise ValueError('invalid datacube of type {!r}'.format(type(append_obj)))

    def list_names(self):
        """Returns a list with the names of the datacubes in this list."""

        return [item.name for item in self]

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

        if not description:
            datacube_table.remove_column('description')

        if pprint:
            datacube_table.pprint(max_width=max_width, max_lines=1e6)
            return

        return datacube_table

    def write_csv(self, filename=None, path=None, overwrite=None, **kwargs):
        ''' Write the datamodel to a CSV '''

        release = self.parent.release.lower().replace('-', '')

        if not filename:
            filename = 'datacubes_dm_{0}.csv'.format(release)

        if not path:
            path = os.path.join(os.getenv("CTHREEPO_DIR"), 'docs', 'sphinx', '_static')

        fullpath = os.path.join(path, filename)
        table = self.to_table(**kwargs)
        table.write(fullpath, format='csv', overwrite=overwrite)


class DataCube(object):
    """Represents a extension in the DRP logcube file.

    Parameters:
        name (str):
            The datacube name. This is the internal name that Marvin will use
            for this datacube. It is different from the ``extension_name``
            parameter, which must be identical to the extension name of the
            datacube in the logcube file.
        extension_name (str):
            The FITS extension containing this datacube.
        extension_wave (str):
            The FITS extension containing the wavelength for this datacube.
        extension_ivar (str or None):
            The extension that contains the inverse variance associated with
            this datacube, if any.
        extension_mask (str or None):
            The extension that contains the mask associated with this
            datacube, if any.
        db_table (str):
            The DB table in which the datacube is stored. Defaults to
            ``spaxel``.
        unit (astropy unit or None):
            The unit for this datacube.
        scale (float):
            The scaling factor for the values of the datacube.
        formats (dict):
            A dictionary with formats that can be used to represent the
            datacube. Default ones are ``latex`` and ``string``.
        description (str):
            A description for the datacube.

    """

    def __init__(self, name, extension_name, extension_wave=None,
                 extension_ivar=None, extension_mask=None, db_table='spaxel',
                 unit=u.dimensionless_unscaled, scale=1, formats={},
                 description=''):

        self.name = name

        self._extension_name = extension_name
        self._extension_wave = extension_wave
        self._extension_ivar = extension_ivar
        self._extension_mask = extension_mask

        self.db_table = db_table

        self._parent = None

        self.formats = formats

        self.description = description

        self.unit = u.CompositeUnit(scale, unit.bases, unit.powers)

    @property
    def parent(self):
        """Retrieves the parent."""

        return self._parent

    @parent.setter
    def parent(self, value):
        """Sets the parent."""

        assert isinstance(value, BaseDataModel), 'parent must be of type BaseDataModel'

        self._parent = value

    def full(self):
        """Returns the name string."""

        return self._extension_name.lower()

    def has_ivar(self):
        """Returns True is the datacube has an ivar extension."""

        return self._extension_ivar is not None

    def has_mask(self):
        """Returns True is the datacube has an mask extension."""

        return self._extension_mask is not None

    def fits_extension(self, ext=None):
        """Returns the FITS extension name."""

        assert ext is None or ext in ['ivar', 'mask'], 'invalid extension'

        if ext is None:
            return self._extension_name.upper()

        elif ext == 'ivar':
            if not self.has_ivar():
                raise CthreepoError('no ivar extension for datacube {0!r}'.format(self.full()))
            return self._extension_ivar.upper()

        elif ext == 'mask':
            if not self.has_mask():
                raise CthreepoError('no mask extension for datacube {0!r}'.format(self.full()))
            return self._extension_mask

    def db_column(self, ext=None):
        """Returns the name of the DB column containing this datacube."""

        return self.fits_extension(ext=ext).lower()

    def __repr__(self):

        return '<DataCube {!r}, release={!r}, unit={!r}>'.format(
            self.name, self.parent.release if self.parent else None, self.unit.to_string())

    def __str__(self):

        return self.full()

    def to_string(self, mode='string'):
        """Return a string representation of the datacube."""

        if mode == 'latex':

            if mode in self.formats:
                latex = self.formats[mode]
            else:
                latex = self.to_string()

            return latex

        else:

            if mode in self.formats:
                string = self.formats[mode]
            else:
                string = self.name

            return string


class SpectrumList(FuzzyList):
    """Creates a list containing spectra and their representation."""

    def __init__(self, the_list, parent=None):

        self.parent = parent

        super(SpectrumList, self).__init__([])

        for item in the_list:
            self.append(item, copy=True)

    def mapper(self, value):
        """Helper method for the fuzzy list to match on the spectrum name."""

        return value.name

    def append(self, value, copy=True):
        """Appends with copy."""

        append_obj = value if copy is False else copy_mod.deepcopy(value)
        append_obj.parent = self.parent

        if isinstance(append_obj, Spectrum):
            super(SpectrumList, self).append(append_obj)
        else:
            raise ValueError('invalid spectrum of type {!r}'.format(type(append_obj)))

    def list_names(self):
        """Returns a list with the names of the spectra in this list."""

        return [item.name for item in self]

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

    def write_csv(self, filename=None, path=None, overwrite=None, **kwargs):
        ''' Write the datamodel to a CSV '''

        release = self.parent.release.lower().replace('-', '')

        if not filename:
            filename = 'spectra_dm_{0}.csv'.format(release)

        if not path:
            path = os.path.join(os.getenv("CTHREEPO_DIR"), 'docs', 'sphinx', '_static')

        fullpath = os.path.join(path, filename)
        table = self.to_table(**kwargs)
        table.write(fullpath, format='csv', overwrite=overwrite)


class Spectrum(object):
    """Represents a extension in the DRP logcube file.

    Parameters:
        name (str):
            The spectrum name. This is the internal name that Marvin will use
            for this spectrum. It is different from the ``extension_name``
            parameter, which must be identical to the extension name of the
            spectrum in the logcube file.
        extension_name (str):
            The FITS extension containing this spectrum.
        extension_wave (str):
            The FITS extension containing the wavelength for this spectrum.
        extension_std (str):
            The FITS extension containing the standard deviation for this
            spectrum.
        db_table (str):
            The DB table in which the spectrum is stored. Defaults to
            ``cube``.
        unit (astropy unit or None):
            The unit for this spectrum.
        scale (float):
            The scaling factor for the values of the spectrum.
        formats (dict):
            A dictionary with formats that can be used to represent the
            spectrum. Default ones are ``latex`` and ``string``.
        description (str):
            A description for the spectrum.

    """

    def __init__(self, name, extension_name, extension_wave=None, extension_std=None,
                 db_table='cube', unit=u.dimensionless_unscaled, scale=1, formats={},
                 description=''):

        self.name = name

        self._extension_name = extension_name
        self._extension_wave = extension_wave
        self._extension_std = extension_std

        self.db_table = db_table

        self.formats = formats

        self.description = description

        self._parent = None

        self.unit = u.CompositeUnit(scale, unit.bases, unit.powers)

    @property
    def parent(self):
        """Retrieves the parent."""

        return self._parent

    @parent.setter
    def parent(self, value):
        """Sets the parent."""

        assert isinstance(value, BaseDataModel), 'parent must be of type BaseDataModel'

        self._parent = value

    def full(self):
        """Returns the name string."""

        return self._extension_name.lower()

    def has_std(self):
        """Returns True is the datacube has an std extension."""

        return self._extension_std is not None

    def has_mask(self):
        """Returns True is the datacube has an mask extension."""

        return self._extension_mask is not None

    def fits_extension(self, ext=None):
        """Returns the FITS extension name."""

        assert ext is None or ext in ['std', 'mask'], 'invalid extension'

        if ext is None:
            return self._extension_name.upper()

        elif ext == 'std':
            if not self.has_std():
                raise CthreepoError('no std extension for spectrum {0!r}'.format(self.full()))
            return self._extension_std.upper()

        elif ext == 'mask':
            if not self.has_mask():
                raise CthreepoError('no mask extension for spectrum {0!r}'.format(self.full()))
            return self._extension_mask

    def db_column(self, ext=None):
        """Returns the name of the DB column containing this datacube."""

        return self.fits_extension(ext=ext).lower()

    def __repr__(self):

        return '<Spectrum {!r}, release={!r}, unit={!r}>'.format(
            self.name, self.parent.release if self.parent else None, self.unit.to_string())

    def __str__(self):

        return self.full()

    def to_string(self, mode='string'):
        """Return a string representation of the spectrum."""

        if mode == 'latex':

            if mode in self.formats:
                latex = self.formats[mode]
            else:
                latex = self.to_string()

            return latex

        else:

            if mode in self.formats:
                string = self.formats[mode]
            else:
                string = self.name

            return string



