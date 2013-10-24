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

from django.core.paginator import InvalidPage, Paginator


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


def paginate_units(request, queryset, items=30, pages=None):
    """Paginates a `Unit` queryset and returns a list of Page objects."""
    paginator = Paginator(queryset, items)

    if pages is None:
        pages = request.GET.get('pages', '1,2')
    elif isinstance(pages, int):
        pages = str(pages)

    page_list = []
    added_pages = []
    page_numbers = pages.split(',')

    for page_number in page_numbers:
        try:
            page_number = int(page_number)
        except ValueError:
            continue

        try:
            page = paginator.page(page_number)

            if page_number not in added_pages:
                page_list.append(page)
                added_pages.append(page_number)
        except InvalidPage:
            pass

    return page_list
