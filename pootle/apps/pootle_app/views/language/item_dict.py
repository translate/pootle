#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

from pootle_store.models               import Store
from pootle_app.views.language         import dispatch
from pootle_misc.util import add_percentages
from pootle_misc.stats import get_raw_stats


def get_item_summary(request, quick_stats, path_obj):
    translated_words = quick_stats['translatedsourcewords']
    total_words      = quick_stats['totalsourcewords']

    # The translated word counts
    word_stats = _("%(translated)d/%(total)d words (%(translatedpercent)d%%) translated",
                   {"translated": translated_words,
                    "total": total_words,
                    "translatedpercent": quick_stats['translatedpercentage']})

    # The translated unit counts
    string_stats_text = _("%(translated)d/%(total)d strings",
                          {"translated": quick_stats['translated'],
                           "total": quick_stats['total']})
    string_stats = '<span class="string-statistics">[%s]</span>' % string_stats_text

    # The whole string of stats
    if not path_obj.is_dir:
        summary = '%s %s' % (word_stats, string_stats)
    else:
        num_stores = Store.objects.filter(pootle_path__startswith=path_obj.pootle_path).count()
        file_stats = ungettext("%d file", "%d files", num_stores, num_stores)
        summary = '%s %s %s' % (file_stats, word_stats, string_stats)

    return summary

def get_terminology_item_summary(request, quick_stats, path_obj):
    # The translated unit counts
    string_stats_text = _("%(translated)d/%(total)d terms",
                          {"translated": quick_stats['translated'],
                           "total": quick_stats['total']})
    string_stats = '<span class="string-statistics">%s</span>' % string_stats_text

    # The whole string of stats
    if not path_obj.is_dir:
        summary = string_stats
    else:
        num_stores = Store.objects.filter(pootle_path__startswith=path_obj.pootle_path).count()
        file_stats = ungettext("%d file", "%d files", num_stores, num_stores)
        summary = '%s %s' % (file_stats, string_stats)

    return summary

def get_item_stats(request, quick_stats, path_obj, terminology=False):
    if terminology:
        summary = get_terminology_item_summary(request, quick_stats, path_obj)
    else:
        summary = get_item_summary(request, quick_stats, path_obj)

    return {'summary': summary}


def stats_descriptions(quick_stats):
    """Provides a dictionary with two textual descriptions of the work
    outstanding."""

    untranslated = quick_stats["untranslatedsourcewords"]
    fuzzy = quick_stats["fuzzysourcewords"]
    todo_words = untranslated + fuzzy
    todo_text = ungettext("%d word needs attention",
            "%d words need attention", todo_words, todo_words)

    todo_tooltip = u""
    untranslated_tooltip = ungettext("%d word untranslated", "%d words untranslated", untranslated, untranslated)
    fuzzy_tooltip = ungettext("%d word needs review", "%d words need review", fuzzy, fuzzy)
    # Firefox and Opera doesn't actually support newlines in tooltips, so we
    # add some extra space to keep things readable
    todo_tooltip = u"  \n".join([untranslated_tooltip, fuzzy_tooltip])

    return {
        'todo_text': todo_text,
        'todo_words': todo_words,
        'todo_tooltip': todo_tooltip,
    }

def make_generic_item(request, path_obj, action, terminology=False):
    """Template variables for each row in the table.

    make_directory_item() and make_store_item() will add onto these variables."""
    try:
        quick_stats = add_percentages(path_obj.getquickstats())
        info = {
            'href':    action,
            'data':    quick_stats,
            'tooltip': _('%(percentage)d%% complete' %
                         {'percentage': quick_stats['translatedpercentage']}),
            'title':   path_obj.name,
            'stats':   get_item_stats(request, quick_stats, path_obj, terminology),
            }
        errors = quick_stats.get('errors', 0)
        if errors:
            info['errortooltip'] = ungettext('Error reading %d file', 'Error reading %d files', errors, errors)
        info.update(stats_descriptions(quick_stats))
    except IOError, e:
        info = {
            'href': action,
            'title': path_obj.name,
            'errortooltip': e.strerror,
            'data': {'errors': 1},
            }
    return info

def make_directory_item(request, directory, terminology=False):
    action = directory.pootle_path
    item = make_generic_item(request, directory, action, terminology)
    item.update({
            'icon': 'folder',
            'isdir': True})
    return item

def make_store_item(request, store, terminology=False):
    action = dispatch.translate(store)
    item = make_generic_item(request, store, action, terminology)
    item['href_todo'] = dispatch.translate(store, state='incomplete')
    item.update({
            'icon': 'page',
            'isfile': True})
    return item
