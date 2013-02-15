#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2013 Zuza Software Foundation
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

"""Helper functions for the rendering of several items on the index views and
similar pages."""

from django.utils.translation import ugettext as _, ungettext

from pootle_app.views.language import dispatch
from pootle_misc.stats import get_raw_stats


def stats_descriptions(quick_stats):
    """Provides a dictionary with two textual descriptions of the work
    outstanding.
    """
    total_words = quick_stats["total"]["words"]
    untranslated = quick_stats["untranslated"]["words"]
    fuzzy = quick_stats["fuzzy"]["words"]
    todo_words = untranslated + fuzzy

    todo_text = ungettext("%d word needs attention",
                          "%d words need attention", todo_words, todo_words)

    untranslated_tooltip = ungettext("%d word untranslated",
                                     "%d words untranslated",
                                     untranslated, untranslated)
    fuzzy_tooltip = ungettext("%d word needs review",
                              "%d words need review", fuzzy, fuzzy)
    todo_tooltip = u"<br>".join([untranslated_tooltip, fuzzy_tooltip])

    return {
        'total_words': total_words,
        'todo_words': todo_words,
        'todo_text': todo_text,
        'todo_tooltip': todo_tooltip,
    }


def make_generic_item(request, path_obj, action, include_suggestions=False):
    """Template variables for each row in the table.

    :func:`make_directory_item` and :func:`make_store_item` will add onto these
    variables.
    """
    try:
        stats = get_raw_stats(path_obj, include_suggestions)
        info = {
            'href': action,
            'href_all': dispatch.translate(path_obj),
            'href_todo': dispatch.translate(path_obj, state='incomplete'),
            'href_sugg': dispatch.translate(path_obj, state='suggestions'),
            'stats': stats,
            'tooltip': _('%(percentage)d%% complete',
                         {'percentage': stats['translated']['percentage']}),
            'title': path_obj.name,
        }

        errors = stats.get('errors', 0)
        if errors:
            info['errortooltip'] = ungettext('Error reading %d file',
                                             'Error reading %d files',
                                             errors, errors)

        info.update(stats_descriptions(stats))
    except IOError, e:
        info = {
            'href': action,
            'title': path_obj.name,
            'errortooltip': e.strerror,
            'data': {'errors': 1},
            }

    return info


def make_directory_item(request, directory, include_suggestions=False):
    action = directory.pootle_path
    item = make_generic_item(request, directory, action, include_suggestions)
    item.update({
        'icon': 'folder',
        'isdir': True,
    })
    return item


def make_store_item(request, store, include_suggestions=False):
    action = store.pootle_path
    item = make_generic_item(request, store, action, include_suggestions)
    item.update({
        'icon': 'file',
        'isfile': True,
    })
    return item
