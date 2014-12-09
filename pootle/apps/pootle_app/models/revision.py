#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from django.db import models, connections


class RevisionManager(models.Manager):

    def inc(self):
        cursor = connections[self.db].cursor()
        cursor.execute("UPDATE %(table)s "
                       "SET %(c_field)s = LAST_INSERT_ID(%(c_field)s + 1) " %
                       {
                           'table': self.model._meta.db_table,
                           'c_field': 'counter'
                       })
        cursor.execute('SELECT LAST_INSERT_ID()')

        result = cursor.fetchall()

        return result[0][0]

    def last(self):
        """Returns the latest revision number."""
        try:
            return self.get_queryset().values_list('counter')[0][0]
        except IndexError:
            return 0


class Revision(models.Model):
    counter = models.IntegerField(null=False, default=0)

    objects = RevisionManager()

    class Meta:
        app_label = "pootle_app"
