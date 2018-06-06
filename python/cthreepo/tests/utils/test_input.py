# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-05-30 10:07:06
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-05-30 11:21:57

from __future__ import print_function, division, absolute_import
from cthreepo.utils.input import read_schema_from_sql, _parse_table
import pytest


table1 = {'table': ("""CREATE TABLE mangadatadb.cube (pk serial PRIMARY KEY NOT NULL, plate INTEGER, mangaid TEXT, designid INTEGER,\n
                    \t\t\t\t\tpipeline_info_pk INTEGER, wavelength_pk INTEGER, ifudesign_pk INTEGER, manga_target_pk integer,\n
                    \t\t\t\t\tspecres double precision[], specresd double precision[], xfocal double precision,\n
                    \t\t\t\t\tyfocal double precision, ra DOUBLE PRECISION, dec DOUBLE PRECISION, cube_shape_pk INTEGER,\n
                    \t\t\t\t\tprespecres double precision[], prespecresd double precision[]);\n"""),
          'count': 17, 'name': 'cube', 'schema': 'mangadatadb', 'columns': ['plate', 'xfocal', 'prespecresd']}

table2 = {'table': ("""CREATE TABLE schema.test (\n    designation character(20),\n    a numeric(10,7),\n
                    "b" numeric(9,7),\n    siga numeric(7,4),\n    sigb numeric(7,4),\n    sigab numeric(8,4),\n
                    glon numeric(10,7),\n    glat numeric(9,7),\n);"""),
          'count': 8, 'schema': 'schema', 'name': 'test', 'columns': ['designation', 'siga', 'b', 'glat']}

table3 = {'table': ("""create table mangadrpall (\n
                    -----------------------------------------------------\n
                    --/H Final summary file of the MaNGA Data Reduction Pipeline (DRP).\n
                    --/T Contains all of the information required to find a given set of spectra for a target.\n
                    -----------------------------------------------------\n
                    plate  bigint  NOT NULL,   --/U --/D Plate ID\n
                    ifudsgn  varchar(20)  NOT NULL, --/U --/D IFU design id (e.g. 12701)\n
                    plateifu  varchar(20)  NOT NULL, --/U --/D Plate+ifudesign name for this object(e.g. 7443-12701)\n
                    mangaid  varchar(20)  NOT NULL,  --/U --/D MaNGA ID for this object (e.g. 1-114145)\n
                    versdrp2  varchar(20)  NOT NULL, --/U --/D Version of DRP used for 2d reductions\n
                    versdrp3  varchar(20)  NOT NULL, --/U --/D Version of DRP used for 3d reductions\n);"""),
          'count': 6, 'schema': None, 'name': 'mangadrpall', 'columns': ['plate', 'ifudsgn', 'versdrp3']}


@pytest.fixture()
def sqlfile(tmpdir):
    p = tmpdir.mkdir("dbtest").join("schemafile.sql")
    data = ('--\n-- PostgreSQL database dump\n--\n\n-- Dumped from database version 9.6.8\n-- Dumped by pg_dump version 9.6.8\n\n'
            '\nSET client_encoding = \'UTF8\';\nSET standard_conforming_strings = on;\n'
            '' + table1['table'] + '\n\n' + table2['table'] + '\n\n' + table3['table'] + '\n\n'
            '\n\n\n--\n-- PostgreSQL database dump complete\n--\n\n')
    p.write(data)
    return p


class TestInput(object):

    @pytest.mark.parametrize('table',
                             [(table1), (table2), (table3)],
                             ids=['table1', 'table2', 'table3'])
    def test_parse_table(self, table):
        tmp = _parse_table(table['table'])
        assert tmp['schema'] == table['schema']
        assert tmp['table'] == table['name']
        assert len(tmp['columns']) == table['count']
        assert set(table['columns']).issubset(set(tmp['columns']))

    def test_read_schema_from_sql(self, sqlfile):
        alltables = read_schema_from_sql(str(sqlfile))
        assert len(alltables) == 3
        schema = [t['schema'] for t in alltables]
        assert schema == ['mangadatadb', 'schema', None]
