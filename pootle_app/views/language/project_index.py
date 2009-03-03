#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2009 Zuza Software Foundation
# 
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# Pootle is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pootle; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import copy

from django.utils.translation import ugettext as _

from pootle_app.views.util import render_to_kid, render_jtoolkit, KidRequestContext
from pootle_app.views.top_stats import gen_top_stats, top_stats_heading
from pootle_app.views.common import navbar_dict, item_dict, search_forms
from pootle_app.goals import Goal
from pootle_app.fs_models import Directory, Search
from pootle_app.url_manip import URL, TranslateDisplayState, read_all_state
from pootle_app.permissions import get_matching_permissions
from pootle_app.profile import get_profile

from Pootle.i18n.jtoolkit_i18n import tr_lang
from Pootle import pan_app

################################################################################

def get_stats_headings():
    """returns a dictionary of localised headings"""
    return {
        "name":                   _("Name"),
        "translated":             _("Translated"),
        "translatedpercentage":   _("Translated percentage"),
        "translatedwords":        _("Translated words"),
        "fuzzy":                  _("Fuzzy"),
        "fuzzypercentage":        _("Fuzzy percentage"),
        "fuzzywords":             _("Fuzzy words"),
        "untranslated":           _("Untranslated"),
        "untranslatedpercentage": _("Untranslated percentage"),
        "untranslatedwords":      _("Untranslated words"),
        "total":                  _("Total"),
        "totalwords":             _("Total words"),
        # l10n: noun. The graphical representation of translation status
        "progress":               _("Progress"),
        "summary":                _("Summary")
        }

################################################################################

def get_children(request, translation_project, directory, url_state):
    store_url_state = copy.deepcopy(url_state)
    store_url_state['translate_display'] = TranslateDisplayState(initial={'view_mode': 'translate',
                                                                          'editing':   True})
    return [item_dict.make_directory_item(request, child_dir, url_state)
            for child_dir in directory.child_dirs.all()] + \
           [item_dict.make_store_item(request, child_store, store_url_state)
            for child_store in directory.filter_stores(Search(**url_state['search'].as_dict())).all()]

################################################################################

def top_stats(translation_project):
    return gen_top_stats(lambda query: query.filter(translation_project=translation_project))

def view(request, translation_project, directory):
    project  = translation_project.project
    language = translation_project.language

    if request.method == 'POST':
        pass

    request.current_path = directory.pootle_path
    request.permissions = get_matching_permissions(get_profile(request.user), translation_project.directory)
    url_state = read_all_state(request.GET)
    del url_state['position']
    template_vars = {
        'pagetitle':             _('%s: Project %s, Language %s') % \
            (pan_app.get_title(), project.fullname, tr_lang(language.fullname)),
        'project':               {"code": project.code,  "name": project.fullname},
        'language':              {"code": language.code, "name": tr_lang(language.fullname)},
        'search':                search_forms.get_search_form(request),
        'children':              get_children(request, translation_project, directory, url_state),
        'navitems':              [navbar_dict.make_navbar_dict(request, directory, url_state)],
        'stats_headings':        get_stats_headings(),
        'editing':               url_state['translate_display'].editing,
        'untranslated_text':     _("%s untranslated words"),
        'fuzzy_text':            _("%s fuzzy words"),
        'complete':              _("Complete"),
        'topstats':              top_stats(translation_project),
        'topstatsheading':       top_stats_heading()
        }

    return render_to_kid("fileindex.html", KidRequestContext(request, template_vars))
