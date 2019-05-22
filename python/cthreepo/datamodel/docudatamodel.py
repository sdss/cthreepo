# !/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Filename: docudatamodel.py
# Project: cthreepo
# Author: Brian Cherinka
# Created: Saturday, 1st December 2018 10:40:25 am
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2018 Brian Cherinka
# Last Modified: Wednesday, 22nd May 2019 5:27:50 pm
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import
from docutils import nodes
from docutils.parsers import rst
from docutils.parsers.rst import directives
from docutils import statemachine
import traceback
import importlib
import six
import abc


def _indent(text, level=1):
    ''' Generic indent function for Sphinx rst '''

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


# class DataModelDirective(rst.Directive):
#     ''' '''
#     has_content = False
#     required_arguments = 1
#     option_spec = {
#         'prog': directives.unchanged_required,
#         'title': directives.unchanged,
#         'fits': directives.flag,
#     }

#     def _load_module(self, module_path):
#         """Load the module."""

#         # __import__ will fail on unicode,
#         # so we ensure module path is a string here.
#         module_path = str(module_path)

#         try:
#             module_name, attr_name = module_path.split(':', 1)
#         except ValueError:  # noqa
#             raise self.error('"{0}" is not of format "module:parser"'.format(module_path))

#         try:
#             mod = __import__(module_name, globals(), locals(), [attr_name])
#         except (Exception, SystemExit) as exc:  # noqa
#             err_msg = 'Failed to import "{0}" from "{1}". '.format(attr_name, module_name)
#             if isinstance(exc, SystemExit):
#                 err_msg += 'The module appeared to call sys.exit()'
#             else:
#                 err_msg += 'The following exception was raised:\n{0}'.format(
#                     traceback.format_exc())

#             raise self.error(err_msg)

#         if not hasattr(mod, attr_name):
#             raise self.error('Module "{0}" has no attribute "{1}"'.format(module_name, attr_name))

#         return getattr(mod, attr_name)

#     def _generate_nodes(self, name, command, parent=None, options={}):
#         """Generate the relevant Sphinx nodes.
#         Format a `click.Group` or `click.Command`.
#         :param name: Name of command, as used on the command line
#         :param title: Title of a group`
#         :param command: Instance of `click.Group` or `click.Command`
#         :param parent: Instance of `click.Context`, or None
#         :param show_nested: Whether subcommands should be included in output
#         :returns: A list of nested docutil nodes
#         """

#         # Title
#         source_name = name

#         section = nodes.section(
#             '',
#             nodes.title(text=name),
#             ids=[nodes.make_id(source_name)],
#             names=[nodes.fully_normalize_name(source_name)])

#         # Summary

#         result = statemachine.ViewList()
#         lines = _format_command(name, command, **options)
#         for line in lines:
#             result.append(line, source_name)
#         self.state.nested_parse(result, 0, section)

#         return [section]

#     def run(self):
#         self.env = self.state.document.settings.env

#         command = self._load_module(self.arguments[0])

#         if 'prog' in self.options:
#             prog_name = self.options.get('prog')
#         else:
#             raise self.error(':prog: must be specified')

#         return self._generate_nodes(prog_name, command, None, options=self.options)


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


def _format_table_info(inst):
    ''' Format the Table info '''

    yield '.. code::'
    yield ''
    info = inst._info.split('\n')
    for line in info:
        yield _indent(line)


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
                info = ', '.join(map(str, info))
                yield f'* {val}: {info}'


def _format_changelog(log):
    ''' Format a changlog for a FITS '''

    report = log.generate_report(split=True)
    for line in report:
        yield f'**{line}**' if 'Version' in line else line
        yield ''


def _format_products(obj):
    ''' Format a FuzzyList of Products '''

    yield f'.. list-table::'
    yield _indent(':widths: auto')
    yield _indent(':header-rows: 1')
    yield ''
    yield _indent('* - Name')
    yield _indent('  - Description')
    yield _indent('  - Datatype')
    yield _indent('  - Public')
    yield _indent('  - SDSS Access Path Name')

    for product in obj:
        name = f":ref:`{product.name} <{product.name.lower()}>`"
        yield _indent(f'* - {name}')
        yield _indent(f'  - {product.short}')
        yield _indent(f'  - {product.datatype}')
        yield _indent(f'  - {product.public}')
        path_name = getattr(product, 'path_name', None)
        yield _indent(f'  - {path_name}')


def _format_models(obj):
    ''' Format a FuzzyList of Models '''

    for name, models in obj.items():
        if name == 'versions':
            continue
        yield f'**{name.title()}**'
        yield ''
        for line in _format_model(models):
            yield line


def _format_model(models):
    ''' Format a list of models '''
    yield f'.. list-table::'
    yield _indent(':widths: auto')
    yield _indent(':header-rows: 1')
    yield ''
    yield _indent('* - Name')
    yield _indent('  - Description')

    for model in models:
        yield _indent(f'* - {model.name}')
        yield _indent(f'  - {model.description}')


def load_module(module_path, error=None, products=None):
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

    # check what kind of module
    if products:
        module = mod.dm.products
    else:
        module = mod

    if not hasattr(module, attr_name):
        raise error('Module "{0}" has no attribute "{1}"'.format(module_name, attr_name))

    return getattr(module, attr_name)


class BaseDirective(abc.ABC, rst.Directive):
    ''' Base Directive class '''

    product = None
    add_docstring = None
    add_version = None
    has_content = False
    required_arguments = 1
    final_argument_whitespace = True

    def run(self):
        ''' run the directive and parse the content '''
        self.env = self.state.document.settings.env

        # get the directive argument
        fileclass = self.arguments[0]
        # load the module or object
        obj = load_module(fileclass, products=self.product)
        # define the basic TOC tree
        base_name = self.options['name'].lower().strip().replace(' ', '_')
        toc = self.get_toc(base_name)

        # add a change log
        if 'change' in self.options:
            toc.append(('ChangeLog', base_name + '_changelog'))

        # make the initial main section
        section = self._make_section_main(obj, items=toc, tag=base_name)
        # create the individual sections
        for item in toc:
            section = self._make_section(obj, node=section, title=item[0], refid=item[1])

        return [section]

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

    @abc.abstractmethod
    def get_toc(self, base_name):
        pass

    @abc.abstractmethod
    def get_section_content(self, obj, refid):
        pass
        
    def _make_section_main(self, obj=None, items=None, tag='main'):
        ''' make a section node - main '''
        filename = self.options['name']
        title = nodes.title(text=filename)

        section = nodes.section('', title, ids=[tag], names=[tag])

        # add docstring
        if self.add_docstring:
            docs = [nodes.paragraph(text=i) for i in obj.__doc__.split('\n')]
            section += nodes.line_block('', *docs)

        # add the main toc
        lines = make_list(items, links=True)
        result = statemachine.ViewList()
        for line in lines:
            result.append(line, tag)
        self.state.nested_parse(result, 0, section)

        # add any version information
        if self.add_version:
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

        # generate section content
        lines = self.get_section_content(obj, refid)

        if lines:
            node = self._parse_format(lines, refid, node)

        return node


class ProductDirective(BaseDirective):
    ''' Product Directive '''

    product = True
    add_docstring = True
    add_version = True
    option_spec = {
        'name': directives.unchanged_required,
        'change': directives.flag
    }

    def get_toc(self, base_name):
        pass

    def get_section_content(self, obj, refid):
        pass

    def get_recent_product(self, obj):
        # expand the fits product
        products = obj.expand_product()
        # get most recent
        inst = products[-1]
        return inst


class FitsDirective(ProductDirective):

    def get_toc(self, base_name):
        ''' get a TOC '''
        toc = [('Basic Info', base_name + '_info'), ('Header', base_name + '_header'),
               ('Tables', base_name + '_tables')]
        return toc
    
    def get_section_content(self, obj, refid):
        ''' generate section content for a fits file '''

        # get product instance
        inst = self.get_recent_product(obj)
        # create section content
        lines = None
        if 'info' in refid:
            lines = _format_fits_info(inst)
        elif 'header' in refid:
            lines = _format_fits_header(inst)
        elif 'table' in refid:
            lines = _format_fits_tables(inst)
        elif 'changelog' in refid:
            log = obj.compute_changelog()
            lines = _format_changelog(log)
        
        return lines


class CatalogDirective(ProductDirective):

    def get_toc(self, base_name):
        ''' get a TOC '''
        toc = [('Basic Info', base_name + '_info')]
        return toc

    def get_section_content(self, obj, refid):
        ''' generate section content for a catalog file '''

        # get product instance
        inst = self.get_recent_product(obj)
        # create section content
        lines = None
        if 'info' in refid:
            lines = _format_table_info(inst)
        elif 'changelog' in refid:
            log = obj.compute_changelog()
            lines = _format_changelog(log)

        return lines


class DataModelDirective(BaseDirective):
    option_spec = {
        'name': directives.unchanged_required
    }

    def get_toc(self, base_name):
        ''' get a TOC '''
        toc = [('Products', base_name + '_products'), ('Models', base_name + '_models')]
        return toc

    def get_section_content(self, obj, refid):
        ''' generate section content for a datamodel '''

        # create section content
        lines = None
        if 'product' in refid:
            item = getattr(obj, 'products')
            lines = _format_products(item)
        elif 'models' in refid:
            item = getattr(obj, 'models')
            lines = _format_models(item)

        return lines


def setup(app):
    app.add_directive('fits', FitsDirective)
    app.add_directive('catalog', CatalogDirective)
    app.add_directive('datamodel', DataModelDirective)
