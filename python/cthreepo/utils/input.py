# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-05-29 17:15:16
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-05-30 10:06:08

from __future__ import print_function, division, absolute_import
import os
import re

__all__ = ('read_schema_from_sql')


def _get_schema_table(data):
    ''' Extract a schema and table name from a string value

    Parameters:
        data (str):
            A string containing the "create table .. (" line

    Returns:
        The schema and table name
    '''

    data = data.lower()
    value = data[data.find('table'):data.find('(')].replace("table", '').strip()
    if '.' in value:
        schema, table = value.split('.')
    else:
        schema, table = None, value
    return schema, table


def _get_columns(row):
    ''' Return the column names and dtypes

    Parameters:
        row (str):
            A single string row of a db table column

    Returns:
        A list of column names, and data-types
    '''

    # search for all names in the string separated by spaces up to a comma preceded by space or end-of-string
    columns = re.findall('(\w+)\s(.+?)(,|$)(\s|$)', row)
    names, dtypes, junk, junk = zip(*columns)
    return names, dtypes


def _parse_table(data):
    ''' Parse a table from a string

    Parses a string sql create table statement into
    a dictionary of schema, tablename, columns, and dtypes

    Parameters:
        data (str):
            A string sql table "create table(...);"

    Returns:
        A dictionary of table columns

    '''

    data = data.strip().split('\n')
    table = {}
    names = []
    dtypes = []
    for d in data:
        # process the string row: strip; remove double quotes, end of table, and comments
        d = d.strip().replace('"', '').replace(');', '').split('--')[0]
        if 'create table' in d.lower():
            # handle the first "create table" line
            table['schema'], table['table'] = _get_schema_table(d)
            # check if additional columns after create table segment
            tmp = d[d.find('(') + 1:]
            if tmp:
                colnames, datatypes = _get_columns(tmp)
                names.extend(colnames)
                dtypes.extend(datatypes)
        elif d and not d.strip().startswith('--'):
            # handle all other lines; don't process commented (--) lines
            colnames, datatypes = _get_columns(d)
            names.extend(colnames)
            dtypes.extend(datatypes)
    table['columns'] = names
    table['dtypes'] = dtypes
    return table


def read_schema_from_sql(sqlfile, schema=None, table=None):
    ''' Builds a Datamodel from a DB SQL Schema file

    Parameters:
        sqlfile (str):
            The name of a schema-only sql file for a specific db.schema.table

    '''

    assert os.path.isfile(sqlfile), 'Input SQL file must exist'

    # read the file
    f = open(sqlfile, 'r')
    data = f.read().lower()
    f.close()

    num_tables = data.count('create table')

    # parse the file for sql tables
    tables = [m.start() for m in re.finditer('create table', data)]
    table_ends = [data.find(');', t) for t in tables]

    # create a list of table dictionaries
    alltables = []
    for i, t in enumerate(tables):
        sub = data[t:table_ends[i] + 2]
        table = _parse_table(sub)
        alltables.append(table)

    # if only one table, just return the one dictionary
    if num_tables == 1:
        return alltables[0]

    return alltables

