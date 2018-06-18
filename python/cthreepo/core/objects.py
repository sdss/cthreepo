# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-06-01 11:19:50
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-06-12 18:23:41

from __future__ import print_function, division, absolute_import
import six
import abc

from cthreepo.core.datamodel import BaseDataModel
from cthreepo.core import mixins
from astropy import units as u


class BaseObject(six.with_metaclass(abc.ABCMeta, object)):
    """Represents a extension in the DRP logcube file.

    """

    def __new__(cls, *args, **kwargs):

        # check keyword arguments against the list of Mixin bases
        mixins.check_mixins(cls, **kwargs)

        return super(BaseObject, cls).__new__(cls, args, kwargs)

    def __init__(self, name, unit=u.dimensionless_unscaled, scale=1, formats={},
                 description='', **kwargs):

        self.name = name

        self._parent = None

        self.formats = formats

        self.description = description

        self.unit = u.CompositeUnit(scale, unit.bases, unit.powers)

        # initialize
        super(BaseObject, self).__init__(**kwargs)

    @property
    def parent(self):
        """Retrieves the parent."""

        return self._parent

    @parent.setter
    def parent(self, value):
        """Sets the parent."""

        assert isinstance(value, BaseDataModel), 'parent must be of type BaseDataModel'

        self._parent = value

    @abc.abstractmethod
    def __repr__(self):

        return '<BaseObject {!r}, release={!r}, unit={!r}>'.format(
            self.name, self.parent.release if self.parent else None, self.unit.to_string())

    def __str__(self):

        return self.name.lower()

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


class DataCube(BaseObject):
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
    def __repr__(self):

        return '<DataCube {!r}, release={!r}, unit={!r}>'.format(
            self.name, self.parent.release if self.parent else None, self.unit.to_string())


class Spectrum(BaseObject):
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
    def __repr__(self):

        return '<Spectrum {!r}, release={!r}, unit={!r}>'.format(
            self.name, self.parent.release if self.parent else None, self.unit.to_string())


# class DataCube(object):
#     """Represents a extension in the DRP logcube file.

#     Parameters:
#         name (str):
#             The datacube name. This is the internal name that Marvin will use
#             for this datacube. It is different from the ``extension_name``
#             parameter, which must be identical to the extension name of the
#             datacube in the logcube file.
#         extension_name (str):
#             The FITS extension containing this datacube.
#         extension_wave (str):
#             The FITS extension containing the wavelength for this datacube.
#         extension_ivar (str or None):
#             The extension that contains the inverse variance associated with
#             this datacube, if any.
#         extension_mask (str or None):
#             The extension that contains the mask associated with this
#             datacube, if any.
#         db_table (str):
#             The DB table in which the datacube is stored. Defaults to
#             ``spaxel``.
#         unit (astropy unit or None):
#             The unit for this datacube.
#         scale (float):
#             The scaling factor for the values of the datacube.
#         formats (dict):
#             A dictionary with formats that can be used to represent the
#             datacube. Default ones are ``latex`` and ``string``.
#         description (str):
#             A description for the datacube.

#     """

#     def __init__(self, name, extension_name, extension_wave=None,
#                  extension_ivar=None, extension_mask=None, db_table='spaxel',
#                  unit=u.dimensionless_unscaled, scale=1, formats={},
#                  description=''):

#         self.name = name

#         self._extension_name = extension_name
#         self._extension_wave = extension_wave
#         self._extension_ivar = extension_ivar
#         self._extension_mask = extension_mask

#         self.db_table = db_table

#         self._parent = None

#         self.formats = formats

#         self.description = description

#         self.unit = u.CompositeUnit(scale, unit.bases, unit.powers)

#     @property
#     def parent(self):
#         """Retrieves the parent."""

#         return self._parent

#     @parent.setter
#     def parent(self, value):
#         """Sets the parent."""

#         assert isinstance(value, BaseDataModel), 'parent must be of type BaseDataModel'

#         self._parent = value

#     def full(self):
#         """Returns the name string."""

#         return self._extension_name.lower()

#     def has_ivar(self):
#         """Returns True is the datacube has an ivar extension."""

#         return self._extension_ivar is not None

#     def has_mask(self):
#         """Returns True is the datacube has an mask extension."""

#         return self._extension_mask is not None

#     def fits_extension(self, ext=None):
#         """Returns the FITS extension name."""

#         assert ext is None or ext in ['ivar', 'mask'], 'invalid extension'

#         if ext is None:
#             return self._extension_name.upper()

#         elif ext == 'ivar':
#             if not self.has_ivar():
#                 raise CthreepoError('no ivar extension for datacube {0!r}'.format(self.full()))
#             return self._extension_ivar.upper()

#         elif ext == 'mask':
#             if not self.has_mask():
#                 raise CthreepoError('no mask extension for datacube {0!r}'.format(self.full()))
#             return self._extension_mask

#     def db_column(self, ext=None):
#         """Returns the name of the DB column containing this datacube."""

#         return self.fits_extension(ext=ext).lower()

#     def __repr__(self):

#         return '<DataCube {!r}, release={!r}, unit={!r}>'.format(
#             self.name, self.parent.release if self.parent else None, self.unit.to_string())

#     def __str__(self):

#         return self.full()

#     def to_string(self, mode='string'):
#         """Return a string representation of the datacube."""

#         if mode == 'latex':

#             if mode in self.formats:
#                 latex = self.formats[mode]
#             else:
#                 latex = self.to_string()

#             return latex

#         else:

#             if mode in self.formats:
#                 string = self.formats[mode]
#             else:
#                 string = self.name

#             return string


# class Spectrum(object):
#     """Represents a extension in the DRP logcube file.

#     Parameters:
#         name (str):
#             The spectrum name. This is the internal name that Marvin will use
#             for this spectrum. It is different from the ``extension_name``
#             parameter, which must be identical to the extension name of the
#             spectrum in the logcube file.
#         extension_name (str):
#             The FITS extension containing this spectrum.
#         extension_wave (str):
#             The FITS extension containing the wavelength for this spectrum.
#         extension_std (str):
#             The FITS extension containing the standard deviation for this
#             spectrum.
#         db_table (str):
#             The DB table in which the spectrum is stored. Defaults to
#             ``cube``.
#         unit (astropy unit or None):
#             The unit for this spectrum.
#         scale (float):
#             The scaling factor for the values of the spectrum.
#         formats (dict):
#             A dictionary with formats that can be used to represent the
#             spectrum. Default ones are ``latex`` and ``string``.
#         description (str):
#             A description for the spectrum.

#     """

#     def __init__(self, name, extension_name, extension_wave=None, extension_std=None,
#                  db_table='cube', unit=u.dimensionless_unscaled, scale=1, formats={},
#                  description=''):

#         self.name = name

#         self._extension_name = extension_name
#         self._extension_wave = extension_wave
#         self._extension_std = extension_std

#         self.db_table = db_table

#         self.formats = formats

#         self.description = description

#         self._parent = None

#         self.unit = u.CompositeUnit(scale, unit.bases, unit.powers)

#     @property
#     def parent(self):
#         """Retrieves the parent."""

#         return self._parent

#     @parent.setter
#     def parent(self, value):
#         """Sets the parent."""

#         assert isinstance(value, BaseDataModel), 'parent must be of type BaseDataModel'

#         self._parent = value

#     def full(self):
#         """Returns the name string."""

#         return self._extension_name.lower()

#     def has_std(self):
#         """Returns True is the datacube has an std extension."""

#         return self._extension_std is not None

#     def has_mask(self):
#         """Returns True is the datacube has an mask extension."""

#         return self._extension_mask is not None

#     def fits_extension(self, ext=None):
#         """Returns the FITS extension name."""

#         assert ext is None or ext in ['std', 'mask'], 'invalid extension'

#         if ext is None:
#             return self._extension_name.upper()

#         elif ext == 'std':
#             if not self.has_std():
#                 raise CthreepoError('no std extension for spectrum {0!r}'.format(self.full()))
#             return self._extension_std.upper()

#         elif ext == 'mask':
#             if not self.has_mask():
#                 raise CthreepoError('no mask extension for spectrum {0!r}'.format(self.full()))
#             return self._extension_mask

#     def db_column(self, ext=None):
#         """Returns the name of the DB column containing this datacube."""

#         return self.fits_extension(ext=ext).lower()

#     def __repr__(self):

#         return '<Spectrum {!r}, release={!r}, unit={!r}>'.format(
#             self.name, self.parent.release if self.parent else None, self.unit.to_string())

#     def __str__(self):

#         return self.full()

#     def to_string(self, mode='string'):
#         """Return a string representation of the spectrum."""

#         if mode == 'latex':

#             if mode in self.formats:
#                 latex = self.formats[mode]
#             else:
#                 latex = self.to_string()

#             return latex

#         else:

#             if mode in self.formats:
#                 string = self.formats[mode]
#             else:
#                 string = self.name

#             return string



