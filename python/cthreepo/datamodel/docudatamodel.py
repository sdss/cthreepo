# !/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Filename: docudatamodel.py
# Project: cthreepo
# Author: Brian Cherinka
# Created: Saturday, 1st December 2018 10:40:25 am
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2018 Brian Cherinka
# Last Modified: Monday, 13th May 2019 6:00:35 pm
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import
from docutils import nodes
from docutils.parsers import rst
from docutils.parsers.rst import directives
from docutils import statemachine
import traceback
import importlib
import six


def _indent(text, level=1):
    ''' Format Bintypes '''

    prefix = ' ' * (4 * level)

    def prefixed_lines():
        for line in text.splitlines(True):
            yield (prefix + line if line.strip() else line)

    return ''.join(prefixed_lines())

#
# This is the Sphinx directive syntax
#
# directive syntax
# .. name:: arguments  
#    :option: value
#    :option: value
#    
#    body line
#    body line
#

# example - builds directive that will connect to database, run query, and parse/render output
# .. sqltable:: List of Users 
#    :connection_string: sqlite:///sampledata.db
#
#    select 
#       name as 'Name'
#       email as "E-mail"
#    from
#       users
#    order by
#       Name asc
#


class DataModelDirective(rst.Directive):
    ''' '''
    has_content = False
    required_arguments = 1
    option_spec = {
        'prog': directives.unchanged_required,
        'title': directives.unchanged,
        'fits': directives.flag,
    }

    def _load_module(self, module_path):
        """Load the module."""

        # __import__ will fail on unicode,
        # so we ensure module path is a string here.
        module_path = str(module_path)

        try:
            module_name, attr_name = module_path.split(':', 1)
        except ValueError:  # noqa
            raise self.error('"{0}" is not of format "module:parser"'.format(module_path))

        try:
            mod = __import__(module_name, globals(), locals(), [attr_name])
        except (Exception, SystemExit) as exc:  # noqa
            err_msg = 'Failed to import "{0}" from "{1}". '.format(attr_name, module_name)
            if isinstance(exc, SystemExit):
                err_msg += 'The module appeared to call sys.exit()'
            else:
                err_msg += 'The following exception was raised:\n{0}'.format(
                    traceback.format_exc())

            raise self.error(err_msg)

        if not hasattr(mod, attr_name):
            raise self.error('Module "{0}" has no attribute "{1}"'.format(module_name, attr_name))

        return getattr(mod, attr_name)

    def _generate_nodes(self, name, command, parent=None, options={}):
        """Generate the relevant Sphinx nodes.
        Format a `click.Group` or `click.Command`.
        :param name: Name of command, as used on the command line
        :param title: Title of a group`
        :param command: Instance of `click.Group` or `click.Command`
        :param parent: Instance of `click.Context`, or None
        :param show_nested: Whether subcommands should be included in output
        :returns: A list of nested docutil nodes
        """

        # Title
        source_name = name

        section = nodes.section(
            '',
            nodes.title(text=name),
            ids=[nodes.make_id(source_name)],
            names=[nodes.fully_normalize_name(source_name)])

        # Summary

        result = statemachine.ViewList()
        lines = _format_command(name, command, **options)
        for line in lines:
            result.append(line, source_name)
        self.state.nested_parse(result, 0, section)

        return [section]

    def run(self):
        self.env = self.state.document.settings.env

        command = self._load_module(self.arguments[0])

        if 'prog' in self.options:
            prog_name = self.options.get('prog')
        else:
            raise self.error(':prog: must be specified')

        return self._generate_nodes(prog_name, command, None, options=self.options)


def make_list(items, links=False):
    ''' make a list '''
    yield ''
    for item in items:
        if links:
            item, ref = item
            itemstr = f':ref:`{item} <{ref}>`'
        else:
            itemstr = f'{item}'
        yield f'* {itemstr}'
    yield ''


def _format_fits_info(inst):
    ''' Format the FITS info '''

    yield '.. code::'
    yield ''
    info = inst._info.split('\n')
    for line in info:
        yield _indent(line)


def _format_fits_header(inst):
    ''' Format the primary FITS header '''

    yield '.. code::'
    yield ''
    h = inst.hdulist['PRIMARY'].header.tostring(sep='\\n')
    for line in h.split('\\n'):
        yield _indent(line)


def _format_fits_tables(inst):
    ''' Format any FITS tables '''

    yield '.. code::'
    yield ''
    for ext in inst.hdulist:
        if not ext.is_image:
            for line in _format_table(ext):
                yield line


def _format_table(ext):
    ''' Format a single FITS table extension ''' 

    yield f'.. list-table:: {ext.name}'
    yield _indent(':widths: auto')
    yield _indent(':header-rows: 1')
    yield ''
    yield _indent('* - Name')
    yield _indent('  - Format')
    columns = ext.columns
    for col in columns:
        yield _indent(f'* - {col.name}')
        yield _indent(f'  - {col.format}')


def _format_version(obj):
    ''' Format the versions of the FITS '''

    if not hasattr(obj, 'versions'):
        yield ''
        return
    yield ''
    yield 'Available Versions'
    yield ''
    if isinstance(obj.versions, list):
        for val in obj.versions:
            if isinstance(val, six.string_types):
                yield f'* {val}'
            else:
                info = tuple(i for k, i in val.__dict__.items()
                               if not k.startswith('_') and i != str(val))
                yield f'* {val}: {info}'
    # # old code
    # elif isinstance(obj.versions, dict):
    #     for key, val in obj.versions.items():
    #         yield f'* {key}: {val}'


def _format_changelog(inst):
    ''' Format a changlog for a FITS '''

    cl = inst.compute_changelog(input='mangacube', plate=8485, ifu=1901, drpver='v2_0_1', split=True)
    for line in cl:
        yield line
        yield ''


def load_module(module_path, error=None):
    """Load the module."""

    # Exception to raise
    error = error if error else RuntimeError

    # __import__ will fail on unicode,
    # so we ensure module path is a string here.
    module_path = str(module_path)
    try:
        module_name, attr_name = module_path.split(':', 1)
    except ValueError:  # noqa
        raise error('"{0}" is not of format "module:object"'.format(module_path))

    # import the module
    try:
        mod = importlib.import_module(module_name)
    except (Exception, SystemExit) as exc:
        err_msg = 'Failed to import module "{0}". '.format(module_name)
        if isinstance(exc, SystemExit):
            err_msg += 'The module appeared to call sys.exit()'
        else:
            err_msg += 'The following exception was raised:\n{0}'.format(
                traceback.format_exc())

        raise error(err_msg)

    if not hasattr(mod.dm.products, attr_name):
        raise error('Module "{0}" has no attribute "{1}"'.format(module_name, attr_name))

    # old return for cthree.datamodels.manga.base: LogCube
    #return getattr(mod, attr_name)
    # new return
    return mod.dm.products[attr_name]


class FitsDirective(rst.Directive):
    ''' Directive to display a FITS table '''

    has_content = False
    required_arguments = 1
    final_argument_whitespace = True
    option_spec = {
        'name': directives.unchanged_required,
        'change': directives.flag
    }

    def run(self):
        ''' run the directive and parse the content '''

        self.env = self.state.document.settings.env

        # Raise an error if the directive does not have contents.
        #self.assert_has_content()

        # get the directive argument
        fileclass = self.arguments[0]
        # load the module or object
        product_obj = load_module(fileclass)
        # define the basic FITS TOC tree
        base_name = self.options['name'].lower().strip().replace(' ', '_')
        toc = [('Basic Info', base_name + '_info'), ('Header', base_name + '_header'), 
               ('Tables', base_name + '_tables')]

        # add a change log
        if 'change' in self.options:
            toc.append(('ChangeLog', base_name + '_changelog'))

        # make the initial FITS section
        section = self._make_section_main(product_obj, items=toc, tag=base_name)
        # create the individual FITS sections
        # for item in toc:
        #     section = self._make_section(product_obj, node=section, title=item[0], refid=item[1])

        return [section]

    def _make_section_main(self, obj, node=None, items=None, tag='main'):
        ''' make a section node - main '''
        filename = self.options['name']
        title = nodes.title(text=filename)

        section = nodes.section('', title, ids=[tag], names=[tag])

        # add docstring
        docs = [nodes.paragraph(text=i) for i in obj.__doc__.split('\n')]
        section += nodes.line_block('', *docs)

        # add the main toc
        lines = make_list(items, links=True)
        result = statemachine.ViewList()
        for line in lines:
            result.append(line, tag)
        self.state.nested_parse(result, 0, section)

        # add any version information
        lines = _format_version(obj)
        result = statemachine.ViewList()
        for line in lines:
            result.append(line, tag)
        self.state.nested_parse(result, 0, section)
        return section

    def _make_section(self, obj, node=None, title=None, refid=None):
        ''' make a section node '''
        title_node = nodes.title(text=title)

        if refid:
            node = self._make_ref(refid, node)
        section = nodes.section('', title_node, ids=[refid], names=[refid])
        if node:
            node += section
        else:
            node = section

        # instantiate the fits object
        inst = obj()
        lines = None
        if 'info' in refid:
            lines = _format_fits_info(inst)
        elif 'header' in refid:
            lines = _format_fits_header(inst)
        elif 'table' in refid:
            lines = _format_fits_tables(inst)
        elif 'changelog' in refid:
            lines = _format_changelog(inst)

        if lines:
            node = self._parse_format(lines, refid, node)

        return node

    def _make_ref(self, refname, node):
        ''' make a reference link '''
        lines = [f'.. _{refname}:']
        result = statemachine.ViewList()
        for line in lines:
            result.append(line, 'tables')
        self.state.nested_parse(result, 0, node)
        return node

    def _parse_format(self, lines, tag, node):
        ''' parse the RST format and add into a node '''
        result = statemachine.ViewList()
        for line in lines:
            result.append(line, tag)
        self.state.nested_parse(result, 0, node)
        return node


def setup(app):
    app.add_directive('fits', FitsDirective)
    app.add_directive('datamodel', DataModelDirective)
