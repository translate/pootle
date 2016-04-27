# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

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
