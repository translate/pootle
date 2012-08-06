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

from django import template


register = template.Library()


def add_widths(stats, progressbar_width):
    """Adds widths to the ``stats`` dictionary according to the
    ``progressbar_width``.
    """
    if progressbar_width < 30:
        progressbar_width = 30

    stats['total']['width'] = progressbar_width
    stats['translated']['width'] = \
        (stats['translated']['percentage'] * progressbar_width) / 100
    stats['fuzzy']['width'] = \
        (stats['fuzzy']['percentage'] * progressbar_width) / 100
    stats['untranslated']['width'] = \
        (stats['untranslated']['percentage'] * progressbar_width) / 100


@register.inclusion_tag('progressbar.html', takes_context=True)
def progressbar(context, cur_stats, total_words=None):
    """Inclusion tag that populates the given ``cur_stats`` stats dictionary
    with the proper widths that the rendering progressbar should have.

    If ``total_words`` is given, this builds a proportional progressbar.
    If the ``total_words`` is 0, nothing is rendered.

    :param cur_stats: Dictionary of quick stats as returned by
                      :func:`pootle_misc.stats.get_raw_stats`
    :param total_words: Total translatable words for the context of the
                        building progressbar. If given, this will result
                        in proportional progressbars.
    """
    proportional = True
    if total_words is None:
        proportional = False

    if proportional and total_words == 0:
        return {}

    cur_total_words = cur_stats['total']['words']
    if proportional:
        progressbar_width = (200 * cur_total_words) / total_words
    else:
        progressbar_width = 100

    add_widths(cur_stats, progressbar_width)

    return {'stats': cur_stats}
