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

import itertools

from django.utils.translation import ugettext as _
from django.utils.translation import ungettext as _N

from translate.storage import versioncontrol
from pootle_app.models.permissions     import check_permission
from pootle_store.models               import Store
from pootle_app.views.language         import dispatch

################################################################################

def get_item_summary(request, quick_stats, path_obj):
    translated_words = quick_stats['translatedsourcewords']
    total_words      = quick_stats['totalsourcewords']
    num_stores       = Store.objects.filter(pootle_path__startswith=path_obj.pootle_path).count()
    state            = dispatch.CommonState(request.GET)
    file_stats = _N("%d file", "%d files", num_stores, num_stores)
    # The translated word counts
    word_stats = _("%(translated)d/%(total)d words (%(translatedpercent)d%%) translated",
                   {"translated": translated_words,
                    "total": total_words,
                    "translatedpercent": quick_stats['translatedpercentage']}
                   )
    # The translated unit counts
    string_stats_text = _("%(translated)d/%(total)d strings",
                          {"translated": quick_stats['translated'],
                           "total": quick_stats['total']}
                          )
    string_stats = '<span class="string-statistics">[%s]</span>' % string_stats_text
    # The whole string of stats
    return '%s %s %s' % (file_stats, word_stats, string_stats)

def get_item_stats(request, quick_stats, path_obj, show_checks=False):
    result = {
        'summary': get_item_summary(request, quick_stats, path_obj),
        'checks':  [],
        }
    if show_checks:
        result['checks'] = getcheckdetails(request, path_obj)
    return result

def getcheckdetails(request, path_obj, url_opts={}):
    """return a list of strings describing the results of
    checks"""

    property_stats = path_obj.getcompletestats(request.translation_project.checker)
    total = property_stats['total']
    checklinks = []
    keys = property_stats.keys()
    keys.sort()
    for checkname in keys:
        if not checkname.startswith('check-'):
            continue
        checkcount = property_stats[checkname]
        if total and checkcount:
            stats = _N('%(checks)d string (%(checkspercent)d%%) failed',
                              '%(checks)d strings (%(checkspercent)d%%) failed', checkcount,
                              {"checks": checkcount, "checkspercent": (checkcount * 100) / total}
                      )
            #url_opts[str(checkname)] = 1
            checklink = {'href': dispatch.translate(request, path_obj.pootle_path, match_names=[checkname]),
                         'text': checkname.replace('check-', '', 1),
                         'stats': stats}
            #del url_opts[str(checkname)]
            checklinks += [checklink]
    return checklinks

################################################################################

def review_link(request, path_obj):
    if path_obj.getcompletestats().get('check-hassuggestion', 0):
        if check_permission('translate', request):
            text = _('Review Suggestions')
        else:
            text = _('View Suggestions')
        return { 
            'href': dispatch.translate(request, path_obj.pootle_path, match_names=['check-hassuggestion']),
            'text': text }

def quick_link(request, path_obj):
    if path_obj.getquickstats()['translated'] < path_obj.getquickstats()['total']:
        if check_permission('translate', request):
            text = _('Quick Translate')
        else:
            text = _('View Untranslated')
        return {
            'href': dispatch.translate(request, path_obj.pootle_path, match_names=['fuzzy', 'untranslated']),
            'text': text }

def translate_all_link(request, path_obj):
    #FIXME: what permissions to check for here?
    return {
        'href': dispatch.translate(request, path_obj.pootle_path),
        'text': _('Translate All') }

def zip_link(request, path_obj):
    if check_permission('archive', request):
        text = _('ZIP of directory')
        link = dispatch.download_zip(request, path_obj)
        return {
            'href':  link,
            'text':  text,
            }

def po_link(request, path_obj):
    href = dispatch.export(request, path_obj.pootle_path, 'po')
    return {
        'href':  href,
        'text':  _('Download PO'),
        }
    
def xliff_link(request, path_obj):
    text = _('Download XLIFF')
    href = dispatch.export(request, path_obj.pootle_path, 'xlf')
    return {
        'href':  href,
        'text':  text,

        }

def commit_link(request, path_obj):
    if check_permission('commit', request) and versioncontrol.hasversioning(request.translation_project.real_path):
        link = dispatch.commit(request, path_obj)
        text = _('Commit to VCS')
        return {
            'href': link,
            'text': text,
            'link': link,
        }

def update_link(request, path_obj):
    if check_permission('commit', request) and versioncontrol.hasversioning(request.translation_project.real_path):
        link = dispatch.update(request, path_obj)
        text = _('Update from VCS')
        return {
            'href': link,
            'text': text,
            'link': link,
        }

def _gen_link_list(request, path_obj, linkfuncs):
    links = []
    for linkfunc in linkfuncs:
        link = linkfunc(request, path_obj)
        if link is not None:
            links.append(link)
    return links

def store_translate_links(request, path_obj):
    """returns a list of links for store items in translate tab"""
    return _gen_link_list(request, path_obj, [quick_link, translate_all_link,
                                              po_link, xliff_link, 
                                              update_link, commit_link])
def store_review_links(request, path_obj):
    """returns a list of links for store items in review tab"""
    return _gen_link_list(request, path_obj, [review_link, po_link, xliff_link,
                                              commit_link, update_link])

def directory_translate_links(request, path_obj):
    """returns a list of links for directory items in translate tab"""
    return _gen_link_list(request, path_obj, [quick_link, translate_all_link, zip_link])

def directory_review_links(request, path_obj):
    """returns a list of links for directory items in review tab"""
    return _gen_link_list(request, path_obj, [review_link, zip_link])


################################################################################

def add_percentages(quick_stats):
    """Add percentages onto the raw stats dictionary."""
    quick_stats['translatedpercentage']   = int(100.0 * quick_stats['translatedsourcewords']   / max(quick_stats['totalsourcewords'], 1))
    quick_stats['fuzzypercentage'] = int(100.0 * quick_stats['fuzzysourcewords'] / max(quick_stats['totalsourcewords'], 1))
    quick_stats['untranslatedpercentage'] = 100 - quick_stats['translatedpercentage'] - quick_stats['fuzzypercentage']
    return quick_stats

def stats_descriptions(quick_stats):
    """Provides a dictionary with two textual descriptions of the work
    outstanding."""

    untranslated = quick_stats["untranslatedsourcewords"]
    fuzzy = quick_stats["fuzzysourcewords"]
    todo_words = untranslated + fuzzy
    todo_text = _N("%d word need attention",
            "%d words need attention", todo_words, todo_words)

    todo_tooltip = u""
    untranslated_tooltip = _N("%d word untranslated", "%d words untranslated", untranslated, untranslated)
    fuzzy_tooltip = _N("%d word need review", "%d words need review", fuzzy, fuzzy)
    # Firefox and Opera doesn't actually support newlines in tooltips, so we
    # add some extra space to keep things readable
    todo_tooltip = u"  \n".join([untranslated_tooltip, fuzzy_tooltip])

    return {
        'todo_text': todo_text,
        'todo_tooltip': todo_tooltip,
    }

def make_generic_item(request, path_obj, action, show_checks=False):
    """Template variables for each row in the table.

    make_directory_item() and make_store_item() will add onto these variables."""
    quick_stats = add_percentages(path_obj.getquickstats())

    info = {
        'href':    action,
        'data':    quick_stats,
        'title':   path_obj.name,
        'stats':   get_item_stats(request, quick_stats, path_obj, show_checks),
        }
    info.update(stats_descriptions(quick_stats))
    return info

def make_directory_item(request, directory, links_required=None):
    action = dispatch.show_directory(request, directory.pootle_path)
    show_checks = links_required == 'review'
    item = make_generic_item(request, directory, action, show_checks)
    if links_required == 'translate':
        item['actions'] = directory_translate_links(request, directory)
    elif links_required == 'review':
        item['actions'] = directory_review_links(request, directory)
    else:
        item['actions'] = []
    item.update({
            'icon':   'folder',
            'isdir':  True })
    return item

def make_store_item(request, store, links_required=None):
    action = dispatch.translate(request, store.pootle_path)
    show_checks = links_required == 'review'
    item = make_generic_item(request, store, action, show_checks)
    if links_required == 'translate':
        item['actions'] = store_translate_links(request, store)
    elif links_required == 'review':
        item['actions'] = store_review_links(request, store)
    else:
        item['actions'] = []
    item.update({
            'icon':   'file',
            'isfile': True })
    return item
