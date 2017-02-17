# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.schema.base import SchemaTool
from pootle.core.schema.mysql import MySQLSchemaDumper


TEST_MYSQL_SCHEMA_PARAM_NAMES = {
    'defaults': set(['collation', 'character_set']),
    'tables': {
        'fields': set(['collation', 'field', 'type', 'key', 'extra']),
        'indices': set(['key_name', 'non_unique', 'column_name']),
        'constraints': set([
            'referenced_table_name',
            'table_name',
            'referenced_column_name',
            'constraint_name',
            'column_name',
        ]),
    }
}


@pytest.mark.django_db
def test_schema_tool():
    schema_tool = SchemaTool()
    if isinstance(schema_tool.schema_dumper, MySQLSchemaDumper):
        defaults = schema_tool.get_defaults()
        assert set(defaults.keys()) == TEST_MYSQL_SCHEMA_PARAM_NAMES['defaults']
        for app_config in schema_tool.app_configs:
            for table in schema_tool.get_app_tables(app_config):
                row = schema_tool.get_table_fields(table)[0]
                assert (
                    set([x.lower() for x in row.keys()]) ==
                    TEST_MYSQL_SCHEMA_PARAM_NAMES['tables']['fields']
                )
                row = schema_tool.get_table_indices(table)[0]
                assert (
                    set([x.lower() for x in row.keys()]) ==
                    TEST_MYSQL_SCHEMA_PARAM_NAMES['tables']['indices']
                )
                row = schema_tool.get_table_constraints(table)[0]
                assert (
                    set([x.lower() for x in row.keys()]) ==
                    TEST_MYSQL_SCHEMA_PARAM_NAMES['tables']['constraints']
                )
