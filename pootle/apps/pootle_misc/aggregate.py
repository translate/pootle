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

def group_by_count(queryset, column):
    result = queryset.values(column).annotate(count=Count(column))
    return dict((item[column], item['count']) for item in result)


def group_by_count_extra(queryset, count_column, extra_column):
    """Similar to :meth:`group_by_count` but returns an extra column which
    is the key in the top level of the returning dictionary.

    :param count_column: Column in which the Count function will be applied.
    :type count_column: str
    :param extra_column: Extra column that will be part of the output and
                         which will be the top-level element in the resulting
                         dictionary.
    :type extra_column: str
    """
    columns = [count_column]
    columns.extend([extra_column])

    result = queryset.values(*columns).annotate(count=Count(count_column))

    rv = {}
    for item in result:
        rv.setdefault(item[extra_column], {}) \
          .update(dict([(item[count_column], item['count'])]))

    return rv


def group_by_sort(queryset, column, fields):
    return queryset.annotate(count=Count(column)).order_by('-count') \
                   .values('count', *fields)
