# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

"""Wrappers around Django 1.1+ aggregate query functions."""

from django.db.models import Count, Max, Sum


def max_column(queryset, column, default):
    result = queryset.aggregate(result=Max(column))['result']
    if result is None:
        return default
    return result


def sum_column(queryset, columns, count=False):
    arg_dict = {}

    if count:
        arg_dict['count'] = Count('id')

    for column in columns:
        arg_dict[column] = Sum(column)

    return queryset.aggregate(**arg_dict)
