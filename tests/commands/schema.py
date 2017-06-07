# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json
import pytest

from django.core.management import CommandError, call_command

from pootle.core.schema.base import SchemaTool
from pootle.core.schema.utils import get_current_db_type
from pootle.core.schema.dump import SchemaDump


@pytest.mark.cmd
@pytest.mark.django_db
def test_schema_supported_databases(capfd):
    if get_current_db_type() != 'mysql':
        with pytest.raises(CommandError):
            call_command('schema')
        return

    call_command('schema')
    out, err = capfd.readouterr()
    assert '' == err


@pytest.mark.cmd
@pytest.mark.django_db
def test_app_schema_supported_databases(capfd):
    if get_current_db_type() != 'mysql':
        with pytest.raises(CommandError):
            call_command('schema', 'app', 'pootle_store')
        return

    call_command('schema', 'app', 'pootle_store')
    out, err = capfd.readouterr()
    assert '' == err


@pytest.mark.cmd
@pytest.mark.django_db
def test_table_schema_supported_databases(capfd):
    if get_current_db_type() != 'mysql':
        with pytest.raises(CommandError):
            call_command('schema', 'table', 'pootle_store_store')
        return

    call_command('schema', 'table', 'pootle_store_store')
    out, err = capfd.readouterr()
    assert '' == err


@pytest.mark.cmd
@pytest.mark.django_db
def test_schema(capfd):
    if get_current_db_type() != 'mysql':
        pytest.skip("unsupported database")

    call_command('schema')
    out, err = capfd.readouterr()
    schema_tool = SchemaTool()
    result = SchemaDump()
    result.load(json.loads(out))
    assert result.defaults == schema_tool.get_defaults()


@pytest.mark.cmd
@pytest.mark.django_db
def test_schema_tables(capfd):
    if get_current_db_type() != 'mysql':
        pytest.skip("unsupported database")

    call_command('schema', '--tables')
    out, err = capfd.readouterr()
    schema_tool = SchemaTool()
    result = SchemaDump()
    result.load(json.loads(out))
    assert schema_tool.get_tables() == result.tables


def _test_table_result(schema_tool, table_result, table_name):
    assert (table_result.fields ==
            schema_tool.get_table_fields(table_name))
    assert (table_result.indices ==
            schema_tool.get_table_indices(table_name))
    assert (table_result.constraints ==
            schema_tool.get_table_constraints(table_name))


@pytest.mark.cmd
@pytest.mark.django_db
def test_schema_app(capfd):
    if get_current_db_type() != 'mysql':
        pytest.skip("unsupported database")

    call_command('schema', 'app', 'pootle_store')
    out, err = capfd.readouterr()
    result = SchemaDump()
    result.load(json.loads(out))
    schema_tool = SchemaTool('pootle_store')
    for table_name in schema_tool.get_tables():
        table_result = result.apps['pootle_store'].tables[table_name]
        _test_table_result(schema_tool, table_result, table_name)


@pytest.mark.cmd
@pytest.mark.django_db
def test_schema_app_tables(capfd):
    if get_current_db_type() != 'mysql':
        pytest.skip("unsupported database")

    call_command('schema', 'app', 'pootle_store', '--tables')
    out, err = capfd.readouterr()
    schema_tool = SchemaTool('pootle_store')
    result = SchemaDump()
    result.load(json.loads(out))
    assert schema_tool.get_tables() == result.tables


@pytest.mark.cmd
@pytest.mark.django_db
def test_schema_table(capfd):
    if get_current_db_type() != 'mysql':
        pytest.skip("unsupported database")

    call_command('schema', 'table', 'pootle_store_store')
    out, err = capfd.readouterr()
    schema_tool = SchemaTool()
    result = SchemaDump()
    result.load(json.loads(out))
    app_label = schema_tool.get_app_by_table('pootle_store_store')
    table_result = result.apps[app_label].tables['pootle_store_store']
    _test_table_result(schema_tool, table_result, 'pootle_store_store')


@pytest.mark.cmd
@pytest.mark.django_db
def test_schema_multi_table(capfd):
    if get_current_db_type() != 'mysql':
        pytest.skip("unsupported database")

    call_command('schema', 'table', 'pootle_store_store', 'pootle_store_unit')
    out, err = capfd.readouterr()
    schema_tool = SchemaTool()
    result = SchemaDump()
    result.load(json.loads(out))
    app_label = schema_tool.get_app_by_table('pootle_store_store')
    table_result = result.apps[app_label].tables['pootle_store_store']
    _test_table_result(schema_tool, table_result, 'pootle_store_store')
    table_result = result.apps[app_label].tables['pootle_store_unit']
    _test_table_result(schema_tool, table_result, 'pootle_store_unit')


@pytest.mark.cmd
@pytest.mark.django_db
def test_schema_wrong_table():
    if get_current_db_type() != 'mysql':
        pytest.skip("unsupported database")

    with pytest.raises(CommandError):
        call_command('schema', 'table', 'wrong_table_name')


@pytest.mark.cmd
@pytest.mark.django_db
def test_schema_wrong_app():
    if get_current_db_type() != 'mysql':
        pytest.skip("unsupported database")

    with pytest.raises(CommandError):
        call_command('schema', 'app', 'wrong_app_name')
