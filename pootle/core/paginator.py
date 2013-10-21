#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Evernote Corporation
# Copyright 2014 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

from django.core.paginator import Paginator


def paginate(request, queryset, items=30, page=None):
    paginator = Paginator(queryset, items)

    if page is None:
        try:
            page = int(request.GET.get('page', 1))
        except ValueError:
            # It wasn't an int, so use 1.
            page = 1
    # If page value is too large.
    page = min(page, paginator.num_pages)

    return paginator.page(page)
