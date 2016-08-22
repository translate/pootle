# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

"""Wrappers around Django 1.1+ aggregate query functions."""

from django.db.models import Max


def max_column(queryset, column, default):
    result = queryset.aggregate(result=Max(column))['result']
    if result is None:
        return default
    return result
