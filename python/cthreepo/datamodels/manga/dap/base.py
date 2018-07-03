# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-06-01 16:28:50
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-06-19 11:51:03

from __future__ import print_function, division, absolute_import
import itertools

from astropy import units as u

from cthreepo.core.exceptions import CthreepoError
from cthreepo.core.datamodel import DataModelList, BaseDataModel


__ALL__ = ('DAPDataModelList', 'DAPDataModel', 'Bintype', 'Template', 'Property',
           'MultiChannelProperty', 'spaxel', 'datamodel', 'Channel')


class DAPDataModel(BaseDataModel):
    """A class representing a DAP datamodel, with bintypes, templates, properties, etc."""

    def __init__(self, release, bintypes=[], templates=[], properties=[], models=[],
                 default_template=None, default_bintype=None, property_table=None,
                 default_binid=None, aliases=[], bitmasks=None, db_only=[], default_mapset=None,
                 default_mapmask=None):

        super(DAPDataModel, self).__init__(release, aliases=aliases, bitmasks=bitmasks)

        self.bintypes = bintypes
        self.templates = templates
        self.db_only = db_only

        self.properties = PropertyList(properties, parent=self)
        self.models = ModelList(models, parent=self)

        self.property_table = property_table

        # default plotting params
        self.default_mapmask = default_mapmask
        self.default_mapset = self.get_default_mapset(default_mapset)
        self.default_plot_params = self.get_default_plot_params()

        # default bintypes/templates
        self._default_bintype = None
        self.default_bintype = default_bintype

        self._default_template = None
        self.default_template = default_template

        self.default_binid = default_binid
        if self.default_binid is not None:
            self.default_binid.parent = self

        assert len([bintype for bintype in self.bintypes if bintype.binned is False]) <= 1, \
            'a DAP datamodel can have only one unbinned bintype'

    def __repr__(self):

        return ('<DAPDataModel release={0!r}, n_bintypes={1}, n_templates={2}, n_properties={3}>'
                .format(self.release, len(self.bintypes), len(self.templates),
                        len(self.properties)))

    def __eq__(self, value):
        """Uses fuzzywuzzy to return the closest property match."""

        prop_names = [prop.name for prop in self.properties.extensions]
        model_names = [model.full() for model in self.models]

        # If the values matches exactly one of the property or model names,
        # we return that one.
        if value in prop_names:
            return self.properties.extensions[prop_names.index(value)]
        elif value in model_names:
            return self.models[model_names.index(value)]

        # Gets the best match for properties and models. Only returns a value
        # if only one of them gets a match.

        try:
            prop_best_match = self.properties[value]
        except ValueError:
            prop_best_match = None

        try:
            model_best_match = self.models[value]
        except ValueError:
            model_best_match = None

        if ((model_best_match is None and prop_best_match is None) or
                (model_best_match is not None and prop_best_match is not None)):
            raise ValueError('too ambiguous input {!r}'.format(value))
        elif model_best_match is not None:
            return model_best_match
        elif prop_best_match is not None:
            return prop_best_match

    @property
    def default_bintype(self):
        """Returns the default bintype."""

        return self._default_bintype

    @default_bintype.setter
    def default_bintype(self, value):
        """Sets the default bintype."""

        for bintype in self.bintypes:
            if str(value) == bintype.name:
                value = bintype

        if value not in self.bintypes and value is not None:
            raise ValueError('{0!r} not found in list of bintypes.'.format(value))

        self._default_bintype = value

    @property
    def default_template(self):
        """Returns the default template."""

        return self._default_template

    @default_template.setter
    def default_template(self, value):
        """Sets the default template."""

        for template in self.templates:
            if str(value) == template.name:
                value = template

        if value not in self.templates and value is not None:
            raise ValueError('{0!r} not found in list of templates.'.format(value))

        self._default_template = value

    def get_unbinned(self):
        """Returns the unbinned bintype."""

        for bintype in self.bintypes:
            if bintype.binned is False:
                return bintype

        raise CthreepoError('cannot find unbinned bintype for '
                            'DAP datamodel for release {0}'.format(self.release))

    def get_bintype(self, value=None):
        """Returns a bintype whose name matches ``value``.

        Returns the default one if ``value=None``.

        """

        if value is None:
            return self.default_bintype

        for bintype in self.bintypes:
            if bintype.name.upper() == str(value).upper():
                return bintype

        raise CthreepoError('invalid bintype {0!r}'.format(value))

    def get_template(self, value=None):
        """Returns a template whose name matches ``value``.

        Returns the default one if ``value=None``.

        """

        if value is None:
            return self.default_template

        for template in self.templates:
            if template.name.upper() == str(value).upper():
                return template

        raise CthreepoError('invalid template {0!r}'.format(value))

    def get_bintemps(self, default=False, db_only=False):
        """Returns a list of all combinations of bintype and template."""

        if default:
            return '{0}-{1}'.format(self.default_bintype.name, self.default_template.name)

        bins = [bintype.name for bintype in self.bintypes]
        temps = [template.name for template in self.templates]

        if db_only and self.db_only:
            bins = [b for b in bins if b in self.db_only]

        return ['-'.join(item) for item in list(itertools.product(bins, temps))]

    @staticmethod
    def get_default_mapset(default=None):
        ''' Return the default set of maps

        Syntax of a map name is parameter:channel

        Parameters:
            default (list):
                A list of default map names

        Returns:
            A list of map names

        '''
        if not default:
            default = ['stellar_vel', 'emline_gflux:ha_6564', 'specindex:d4000']

        assert len(default) <= 6, 'default maps must number less than six'
        return default

    def get_default_plot_params(self):
        ''' Return the default set of plotting params '''

        if not self.default_mapmask:
            self.default_mapmask = ['DONOTUSE']

        return self.set_base_params()

    def get_plot_params(self, prop=None):
        ''' Get one set of plotting params for a given property

        Parameters:
            prop (str):
                The name of the property
        Returns:
            The default set of plotting params for the given property
        '''

        defaults = self.get_default_plot_params()

        if 'vel' in prop:
            key = 'vel'
        elif 'sigma' in prop:
            key = 'sigma'
        else:
            key = 'default'
        return defaults[key]

    def set_base_params(self):
        ''' Set the base plotting param defaults '''

        return {'default': {'bitmasks': self.default_mapmask,
                            'cmap': 'linearlab',
                            'percentile_clip': [5, 95],
                            'symmetric': False,
                            'snr_min': 1},
                'vel': {'bitmasks': self.default_mapmask,
                        'cmap': 'RdBu_r',
                        'percentile_clip': [10, 90],
                        'symmetric': True,
                        'snr_min': None},
                'sigma': {'bitmasks': self.default_mapmask,
                          'cmap': 'inferno',
                          'percentile_clip': [10, 90],
                          'symmetric': False,
                          'snr_min': 1}}


class DAPDataModelList(DataModelList):
    """A dictionary of DAP datamodels."""

    base = {'DAPDataModel': DAPDataModel}


class Bintype(object):
    """A class representing a bintype."""

    def __init__(self, bintype, binned=True, n=None, description=''):

        self.name = bintype
        self.binned = binned
        self.n = n
        self.description = description

    def __repr__(self):

        return '<Bintype {0!r}, binned={1!r}>'.format(self.name, self.binned)

    def __str__(self):

        return self.name

    def __eq__(self, other):

        return self.name == other or super(Bintype, self) == other


class Template(object):
    """A class representing a template."""

    def __init__(self, template, n=None, description=''):

        self.name = template
        self.n = n
        self.description = description

    def __repr__(self):

        return '<Template {0!r}>'.format(self.name)

    def __str__(self):

        return self.name

    def __eq__(self, other):

        return self.name == other or super(Template, self) == other


# class Property(object):
#     """A class representing a DAP property.

#     Parameters:
#         name (str):
#             The name of the property.
#         channel (:class:`Channel` object or None):
#             The channel associated to the property, if any.
#         ivar (bool):
#             Whether the property has an inverse variance measurement.
#         mask (bool):
#             Whether the property has an associated mask.
#         unit (astropy unit or None):
#             The unit for this channel. If not defined, the unit from the
#             ``channel`` will be used.
#         scale (float or None):
#             The scaling factor for the property. If not defined, the scaling
#             factor from the ``channel`` will be used.
#         formats (dict):
#             A dictionary with formats that can be used to represent the
#             property. Default ones are ``latex`` and ``string``.
#         parent (:class:`DAPDataModel` object or None):
#             The associated :class:`DAPDataModel` object. Usually it is set to
#             ``None`` and populated when the property is added to the
#             ``DAPDataModel`` object.
#         binid (:class:`Property` object or None):
#             The ``binid`` :class:`Property` object associated with this
#             propety. If not set, assumes the `.DAPDataModel` ``default_binid``.
#         description (str):
#             A description of the property.

#     """

#     def __init__(self, name, channel=None, ivar=False, mask=False, unit=None,
#                  scale=1, formats={}, parent=None, binid=None, description=''):

#         self.name = name
#         self.channel = copy_mod.deepcopy(channel)

#         self.ivar = ivar
#         self.mask = mask

#         self.formats = formats

#         if unit is not None:
#             self.unit = u.CompositeUnit(scale, unit.bases, unit.powers)
#         elif unit is None and self.channel is None:
#             self.unit = u.dimensionless_unscaled
#         else:
#             self.unit = self.channel.unit

#         self._binid = binid

#         # Makes sure the channel shares the units and scale
#         if self.channel:
#             self.channel.unit = self.unit

#         self.description = description

#         self._parent = None
#         self.parent = parent

#         self._binid = copy_mod.deepcopy(binid)
#         if self._binid is not None:
#             self._binid.parent = self.parent

#     @property
#     def parent(self):
#         """Returns the parent for this property."""

#         return self._parent

#     @parent.setter
#     def parent(self, value):
#         """Sets the parent."""

#         assert value is None or isinstance(value, DAPDataModel), 'value must be a DAPDataModel'

#         self._parent = value

#         if self._binid is not None:
#             self._binid.parent = value

#     def full(self, web=None):
#         """Returns the name + channel string."""

#         if self.channel:
#             if web:
#                 return self.name + ':' + self.channel.name
#             else:
#                 return self.name + '_' + self.channel.name

#         return self.name

#     @property
#     def binid(self):
#         """Returns the binid property associated with this property."""

#         if self.name == 'binid':
#             raise MarvinError('binid has not associated binid (?!)')

#         assert self.parent is not None, 'a parent needs to be defined to get an associated binid.'

#         if self._binid is None:
#             return self.parent.default_binid

#         return self._binid

#     def has_ivar(self):
#         """Returns True if the property has an ivar extension."""

#         return self.ivar is not False

#     def has_mask(self):
#         """Returns True if the property has an mask extension."""

#         return self.mask is not False

#     def db_column(self, ext=None):
#         """Returns the name of the DB column containing this property."""

#         assert ext is None or ext in ['ivar', 'mask'], 'invalid extension'

#         if ext is None:
#             return self.full()

#         if ext == 'ivar':
#             assert self.ivar is True, 'no ivar for property {0!r}'.format(self.full())
#             return self.name + '_ivar' + \
#                 ('_{0}'.format(self.channel.db_name) if self.channel else '')

#         if ext == 'mask':
#             assert self.mask is True, 'no mask for property {0!r}'.format(self.full())
#             return self.name + '_mask' + \
#                 ('_{0}'.format(self.channel.db_name) if self.channel else '')

#     def __repr__(self):

#         return '<Property {0!r}, channel={2!r}, release={1!r}, unit={3!r}>'.format(
#             self.name, self.parent.release if self.parent else None,
#             self.channel.name if self.channel else 'None', self.unit.to_string())

#     def __str__(self):

#         return self.full()

#     @property
#     def model(self):
#         ''' The ModelClass the property belongs to '''

#         return self.parent.property_table

#     @property
#     def db_table(self):
#         """The DB table to use to retrieve this property."""

#         assert self.parent is not None, 'parent DAPDataModel is not set for this property.'

#         return self.parent.property_table.lower()

#     def fits_extension(self):
#         ''' The FITS extension this property belongs to '''

#         ext = self.name.upper()
#         if self.channel:
#             channel_num = self.channel.idx
#             ext = '{0}_{1}'.format(ext, channel_num)
#         return ext

#     def to_string(self, mode='string', include_channel=True):
#         """Return a string representation of the channel."""

#         if mode == 'latex':

#             if mode in self.formats:
#                 latex = self.formats[mode]
#             else:
#                 latex = self.to_string(include_channel=False)

#             if self.channel and include_channel:
#                 latex = latex + ' ' + self.channel.to_string('latex')

#             return latex

#         else:

#             if mode in self.formats:
#                 string = self.formats[mode]
#             else:
#                 string = self.name

#             if self.channel is None or include_channel is False:
#                 return string
#             else:
#                 return string + ': ' + self.channel.to_string(mode=mode)


# class MultiChannelProperty(list):
#     """A class representing a list of channels for the same property.

#     Parameters:
#         name (str):
#             The name of the property.
#         channels (list of :class:`Channel` objects):
#             The channels associated to the property.
#         ivar (bool):
#             Whether the properties have an inverse variance measurement.
#         mask (bool):
#             Whether the properties have an associated mask.
#         unit (astropy unit or None):
#             The unit for these channels. If set, it will override any unit
#             defined in the individual channels.
#         scale (float):
#             The scaling factor for these channels. If set, it will override
#             any unit defined in the individual channels.
#         formats (dict):
#             A dictionary with formats that can be used to represent the
#             property. Default ones are ``latex`` and ``string``.
#         parent (:class:`DAPDataModel` object or None):
#             The associated :class:`DAPDataModel` object. Usually it is set to
#             ``None`` and populated when the property is added to the
#             ``DAPDataModel`` object.
#         binid (:class:`Property` object or None):
#             The ``binid`` `.Property` object to be associated to all the
#             propeties in this `.MultiChannelProperty`.
#         description (str):
#             A description of the property.
#         kwargs (dict):
#             Arguments to be passed to each ``Property`` on initialisation.

#     """

#     def __init__(self, name, channels=[], unit=None, scale=1, binid=None, **kwargs):

#         self.name = name

#         self.ivar = kwargs.get('ivar', False)
#         self.mask = kwargs.get('mask', False)
#         self.description = kwargs.get('description', '')

#         self._parent = None
#         self.parent = kwargs.get('parent', None)

#         self_list = []
#         for ii, channel in enumerate(channels):
#             this_unit = unit if not isinstance(unit, (list, tuple)) else unit[ii]
#             this_scale = scale if not isinstance(scale, (list, tuple)) else scale[ii]
#             self_list.append(Property(self.name, channel=channel,
#                                       unit=this_unit, scale=this_scale,
#                                       binid=binid, **kwargs))

#         list.__init__(self, self_list)

#     @property
#     def parent(self):
#         """Returns the parent for this MultiChannelProperty."""

#         return self._parent

#     @parent.setter
#     def parent(self, value):
#         """Sets parent for the instance and all listed Property objects."""

#         assert value is None or isinstance(value, DAPDataModel), 'value must be a DAPDataModel'

#         self._parent = value

#         for prop in self:
#             prop.parent = value

#     @property
#     def channels(self):
#         """Returns a list of channels."""

#         return [item.channel for item in self]

#     def __getitem__(self, value):
#         """Uses fuzzywuzzy to get a channel."""

#         if not isinstance(value, six.string_types):
#             return super(MultiChannelProperty, self).__getitem__(value)

#         best_match = get_best_fuzzy(value, self.channels)

#         return super(MultiChannelProperty, self).__getitem__(self.channels.index(best_match))

#     def __repr__(self):

#         return '<MultiChannelProperty {0!r}, release={1!r}, channels={2!r}>'.format(
#             self.name, self.parent.release if self.parent else None,
#             [channel.name for channel in self.channels])

#     @property
#     def db_table(self):
#         ''' Returns the db table this belongs to '''

#         return self.parent.property_table.lower()

#     def db_columns(self):
#         ''' Returns a list of db columns for this MultiChannelProperty '''

#         return [item.db_column() for item in self]

#     def fits_extension(self):
#         ''' Returns the FITS extension this belongs to '''

#         return self.name.upper()


# class Channel(object):
#     """A class representing a channel in a property.

#     Parameters:
#         name (str):
#             The channel name.
#         unit (astropy unit or None):
#             The unit for this channel.
#         scale (float):
#             The scaling factor for the channel.
#         formats (dict):
#             A dictionary with formats that can be used to represent the
#             channel. Default ones are ``latex`` and ``string``.
#         idx (int):
#             The index of the channel in the MAPS file extension.
#         db_name (str or None):
#             The name of this channel in the database. If None, ``name`` will
#             be used.
#         description (str):
#             A description for the channel.

#     """

#     def __init__(self, name, unit=u.dimensionless_unscaled, scale=1, formats={},
#                  idx=None, db_name=None, description=''):

#         self.name = name
#         self.unit = u.CompositeUnit(scale, unit.bases, unit.powers)
#         self.formats = formats
#         self.idx = idx
#         self.db_name = db_name or self.name
#         self.description = description

#     def to_string(self, mode='string'):
#         """Return a string representation of the channel."""

#         if mode == 'latex':
#             if 'latex' in self.formats:
#                 latex = self.formats['latex']
#                 latex = re.sub(r'forb{(.+)}', r'lbrack\\textrm{\1}\\rbrack', latex)
#             else:
#                 latex = self.to_string().replace(' ', '\\ ')
#             return latex
#         elif mode is not None and mode in self.formats:
#             return self.formats[mode]
#         else:
#             return self.name

#     def __repr__(self):

#         return '<Channel {0!r} unit={1!r}>'.format(self.name, self.unit.to_string())

#     def __str__(self):

#         return self.name


# class Model(object):
#     """Represents a extension in the DAP logcube file.

#     Parameters:
#         name (str):
#             The model name. This is the internal name that Marvin will use for
#             this model. It is different from the ``extension_name`` parameter,
#             which must be identical to the extension name of the model.
#         extension_name (str):
#             The FITS extension containing this model.
#         extension_wave (str):
#             The FITS extension containing the wavelength for this model.
#         extension_ivar (str or None):
#             The extension that contains the inverse variance associated with
#             this model, if any.
#         extension_mask (str or None):
#             The extension that contains the mask associated with this model,
#             if any.
#         channels (list):
#             The channels associated with this model (probably only used
#             for binid).
#         unit (astropy unit or None):
#             The unit for this model.
#         scale (float):
#             The scaling factor for the values of the model.
#         formats (dict):
#             A dictionary with formats that can be used to represent the
#             model. Default ones are ``latex`` and ``string``.
#         parent (:class:`DAPDataModel` object or None):
#             The associated :class:`DAPDataModel` object. Usually it is set to
#             ``None`` and populated when the model is added to the
#             ``DAPDataModel`` object.
#         binid (:class:`Property` object or None):
#             The ``binid`` :class:`Property` object associated with this
#             model. If not set, assumes the `.DAPDataModel` ``default_binid``.
#         description (str):
#             A description for the model.
#         db_table (str):
#             The database table the model belongs to.

#     """

#     def __init__(self, name, extension_name, extension_wave=None,
#                  extension_ivar=None, extension_mask=None, channels=[],
#                  unit=u.dimensionless_unscaled, scale=1, formats={},
#                  parent=None, binid=None, description='', db_table='modelspaxel'):

#         self.name = name

#         self._extension_name = extension_name
#         self._extension_wave = extension_wave
#         self._extension_ivar = extension_ivar
#         self._extension_mask = extension_mask

#         self.channels = channels

#         self.unit = u.CompositeUnit(scale, unit.bases, unit.powers)

#         self.formats = formats
#         self.description = description
#         self.db_table = db_table

#         self._binid = binid

#         self._parent = None
#         self.parent = parent

#         self._binid = copy_mod.deepcopy(binid)
#         if self._binid is not None:
#             self._binid.parent = self.parent

#     @property
#     def parent(self):
#         """Returns the parent for this model."""

#         return self._parent

#     @parent.setter
#     def parent(self, value):
#         """Sets parent."""

#         assert value is None or isinstance(value, DAPDataModel), 'value must be a DAPDataModel'

#         self._parent = value

#         if self._binid is not None:
#             self._binid.parent = value

#     def full(self):
#         """Returns the name + channel string."""

#         return self.name

#     def has_ivar(self):
#         """Returns True if the datacube has an ivar extension."""

#         return self._extension_ivar is not None

#     def has_mask(self):
#         """Returns True if the datacube has an mask extension."""

#         return self._extension_mask is not None

#     @property
#     def binid(self):
#         """Returns the binid property associated with this property."""

#         if self.name == 'binid':
#             raise MarvinError('binid has not associated binid (?!)')

#         assert self.parent is not None, 'a parent needs to be defined to get an associated binid.'

#         if self._binid is None:
#             return self.parent.default_binid

#         return self._binid

#     def fits_extension(self, ext=None):
#         """Returns the FITS extension name."""

#         assert ext is None or ext in ['ivar', 'mask'], 'invalid extension'

#         if ext is None:
#             return self._extension_name.upper()

#         elif ext == 'ivar':
#             if not self.has_ivar():
#                 raise MarvinError('no ivar extension for datacube {0!r}'.format(self.full()))
#             return self._extension_ivar.upper()

#         elif ext == 'mask':
#             if not self.has_mask():
#                 raise MarvinError('no mask extension for datacube {0!r}'.format(self.full()))
#             return self._extension_mask

#     def db_column(self, ext=None):
#         """Returns the name of the DB column containing this datacube."""

#         return self.fits_extension(ext=ext).lower()

#     def __repr__(self):

#         return '<Model {!r}, release={!r}, unit={!r}>'.format(
#             self.name, self.parent.release if self.parent else None, self.unit.to_string())

#     def __str__(self):

#         return self.full()

#     def to_string(self, mode='string', include_channel=True):
#         """Return a string representation of the channel."""

#         if mode == 'latex':

#             if mode in self.formats:
#                 latex = self.formats[mode]
#             else:
#                 latex = self.to_string(include_channel=False)

#             if self.channel and include_channel:
#                 latex = latex + ' ' + self.channel.to_string('latex')

#             return latex

#         else:

#             if mode in self.formats:
#                 string = self.formats[mode]
#             else:
#                 string = self.name

#             if self.channel is None or include_channel is False:
#                 return string
#             else:
#                 return string + ': ' + self.channel.to_string(mode=mode)
