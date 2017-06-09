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
from pootle.core.schema.utils import get_current_db_type
from pootle.core.utils.json import jsonify


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
    assert jsonify(schema_tool.get_defaults()) in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_schema_tables(capfd):
    if get_current_db_type() != 'mysql':
        pytest.skip("unsupported database")

    call_command('schema', '--tables')
    out, err = capfd.readouterr()
    schema_tool = SchemaTool()
    assert jsonify(schema_tool.get_tables()) in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_schema_app(capfd):
    if get_current_db_type() != 'mysql':
        pytest.skip("unsupported database")

    call_command('schema', 'app', 'pootle_store')
    out, err = capfd.readouterr()
    schema_tool = SchemaTool('pootle_store')
    for table_name in schema_tool.get_tables():
        assert jsonify(schema_tool.get_table_fields(table_name)) in out
        assert jsonify(schema_tool.get_table_indices(table_name)) in out
        assert jsonify(
            schema_tool.get_table_constraints(table_name)) in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_schema_app_tables(capfd):
    if get_current_db_type() != 'mysql':
        pytest.skip("unsupported database")

    call_command('schema', 'app', 'pootle_store', '--tables')
    out, err = capfd.readouterr()
    schema_tool = SchemaTool('pootle_store')
    assert jsonify(schema_tool.get_tables()) in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_schema_table(capfd):
    if get_current_db_type() != 'mysql':
        pytest.skip("unsupported database")

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
