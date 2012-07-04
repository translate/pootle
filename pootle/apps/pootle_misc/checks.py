#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Zuza Software Foundation
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

from django.utils.translation import ugettext_lazy as _

from translate.filters.decorators import Category

from pootle_app.views.language import dispatch


def get_quality_check_failures(path_obj, dir_stats, include_url=True):
    """Returns a list of the failed checks sorted by their importance.

    :param path_obj: An object which has the ``getcompletestats`` method.
    :param dir_stats: A dictionary of raw stats, as returned by
                      :func:`pootle_misc.stats.get_raw_stats`.
    :param include_url: Whether to include URLs in the returning result
                        or not.
    """
    checks = []
    category_map = {
        Category.CRITICAL: _("Critical"),
        Category.FUNCTIONAL: _("Functional"),
        Category.COSMETIC: _("Cosmetic"),
        Category.EXTRACTION: _("Extraction"),
        Category.NO_CATEGORY: _("No category"),
    }

    try:
        property_stats = path_obj.getcompletestats()
        total = dir_stats['total']['units']
        keys = property_stats.keys()
        keys.sort(reverse=True)

        for i, category in enumerate(keys):
            if category != Category.NO_CATEGORY:
                checks.append({'category': category,
                               'category_display': unicode(category_map[category]),
                               'checks': []})

            cat_keys = property_stats[category].keys()
            cat_keys.sort()

            for checkname in cat_keys:
                checkcount = property_stats[category][checkname]

                if total and checkcount:
                    check = {'name': checkname,
                             'count': checkcount}

                    if include_url:
                        check['url'] = dispatch.translate(path_obj,
                                                          check=checkname)

                    checks[i]['checks'].append(check)
    except IOError:
        pass

    return checks
