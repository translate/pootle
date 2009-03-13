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

import copy
import itertools

from django.utils.translation import ugettext as _
from django.utils.translation import ungettext

from pootle_app.profile import get_profile
from pootle_app.fs_models import Search, search_from_state
from pootle_app.url_manip import URL
from pootle_app.store_iteration import get_next_match
from pootle_app.permissions import check_permission

################################################################################

def make_toggle_link(request, url, property, first_option, second_option):
    new_url = copy.deepcopy(url)
    state = new_url.state['translate_display']
    if not getattr(state, property):
        setattr(state, property, True)
        return {'text': first_option,
                'sep':  ' | ',
                'href': new_url.as_relative_to_path_info(request) }
    else:
        setattr(state, property, False)
        return {'text': second_option,
                'sep':  ' | ',
                'href': new_url.as_relative_to_path_info(request) }

################################################################################

def get_item_summary(quick_stats, path_obj, url_state):
    translated_words = quick_stats['translatedsourcewords']
    total_words      = quick_stats['totalsourcewords']
    num_stores       = path_obj.num_stores()
    # Stats showing the number of files
    goal = url_state['search'].goal
    if goal is not None:
        file_stats = _("%d/%d files") % (path_obj.num_stores(goal, num_stores))
    else:
        file_stats = ungettext("%d file", "%d files", num_stores) % num_stores
    # The translated word counts
    word_stats = _("%d/%d words (%d%%) translated") % (translated_words, total_words, quick_stats['translatedpercentage'])
    # The translated unit counts
    string_stats_text = _("%d/%d strings") % (quick_stats['translated'],
                                              quick_stats['total'])
    string_stats = '<span class="string-statistics">[%s]</span>' % string_stats_text
    # The whole string of stats
    return '%s %s %s' % (file_stats, word_stats, string_stats)

def get_item_stats(request, quick_stats, path_obj, url_state):
    result = {
        'summary': get_item_summary(quick_stats, path_obj, url_state),
        'checks':  [],
        'assigns': [] }

    if url_state['translate_display'].show_checks:
        result['checks'] = None  # TBD
    if url_state['translate_display'].show_assigns:
        result['assings'] = None # TBD
    return result

################################################################################

def has_assigned_strings(path_obj, search):
    try:
        get_next_match(path_obj, search=search)
        return True
    except StopIteration:
        return False

def get_assigned_strings(request, assigned_url, path_obj, has_strings):
    if check_permission('translate', request):
        result = { 'text': _('Translate My Strings') }
        assigned_url = assigned_url.copy_and_set('translate_display', view_mode='translate')
    else:
        result = { 'text':  _('View My Strings') }
    if has_strings:
        result.update({
                'href':  assigned_url.as_relative('/'+request.path_info[1:]) })
    else:
        result.update({
                'title': _('No strings assigned to you') })
    return result

def get_quick_assigned_strings(request, assigned_url, path_obj, has_strings):
    assigned_url = assigned_url\
        .copy_and_set('translate_display', view_mode='translate')\
        .copy_and_set('search', match_names=['fuzzy', 'untranslated'])
    text = _('Quick Translate My Strings')
    search = search_from_state(request.translation_project, assigned_url.state['search'])
    if has_strings and has_assigned_strings(path_obj, search):
        return {
            'href':  assigned_url.as_relative_to_path_info(request),
            'text':  text }
    else:
        return {
            'title': _('No untranslated strings assigned to you'),
            'text':  text }

def yield_assigned_links(request, url, path_obj, links_required):
    if 'mine' in links_required and request.user.is_authenticated():
        assigned_url = url.copy_and_set('search', assigned_to=[get_profile(request.user)])
        search = search_from_state(request.translation_project, assigned_url.state['search'])
        has_strings = has_assigned_strings(path_obj, search)
        yield get_assigned_strings(request, url, path_obj, has_strings)
        if 'quick' in links_required and check_permission('translate', request):
            yield get_quick_assigned_strings(request, url, path_obj, has_strings)

def yield_review_link(request, url, links_required, stats_totals):
    if 'review' in links_required and stats_totals.get('check-hassuggestion', 0):
        if check_permission('review', request):
            text = _('Review Suggestions')
            url = url.copy_and_set('translate_display', view_mode='review')
        else:
            text = _('View Suggestions')
        yield { 
            'href': url.copy_and_set('search', match_names=['review']).as_relative_to_path_info(request),
            'text': text }

def yield_quick_link(request, url, links_required, stats_totals):
    if check_permission('translate', request):
        text = _('Quick Translate')
        url = url.copy_and_set('translate_display', view_mode='translate')
    else:
        text = _('View Untraslated')
    if stats_totals['translated'] < stats_totals['total']:
        yield {
            'href': url\
                .copy_and_set('search', match_names=['fuzzy', 'untranslated'])\
                .as_relative_to_path_info(request),
            'text': text }

def yield_translate_all_link(request, url, links_required):
    if check_permission('translate', request):
        url = url.copy_and_set('translate_display', view_mode='translate')
    yield {
        'href': url.as_relative_to_path_info(request),
        'text': _('Translate All') }

def yield_zip_link(request, url, path_obj, links_required):
    if 'zip' in links_required and check_permission('archive', request):
        archive_name = "%s-%s" % (request.translation_project.project.code, 
                                 request.translation_project.language.code)
        if url.state['search'].goal is None:
            if path_obj.is_dir:
                current_folder = path_obj.pootle_path
            else:
                current_folder = path_obj.parent.pootle_path
            archive_name += "-%s.zip" % currentfolder.replace(os.path.sep, "-")
            text = _('ZIP of directory')
        else:
            archive_name += "-%(goal)s.zip?goal=%(goal)s" % url.state['search'].goal.name
            text = _('ZIP of goal')
        yield {
            'href':  archive_name,
            'text':  text,
            'title': archive_name
            }

def yield_sdf_link(request, url, path_obj, links_required):
    if 'sdf' in links_required and \
            check_permission('pocompile', request) and \
            request.translation_project.ootemplate() and \
            path_obj == translation_project.directory:
        archive_name = request.translation_project.language.coed
        yield {
            'href':  archive_name,
            'text':  _('Generate SDF'),
            'title': archive_name
            }

def get_store_extended_links(request, url, path_obj, links_required):
    stats_totals = path_obj.get_stats_totals(request.translation_project.checker)
    return list(itertools.chain(
            yield_assigned_links(request, url, path_obj, links_required),
            yield_review_link(request, url, links_required, stats_totals),
            yield_quick_link(request, url, links_required, stats_totals),
            yield_translate_all_link(request, url, links_required),
            yield_zip_link(request, url, path_obj, links_required),
            yield_sdf_link(request, url, path_obj, links_required)))

def get_default_links_required(links_required):
    if links_required is None:
        return ["mine", "review", "quick", "all"]
    else:
        return links_required

def get_action_links(request, url, path_obj, links_required):
    return {
        'basic': [],
        'extended': get_store_extended_links(request, url, path_obj,
                                             get_default_links_required(links_required)),
        'goalform': None,
        }

################################################################################

def add_percentages(quick_stats):
    quick_stats['translatedpercentage']   = int(100.0 * quick_stats['translatedsourcewords']   / max(quick_stats['totalsourcewords'], 1))
    quick_stats['untranslatedpercentage'] = int(100.0 * quick_stats['untranslatedsourcewords'] / max(quick_stats['totalsourcewords'], 1))
    return quick_stats

def make_generic_item(request, path_obj, translation_url, url_state, links_required):
    search = Search(goal=url_state['search'].goal)
    quick_stats = add_percentages(path_obj.get_quick_stats(request.translation_project.checker, search))
    return {
        'href':    URL(path_obj.pootle_path, url_state).as_relative_to_path_info(request),
        'data':    quick_stats,
        'title':   path_obj.name,
        'stats':   get_item_stats(request, quick_stats, path_obj, url_state),
        'actions': get_action_links(request, translation_url, path_obj, links_required) }

def make_directory_item(request, directory, url_state, links_required=None):
    translation_url = URL(directory.pootle_path).child('translate.html')
    item = make_generic_item(request, directory, translation_url, url_state, links_required)
    item.update({
            'icon':   'folder',
            'isdir':  True })
    return item

def default_store_links_required(store, links_required):
    if links_required is None:
        if store.name.endswith('.po'):
            return ["mine", "review", "quick", "all", "po", "xliff",
                    "ts", "csv", "mo", "update", "commit"]
        else:
            return ["mine", "review", "quick", "all", "po", "xliff",
                    "update", "commit"]
    else:
        return links_required

def make_store_item(request, store, url_state, links_required=None):
    translation_url = URL(store.pootle_path)
    item = make_generic_item(request, store, translation_url, url_state,
                             default_store_links_required(store, links_required))
    item.update({
            'icon':   'file',
            'isfile': True })
    return item
