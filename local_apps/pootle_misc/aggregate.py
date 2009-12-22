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
    raise ImportError
    from django.db.models import Sum, Count
    
    def sum_column(queryset, columns, count=False):
        arg_dict = {}
        if count:
            arg_dict['count'] = Count('id')
        
        for column in columns:
            arg_dict[column] = Sum(column)
        
        return  queryset.aggregate(**arg_dict)

except ImportError:
    from pootle_store.util import dictsum
    
    def sum_column(queryset, columns, count=False):
        initial = {}
        for column in columns:
            initial[column] = 0
        
        result = reduce(dictsum, queryset.values(*columns), initial)
        result['count'] = queryset.count()
        return result

