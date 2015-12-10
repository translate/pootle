# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db.models import Max


class SearchSort(object):

    def __init__(self, qs):
        self.qs = qs

    def sort_qs(self, sort_on, sort_by):
        if not sort_by:
            return self.qs.distinct()
        if sort_on == "units":
            return self.sort_on_units(sort_by).distinct()
        return self.sort_on_field(sort_by).distinct()

    def sort_on_units(self, sort_by):
        return self.qs.order_by(sort_by)

    def sort_on_field(self, sort_by):
        if sort_by[0] == '-':
            max_field = sort_by[1:]
            sort_order = '-sort_by_field'
        else:
            max_field = sort_by
            sort_order = 'sort_by_field'
        return (
            self.qs.annotate(sort_by_field=Max(max_field))
                .order_by(sort_order))
