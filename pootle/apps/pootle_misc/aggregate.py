#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""Wrappers around Django 1.1+ aggregate query functions."""

from django.db.models import Sum, Count, Max


def max_column(queryset, column, default):
    result = queryset.aggregate(result=Max(column))['result']

    if result is None:
        return default
    else:
        return result


def sum_column(queryset, columns, count=False):
    arg_dict = {}

    if count:
        arg_dict['count'] = Count('id')

    for column in columns:
        arg_dict[column] = Sum(column)

    return queryset.aggregate(**arg_dict)
