# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db import connection


def get_current_db_type():
    with connection.cursor() as cursor:
        if hasattr(cursor.db, "mysql_version"):
            return 'mysql'
        return cursor.db.settings_dict['ENGINE'].split('.')[-1]
