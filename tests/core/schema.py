# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json
import pytest

from pootle.core.schema.base import SchemaTool, UnsupportedDBError
from pootle.core.schema.utils import get_current_db_type
from pootle.core.schema.dump import SchemaDump


TEST_MYSQL_SCHEMA_PARAM_NAMES = {
    'defaults': set(['collation', 'character_set']),
    'tables': {
        'fields': set(['collation', 'type', 'key', 'extra']),
        'indices': set(['non_unique', 'column_name', 'column_names']),
        'constraints': set([
            'referenced_table_name',
            'table_name',
            'referenced_column_name',
            'column_name',
            'column_names',
        ]),
    }
}


@pytest.mark.django_db
def test_schema_tool_supported_database():
    if get_current_db_type() != 'mysql':
        with pytest.raises(UnsupportedDBError):
            SchemaTool()
        return

    assert SchemaTool()


@pytest.mark.django_db
def test_schema_tool():
    if get_current_db_type() != 'mysql':
        pytest.skip("unsupported database")

    schema_tool = SchemaTool()
    defaults = schema_tool.get_defaults()
    assert set(defaults.keys()) == TEST_MYSQL_SCHEMA_PARAM_NAMES['defaults']
    for app_label in schema_tool.app_configs:
        for table in schema_tool.get_app_tables(app_label):
            row = schema_tool.get_table_fields(table).values()[0]
            assert (
                set([x.lower() for x in row.keys()]).issubset(
                    TEST_MYSQL_SCHEMA_PARAM_NAMES['tables']['fields'])
            )
            row = schema_tool.get_table_indices(table).values()[0]
            assert (
                set([x.lower() for x in row.keys()]).issubset(
                    TEST_MYSQL_SCHEMA_PARAM_NAMES['tables']['indices'])
            )
            row = schema_tool.get_table_constraints(table).values()[0]
            assert (
                set([x.lower() for x in row.keys()]).issubset(
                    TEST_MYSQL_SCHEMA_PARAM_NAMES['tables']['constraints'])
            )


@pytest.mark.django_db
def test_schema_dump(test_fs):
    if get_current_db_type() != 'mysql':
        pytest.skip("unsupported database")

    schema_tool = SchemaTool()
    expected_result = SchemaDump()
    with test_fs.open(['data', 'schema.json']) as f:
        expected_result.load(data=json.loads(f.read()))

    assert expected_result.defaults == schema_tool.get_defaults()
    for app_label in schema_tool.app_configs:
        expected_app_result = expected_result.get_app(app_label)
        for table_name in schema_tool.get_app_tables(app_label):
            expected_table_result = expected_app_result.get_table(table_name)
            assert (schema_tool.get_table_fields(table_name) ==
                    expected_table_result.fields)
            assert (schema_tool.get_table_indices(table_name) ==
                    expected_table_result.indices)
            assert (schema_tool.get_table_constraints(table_name) ==
                    expected_table_result.constraints)
