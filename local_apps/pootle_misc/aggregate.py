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

"""wrapper around Django 1.1+ aggregate query functions, with alternative implementation for Django 1.0"""

try:
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

        return  queryset.aggregate(**arg_dict)

    def group_by_count(queryset, column):
        result = queryset.values(column).annotate(count=Count(column))
        return dict((item[column], item['count']) for item in result)

    def group_by_sort(queryset, column, fields):
        return queryset.annotate(count=Count(column)).order_by('-count').values('count', *fields)

except ImportError:
    # pure python alternative implementation of aggregate queries

    from pootle_misc.util import dictsum
    from django.core.exceptions import ObjectDoesNotExist

    def max_column(queryset, column, default):
        try:
            return queryset.order_by('-'+column).values_list(column, flat=True)[0]
        except (IndexError, ObjectDoesNotExist):
            return default


    def sum_column(queryset, columns, count=False):
        initial = {}
        for column in columns:
            initial[column] = 0

        result = reduce(dictsum, queryset.values(*columns), initial)
        result['count'] = queryset.count()
        return result

    def group_by_count(queryset, column):
        result = {}
        for item in queryset.values_list(column, flat=True):
            result.setdefault(item, 0)
            result[item] += 1
        return result

    def group_by_sort(queryset, column, fields):
        items = queryset.values('id', *fields).distinct()
        result = []
        for item in items.iterator():
            item['count'] = queryset.filter(id=item['id']).count()
            result.append(item)
        result.sort(key=lambda x: x['count'], reverse=True)
        return result
