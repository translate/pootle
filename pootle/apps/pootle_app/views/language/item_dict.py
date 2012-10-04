#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2012 Zuza Software Foundation
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

from django.utils.translation import ugettext as _
from django.utils.translation import ungettext

from pootle_app.views.language import dispatch
from pootle_misc.stats import get_raw_stats
from pootle_misc.util import add_percentages
from pootle_store.models import Store


def get_item_summary(request, stats, path_obj):
    translated_words = stats['translated']['words']
    total_words = stats['total']['words']

    # The translated word counts
    word_stats = _("%(translated)d/%(total)d words (%(translatedpercent)d%%) translated",
                   {"translated": translated_words,
                    "total": total_words,
                    "translatedpercent": stats['translated']['percentage']})

    # The translated unit counts
    string_stats_text = _("%(translated)d/%(total)d strings",
                          {"translated": stats['translated']['units'],
                           "total": stats['total']['units']})
    string_stats = '<span class="string-statistics">[%s]</span>' % string_stats_text

    # The whole string of stats
    if not path_obj.is_dir:
        summary = '%s %s' % (word_stats, string_stats)
    else:
        num_stores = Store.objects.filter(
            pootle_path__startswith=path_obj.pootle_path
        ).count()
        file_stats = ungettext("%d file", "%d files", num_stores, num_stores)
        summary = '%s %s %s' % (file_stats, word_stats, string_stats)

    return summary

def get_terminology_item_summary(request, stats, path_obj):
    # The translated unit counts
    string_stats_text = _("%(translated)d/%(total)d terms",
                          {"translated": stats['translated']['units'],
                           "total": stats['total']['units']})
    string_stats = '<span class="string-statistics">%s</span>' % string_stats_text

    # The whole string of stats
    if not path_obj.is_dir:
        summary = string_stats
    else:
        num_stores = Store.objects.filter(
            pootle_path__startswith=path_obj.pootle_path
        ).count()
        file_stats = ungettext("%d file", "%d files", num_stores, num_stores)
        summary = '%s %s' % (file_stats, string_stats)

    return summary

def get_item_stats(request, stats, path_obj, terminology=False):
    if terminology:
        summary = get_terminology_item_summary(request, stats, path_obj)
    else:
        summary = get_item_summary(request, stats, path_obj)

    return {'summary': summary}


def stats_descriptions(quick_stats):
    """Provides a dictionary with two textual descriptions of the work
    outstanding."""

    untranslated = quick_stats["untranslated"]["words"]
    fuzzy = quick_stats["fuzzy"]["words"]
    todo_words = untranslated + fuzzy
    todo_text = ungettext("%d word needs attention",
            "%d words need attention", todo_words, todo_words)

    todo_tooltip = u""
    untranslated_tooltip = ungettext("%d word untranslated", "%d words untranslated", untranslated, untranslated)
    fuzzy_tooltip = ungettext("%d word needs review", "%d words need review", fuzzy, fuzzy)
    todo_tooltip = u"<br>".join([untranslated_tooltip, fuzzy_tooltip])

    return {
        'todo_text': todo_text,
        'todo_words': todo_words,
        'todo_tooltip': todo_tooltip,
    }


def make_generic_item(request, path_obj, action, include_suggestions=False,
                      terminology=False):
    """Template variables for each row in the table.

    make_directory_item() and make_store_item() will add onto these variables."""
    try:
        stats = get_raw_stats(path_obj, include_suggestions)
        info = {
            'href': action,
            'href_todo': dispatch.translate(path_obj, state='incomplete'),
            'href_sugg': dispatch.translate(path_obj, state='suggestions'),
            'stats': stats,
            'tooltip': _('%(percentage)d%% complete' %
                         {'percentage': stats['translated']['percentage']}),
            'title': path_obj.name,
            'summary': get_item_stats(request, stats, path_obj, terminology),
        }

        errors = stats.get('errors', 0)
        if errors:
            info['errortooltip'] = ungettext('Error reading %d file', 'Error reading %d files', errors, errors)

        info.update(stats_descriptions(stats))
    except IOError, e:
        info = {
            'href': action,
            'title': path_obj.name,
            'errortooltip': e.strerror,
            'data': {'errors': 1},
            }

    return info


def make_directory_item(request, directory, include_suggestions=False,
                        terminology=False):
    action = directory.pootle_path
    item = make_generic_item(request, directory, action, include_suggestions,
                             terminology)
    item.update({
            'icon': 'folder',
            'isdir': True})
    return item


def make_store_item(request, store, include_suggestions=False,
                    terminology=False):
    action = store.pootle_path
    item = make_generic_item(request, store, action, include_suggestions,
                             terminology)
    item.update({
            'icon': 'file',
            'isfile': True})
    return item
