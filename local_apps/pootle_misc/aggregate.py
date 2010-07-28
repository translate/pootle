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

try:
    from django.db.models import Count

    def group_by_sort(queryset, column, fields):
        return queryset.annotate(count=Count(column)).order_by('-count').values('count',*fields)

except ImportError:

    def group_by_sort(queryset, column, fields):
        items = queryset.values('id', *fields).distinct()
        result = []
        for item in items.iterator():
            item['count'] = queryset.filter(id=item['id']).count()
            result.append(item)
        result.sort(key=lambda x: x['count'], reverse=True)
        return result

