# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.management import CommandError, call_command

from pootle.core.schema.base import SchemaTool
from pootle.core.utils.json import jsonify


@pytest.mark.cmd
@pytest.mark.django_db
def test_schema(capfd):
    call_command('schema')
    out, err = capfd.readouterr()
    schema_tool = SchemaTool()
    assert jsonify(schema_tool.get_defaults()) in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_schema_tables(capfd):
    call_command('schema', '--tables')
    out, err = capfd.readouterr()
    schema_tool = SchemaTool()
    assert jsonify(schema_tool.get_tables()) in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_schema_app(capfd):
    call_command('schema', 'app', 'pootle_store')
    out, err = capfd.readouterr()
    schema_tool = SchemaTool('pootle_store')
    for table_name in schema_tool.get_tables():
        assert jsonify(schema_tool.get_table_fields(table_name)) in out
        assert jsonify(schema_tool.get_table_indices(table_name)) in out
        assert jsonify(schema_tool.get_table_constraints(table_name)) in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_schema_app_tables(capfd):
    call_command('schema', 'app', 'pootle_store', '--tables')
    out, err = capfd.readouterr()
    schema_tool = SchemaTool('pootle_store')
    assert jsonify(schema_tool.get_tables()) in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_schema_table(capfd):
    call_command('schema', 'table', 'pootle_store_store')
    out, err = capfd.readouterr()
    schema_tool = SchemaTool()
    assert jsonify(schema_tool.get_table_fields('pootle_store_store')) in out
    assert jsonify(schema_tool.get_table_indices('pootle_store_store')) in out
    assert jsonify(
        schema_tool.get_table_constraints('pootle_store_store')) in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_schema_wrong_table():
    with pytest.raises(CommandError):
        call_command('schema', 'table', 'wrong_table_name')


@pytest.mark.cmd
@pytest.mark.django_db
def test_schema_wrong_app():
    with pytest.raises(CommandError):
        call_command('schema', 'app', 'wrong_app_name')
