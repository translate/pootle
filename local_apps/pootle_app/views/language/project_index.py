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

from django.utils.translation import ugettext as _
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.exceptions import PermissionDenied

from pootle_app.views.top_stats import gentopstats
from pootle_app.models.permissions import get_matching_permissions, check_permission
from pootle_app.models.profile import get_profile
from pootle_app.project_tree import scan_translation_project_files
from pootle_app.views.base import BaseView
from pootle_app.views.language import tp_common
from pootle_app.views import pagelayout

from pootle.i18n.gettext import tr_lang

import dispatch, navbar_dict, item_dict, search_forms

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
        "totalwords":             _("Total Words"),
        # l10n: noun. The graphical representation of translation status
        "progress":               _("Progress"),
        "summary":                _("Summary")
        }

def top_stats(translation_project):
    return gentopstats(lambda query: query.filter(translation_project=translation_project))

################################################################################

class ProjectIndexView(BaseView):
    def GET(self, template_vars, request, translation_project, directory):
        template_vars = super(ProjectIndexView, self).GET(template_vars, request)
        request.permissions = get_matching_permissions(get_profile(request.user), translation_project.directory)
        state    = dispatch.ProjectIndexState(request.GET)
        project  = translation_project.project
        language = translation_project.language

        template_vars.update({
            'project':               {"code": project.code,  "name": project.fullname},
            'language':              {"code": language.code, "name": tr_lang(language.fullname)},
            'search':                search_forms.get_search_form(request),
            'children':              tp_common.get_children(request, translation_project, directory),
            'navitems':              [navbar_dict.make_directory_navbar_dict(request, directory)],
            'stats_headings':        get_stats_headings(),
            'editing':               state.editing,
            'topstats':              top_stats(translation_project),
            'feed_path':             directory.pootle_path[1:],
            })
        return template_vars

def view(request, translation_project, directory):
    request.permissions = get_matching_permissions(get_profile(request.user),
                                                   translation_project.directory)
    if not check_permission("view", request):
        raise PermissionDenied

    view_obj = ProjectIndexView(forms=dict(upload=tp_common.UploadHandler,
                                           update=tp_common.UpdateHandler))
    return render_to_response("language/tp_overview.html",
                         view_obj(request, translation_project, directory),
                              context_instance=RequestContext(request))
