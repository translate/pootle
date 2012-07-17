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
    stats['total']['width'] = progressbar_width
    stats['translated']['width'] = \
        (stats['translated']['percentage'] * progressbar_width) / 100
    stats['fuzzy']['width'] = \
        (stats['fuzzy']['percentage'] * progressbar_width) / 100
    stats['untranslated']['width'] = \
        (stats['untranslated']['percentage'] * progressbar_width) / 100


@register.inclusion_tag('progressbar.html', takes_context=True)
def progressbar(context, cur_stats):
    """Inclusion tag that populates the given ``cur_stats`` stats dictionary
    with the proper widths that the rendering progressbar should have.

    This builds a proportional progressbar. The only requirement is that
    the context using this inclusion tag must have a ``stats`` dictionary
    with the totals for that context/directory.

    If the stats say there are no translatable units, nothing is rendered.

    :param cur_stats: Dictionary of quick stats as returned by
                      :func:`pootle_misc.stats.get_raw_stats`
    """
    dir_total_words = context['stats']['total']['words']

    if dir_total_words == 0:
        return {}

    cur_total_words = cur_stats['total']['words']
    progressbar_width = (200 * cur_total_words) / dir_total_words

    add_widths(cur_stats, progressbar_width)

    return {'stats': cur_stats}
