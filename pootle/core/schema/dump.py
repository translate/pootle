# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json
from collections import OrderedDict

from pootle.core.utils.json import PootleJSONEncoder


class JSONOutput(object):
    indent = 4

    def out(self, obj):
        return json.dumps(obj, indent=self.indent, cls=PootleJSONEncoder)


class BaseSchemaDump(object):
    out_class = JSONOutput

    def __init__(self):
        self._data = OrderedDict()

    def load(self, data):
        self._data.update(data)

    def __str__(self):
        return self.out_class().out(self._data)


class SchemaTableDump(BaseSchemaDump):
    def __init__(self, name):
        self.name = name
        self.fields = None
        self.indices = None
        self.constraints = None
        super(SchemaTableDump, self).__init__()

    def load(self, data):
        attr_names = ['fields', 'indices', 'constraints']
        for attr_name in attr_names:
            if attr_name in data:
                setattr(self, attr_name, data[attr_name])
        super(SchemaTableDump, self).load(data)


class SchemaAppDump(BaseSchemaDump):
    def __init__(self, name):
        self.name = name
        self.tables = OrderedDict()
        super(SchemaAppDump, self).__init__()
        self._data['tables'] = OrderedDict()

    def load(self, data):
        if 'tables' in data:
            for table_name in data['tables']:
                table_dump = SchemaTableDump(table_name)
                table_dump.load(data['tables'][table_name])
                self.add_table(table_dump)

    def add_table(self, table_dump):
        self.tables[table_dump.name] = table_dump
        self._data['tables'][table_dump.name] = table_dump._data

    def get_table(self, table_name):
        return self.tables.get(table_name, None)


class SchemaDump(BaseSchemaDump):

    def __init__(self):
        self.defaults = None
        self.apps = OrderedDict()
        super(SchemaDump, self).__init__()
        self._data['apps'] = OrderedDict()

    def load(self, data):
        if 'defaults' in data:
            self.defaults = data['defaults']
            self._data['defaults'] = self.defaults
        if 'apps' in data:
            for app_label in data['apps']:
                app_dump = SchemaAppDump(app_label)
                app_dump.load(data['apps'][app_label])
                self.add_app(app_dump)
        if 'tables' in data:
            self.tables = data['tables']
            self._data['tables'] = self.tables

    def add_app(self, app_dump):
        self.apps[app_dump.name] = app_dump
        self._data['apps'][app_dump.name] = app_dump._data

    def app_exists(self, app_label):
        return app_label in self.apps

    def get_app(self, app_label):
        return self.apps.get(app_label, None)

    def set_table_list(self, data):
        self.load(data={'tables': data})
