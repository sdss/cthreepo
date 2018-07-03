# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-06-01 11:19:50
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-06-20 09:26:24

from __future__ import print_function, division, absolute_import
import six
import abc
import re
import copy as copy_mod

from cthreepo.core.exceptions import CthreepoError
from cthreepo.core.datamodel import BaseDataModel
from cthreepo.core import mixins
from astropy import units as u


class BaseObject(six.with_metaclass(mixins.MixMeta, object)):
    """Represents a extension in the DRP logcube file.

    """

    def __new__(cls, *args, **kwargs):

        bases = cls.__bases__
        any_mixins = any([b for b in bases if 'mixin' in b.__name__.lower()])
        assert any_mixins, ('Cannot create object directly.  You must mix with at '
                            'least one Mixin Class {0}'.format(mixins.list_mixins(by_name=True)))

        # check keyword arguments against the list of Mixin bases
        mixins.check_mixins(cls, **kwargs)

        return super(BaseObject, cls).__new__(cls, args, kwargs)

    def __init__(self, parameter, unit=u.dimensionless_unscaled, scale=1, formats={},
                 description='', **kwargs):

        self.name = parameter

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
                latex = re.sub(r'forb{(.+)}', r'lbrack\\textrm{\1}\\rbrack', latex)
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


class Property(BaseObject):
    """A class representing a DAP property.

    Parameters:
        name (str):
            The name of the property.
        channel (:class:`Channel` object or None):
            The channel associated to the property, if any.
        ivar (bool):
            Whether the property has an inverse variance measurement.
        mask (bool):
            Whether the property has an associated mask.
        unit (astropy unit or None):
            The unit for this channel. If not defined, the unit from the
            ``channel`` will be used.
        scale (float or None):
            The scaling factor for the property. If not defined, the scaling
            factor from the ``channel`` will be used.
        formats (dict):
            A dictionary with formats that can be used to represent the
            property. Default ones are ``latex`` and ``string``.
        parent (:class:`DAPDataModel` object or None):
            The associated :class:`DAPDataModel` object. Usually it is set to
            ``None`` and populated when the property is added to the
            ``DAPDataModel`` object.
        binid (:class:`Property` object or None):
            The ``binid`` :class:`Property` object associated with this
            propety. If not set, assumes the `.DAPDataModel` ``default_binid``.
        description (str):
            A description of the property.

    """

    def __init__(self, parameter, channel=None, unit=None, scale=1, formats={},
                 parent=None, binid=None, description='', **kwargs):

        #self.name = name
        self.channel = copy_mod.deepcopy(channel)

        #self.ivar = ivar
        #self.mask = mask

        #self.formats = formats

        if unit is not None:
            self.unit = u.CompositeUnit(scale, unit.bases, unit.powers)
        elif unit is None and self.channel is None:
            self.unit = u.dimensionless_unscaled
        else:
            self.unit = self.channel.unit

        self._binid = binid

        # Makes sure the channel shares the units and scale
        if self.channel:
            self.channel.unit = self.unit

        super(Property, self).__init__(parameter, unit=self.unit, scale=scale,
                                       formats=formats, description=description, **kwargs)

        #self.description = description

        #self._parent = None
        #self.parent = parent

        self._binid = copy_mod.deepcopy(binid)
        if self._binid is not None:
            self._binid.parent = self.parent

    @property
    def parent(self):
        """Returns the parent for this property."""

        return self._parent

    @parent.setter
    def parent(self, value):
        """Sets the parent."""

        assert value is None or isinstance(value, BaseDataModel), 'value must be a BaseDataModel'

        self._parent = value

        if self._binid is not None:
            self._binid.parent = value

    # def full(self, web=None):
    #     """Returns the name + channel string."""

    #     if self.channel:
    #         if web:
    #             return self.name + ':' + self.channel.name
    #         else:
    #             return self.name + '_' + self.channel.name

    #     return self.name

    @property
    def binid(self):
        """Returns the binid property associated with this property."""

        if self.name == 'binid':
            raise CThreepoError('binid has not associated binid (?!)')

        assert self.parent is not None, 'a parent needs to be defined to get an associated binid.'

        if self._binid is None:
            return self.parent.default_binid

        return self._binid

    # def has_ivar(self):
    #     """Returns True if the property has an ivar extension."""

    #     return self.ivar is not False

    # def has_mask(self):
    #     """Returns True if the property has an mask extension."""

    #     return self.mask is not False

    # def db_column(self, ext=None):
    #     """Returns the name of the DB column containing this property."""

    #     assert ext is None or ext in ['ivar', 'mask'], 'invalid extension'

    #     if ext is None:
    #         return self.full()

    #     if ext == 'ivar':
    #         assert self.ivar is True, 'no ivar for property {0!r}'.format(self.full())
    #         return self.name + '_ivar' + \
    #             ('_{0}'.format(self.channel.db_name) if self.channel else '')

    #     if ext == 'mask':
    #         assert self.mask is True, 'no mask for property {0!r}'.format(self.full())
    #         return self.name + '_mask' + \
    #             ('_{0}'.format(self.channel.db_name) if self.channel else '')

    def __repr__(self):

        return '<Property {0!r}, channel={2!r}, release={1!r}, unit={3!r}>'.format(
            self.name, self.parent.release if self.parent else None,
            self.channel.name if self.channel else 'None', self.unit.to_string())

    def __str__(self):

        return self.full()

    # @property
    # def model(self):
    #     ''' The ModelClass the property belongs to '''

    #     return self.parent.property_table

    # @property
    # def db_table(self):
    #     """The DB table to use to retrieve this property."""

    #     assert self.parent is not None, 'parent DAPDataModel is not set for this property.'

    #     return self.parent.property_table.lower()

    # def fits_extension(self):
    #     ''' The FITS extension this property belongs to '''

    #     ext = self.name.upper()
    #     if self.channel:
    #         channel_num = self.channel.idx
    #         ext = '{0}_{1}'.format(ext, channel_num)
    #     return ext

    def to_string(self, mode='string', include_channel=True):
        """Return a string representation of the channel."""

        if mode == 'latex':

            if mode in self.formats:
                latex = self.formats[mode]
            else:
                latex = self.to_string(include_channel=False)

            if self.channel and include_channel:
                latex = latex + ' ' + self.channel.to_string('latex')

            return latex

        else:

            if mode in self.formats:
                string = self.formats[mode]
            else:
                string = self.name

            if self.channel is None or include_channel is False:
                return string
            else:
                return string + ': ' + self.channel.to_string(mode=mode)


class MultiChannelProperty(list):
    """A class representing a list of channels for the same property.

    Parameters:
        name (str):
            The name of the property.
        channels (list of :class:`Channel` objects):
            The channels associated to the property.
        ivar (bool):
            Whether the properties have an inverse variance measurement.
        mask (bool):
            Whether the properties have an associated mask.
        unit (astropy unit or None):
            The unit for these channels. If set, it will override any unit
            defined in the individual channels.
        scale (float):
            The scaling factor for these channels. If set, it will override
            any unit defined in the individual channels.
        formats (dict):
            A dictionary with formats that can be used to represent the
            property. Default ones are ``latex`` and ``string``.
        parent (:class:`DAPDataModel` object or None):
            The associated :class:`DAPDataModel` object. Usually it is set to
            ``None`` and populated when the property is added to the
            ``DAPDataModel`` object.
        binid (:class:`Property` object or None):
            The ``binid`` `.Property` object to be associated to all the
            propeties in this `.MultiChannelProperty`.
        description (str):
            A description of the property.
        kwargs (dict):
            Arguments to be passed to each ``Property`` on initialisation.

    """

    def __init__(self, name, channels=[], unit=None, scale=1, binid=None, **kwargs):

        self.name = name

        self.ivar = kwargs.get('ivar', False)
        self.mask = kwargs.get('mask', False)
        self.description = kwargs.get('description', '')

        self._parent = None
        self.parent = kwargs.get('parent', None)

        self_list = []
        for ii, channel in enumerate(channels):
            this_unit = unit if not isinstance(unit, (list, tuple)) else unit[ii]
            this_scale = scale if not isinstance(scale, (list, tuple)) else scale[ii]
            self_list.append(Property(self.name, channel=channel,
                                      unit=this_unit, scale=this_scale,
                                      binid=binid, **kwargs))

        list.__init__(self, self_list)

    @property
    def parent(self):
        """Returns the parent for this MultiChannelProperty."""

        return self._parent

    @parent.setter
    def parent(self, value):
        """Sets parent for the instance and all listed Property objects."""

        assert value is None or isinstance(value, BaseDataModel), 'value must be a DataModel'

        self._parent = value

        for prop in self:
            prop.parent = value

    @property
    def channels(self):
        """Returns a list of channels."""

        return [item.channel for item in self]

    def __getitem__(self, value):
        """Uses fuzzywuzzy to get a channel."""

        if not isinstance(value, six.string_types):
            return super(MultiChannelProperty, self).__getitem__(value)

        best_match = get_best_fuzzy(value, self.channels)

        return super(MultiChannelProperty, self).__getitem__(self.channels.index(best_match))

    def __repr__(self):

        return '<MultiChannelProperty {0!r}, release={1!r}, channels={2!r}>'.format(
            self.name, self.parent.release if self.parent else None,
            [channel.name for channel in self.channels])

    # @property
    # def db_table(self):
    #     ''' Returns the db table this belongs to '''

    #     return self.parent.property_table.lower()

    # def db_columns(self):
    #     ''' Returns a list of db columns for this MultiChannelProperty '''

    #     return [item.db_column() for item in self]

    # def fits_extension(self):
    #     ''' Returns the FITS extension this belongs to '''

    #     return self.name.upper()


class Channel(BaseObject):
    """A class representing a channel in a property.

    Parameters:
        name (str):
            The channel name.
        unit (astropy unit or None):
            The unit for this channel.
        scale (float):
            The scaling factor for the channel.
        formats (dict):
            A dictionary with formats that can be used to represent the
            channel. Default ones are ``latex`` and ``string``.
        idx (int):
            The index of the channel in the MAPS file extension.
        db_name (str or None):
            The name of this channel in the database. If None, ``name`` will
            be used.
        description (str):
            A description for the channel.

    """

    def __init__(self, name, unit=u.dimensionless_unscaled, scale=1, formats={},
                 idx=None, description='', **kwargs):

        super(Channel, self).__init__(name, unit=unit, scale=scale,
                                      formats=formats, description=description, **kwargs)
        self.idx = idx

    # def to_string(self, mode='string'):
    #     """Return a string representation of the channel."""

    #     if mode == 'latex':
    #         if 'latex' in self.formats:
    #             latex = self.formats['latex']
    #             latex = re.sub(r'forb{(.+)}', r'lbrack\\textrm{\1}\\rbrack', latex)
    #         else:
    #             latex = self.to_string().replace(' ', '\\ ')
    #         return latex
    #     elif mode is not None and mode in self.formats:
    #         return self.formats[mode]
    #     else:
    #         return self.name

    def __repr__(self):

        return '<Channel {0!r} unit={1!r}>'.format(self.name, self.unit.to_string())


class Model(BaseObject):
    """Represents a extension in the DAP logcube file.

    Parameters:
        name (str):
            The model name. This is the internal name that Marvin will use for
            this model. It is different from the ``extension_name`` parameter,
            which must be identical to the extension name of the model.
        extension_name (str):
            The FITS extension containing this model.
        extension_wave (str):
            The FITS extension containing the wavelength for this model.
        extension_ivar (str or None):
            The extension that contains the inverse variance associated with
            this model, if any.
        extension_mask (str or None):
            The extension that contains the mask associated with this model,
            if any.
        channels (list):
            The channels associated with this model (probably only used
            for binid).
        unit (astropy unit or None):
            The unit for this model.
        scale (float):
            The scaling factor for the values of the model.
        formats (dict):
            A dictionary with formats that can be used to represent the
            model. Default ones are ``latex`` and ``string``.
        parent (:class:`DAPDataModel` object or None):
            The associated :class:`DAPDataModel` object. Usually it is set to
            ``None`` and populated when the model is added to the
            ``DAPDataModel`` object.
        binid (:class:`Property` object or None):
            The ``binid`` :class:`Property` object associated with this
            model. If not set, assumes the `.DAPDataModel` ``default_binid``.
        description (str):
            A description for the model.
        db_table (str):
            The database table the model belongs to.

    """

    def __init__(self, parameter, channels=[], unit=u.dimensionless_unscaled, scale=1,
                 formats={}, binid=None, description='', **kwargs):

        # self.name = name

        # self._extension_name = extension_name
        # self._extension_wave = extension_wave
        # self._extension_ivar = extension_ivar
        # self._extension_mask = extension_mask

        super(Model, self).__init__(parameter, unit=unit, scale=scale,
                                    formats=formats, description=description, **kwargs)

        self.channels = channels

        # self.unit = u.CompositeUnit(scale, unit.bases, unit.powers)

        # self.formats = formats
        # self.description = description
        # self.db_table = db_table

        self._binid = binid

        #self._parent = None

        self._binid = copy_mod.deepcopy(binid)
        if self._binid is not None:
            self._binid.parent = self.parent

    @property
    def parent(self):
        """Returns the parent for this model."""

        return self._parent

    @parent.setter
    def parent(self, value):
        """Sets parent."""

        assert value is None or isinstance(value, BaseDataModel), 'parent must be of type BaseDataModel'

        self._parent = value

        if self._binid is not None:
            self._binid.parent = value

    # def full(self):
    #     """Returns the name + channel string."""

    #     return self.name

    # def has_ivar(self):
    #     """Returns True if the datacube has an ivar extension."""

    #     return self._extension_ivar is not None

    # def has_mask(self):
    #     """Returns True if the datacube has an mask extension."""

    #     return self._extension_mask is not None

    @property
    def binid(self):
        """Returns the binid property associated with this property."""

        if self.name == 'binid':
            raise CthreepoError('binid has not associated binid (?!)')

        assert self.parent is not None, 'a parent needs to be defined to get an associated binid.'

        if self._binid is None:
            return self.parent.default_binid

        return self._binid

    # def fits_extension(self, ext=None):
    #     """Returns the FITS extension name."""

    #     assert ext is None or ext in ['ivar', 'mask'], 'invalid extension'

    #     if ext is None:
    #         return self._extension_name.upper()

    #     elif ext == 'ivar':
    #         if not self.has_ivar():
    #             raise MarvinError('no ivar extension for datacube {0!r}'.format(self.full()))
    #         return self._extension_ivar.upper()

    #     elif ext == 'mask':
    #         if not self.has_mask():
    #             raise MarvinError('no mask extension for datacube {0!r}'.format(self.full()))
    #         return self._extension_mask

    # def db_column(self, ext=None):
    #     """Returns the name of the DB column containing this datacube."""

    #     return self.fits_extension(ext=ext).lower()

    def __repr__(self):

        return '<Model {!r}, release={!r}, unit={!r}>'.format(
            self.name, self.parent.release if self.parent else None, self.unit.to_string())

    def __str__(self):

        return self.full()

    # def to_string(self, mode='string', include_channel=True):
    #     """Return a string representation of the channel."""

    #     if mode == 'latex':

    #         if mode in self.formats:
    #             latex = self.formats[mode]
    #         else:
    #             latex = self.to_string(include_channel=False)

    #         if self.channel and include_channel:
    #             latex = latex + ' ' + self.channel.to_string('latex')

    #         return latex

    #     else:

    #         if mode in self.formats:
    #             string = self.formats[mode]
    #         else:
    #             string = self.name

    #         if self.channel is None or include_channel is False:
    #             return string
    #         else:
    #             return string + ': ' + self.channel.to_string(mode=mode)

