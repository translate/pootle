# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.apps import apps
from django.conf import settings
from django.db import connection

from .mysql import MySQLSchemaDumper
from .checks import MySQLDefaultsChecker


class SchemaTool(object):
    def __init__(self, *app_labels):
        self.schema_dumper = None
        if not app_labels:
            app_labels = [app_label.split('.')[-1]
                          for app_label in settings.INSTALLED_APPS]

        self.app_configs = [apps.get_app_config(app_label)
                            for app_label in app_labels]

        with connection.cursor() as cursor:
            if hasattr(cursor.db, "mysql_version"):
                self.schema_dumper = MySQLSchemaDumper()
                self.schema_checker = MySQLDefaultsChecker()

    def get_tables(self):
        tables = []
        for app_config in self.app_configs:
             tables += self.get_app_tables(app_config)
        return tables

    def get_app_tables(self, app_config):
        return [model._meta.db_table
                for model in app_config.get_models(include_auto_created=True)]

    def get_defaults(self):
        if self.schema_dumper is not None:
            return self.schema_dumper.get_defaults()

    def get_table_fields(self, table_name):
        if self.schema_dumper is not None:
            return self.schema_dumper.get_table_fields(table_name)

    def get_table_indices(self, table_name):
        if self.schema_dumper is not None:
            return self.schema_dumper.get_table_indices(table_name)

    def get_table_constraints(self, table_name):
        if self.schema_dumper is not None:
            return self.schema_dumper.get_table_constraints(table_name)

    def check(self):
        return self.schema_checker.check(self.get_defaults())

    @property
    def state(self):
        return self.schema_checker.state(self.get_defaults())
