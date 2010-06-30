#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2009 Zuza Software Foundation
#
# This file is part of translate.
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

from django.shortcuts import get_object_or_404, render_to_response
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
from django.template import RequestContext
from django.core.exceptions import PermissionDenied

from pootle_app.views.language.view import get_stats_headings
from pootle_app.views.language.item_dict import nice_percentage, add_percentages, stats_descriptions
from pootle_app.views import pagelayout
from pootle_app.views.top_stats import gentopstats_language
from pootle_language.models import Language
from pootle_statistics.models import Submission

from pootle.i18n.gettext import tr_lang

from pootle_app.models.permissions import get_matching_permissions, check_permission
from pootle_app.views.admin.permissions import admin_permissions
from pootle_profile.models import get_profile

def limit(query):
    return query[:5]

def get_last_action(translation_project):
    try:
        return Submission.objects.filter(translation_project=translation_project).latest()
    except Submission.DoesNotExist:
        return ''

def make_project_item(translation_project):
    project = translation_project.project
    href = translation_project.pootle_path
    projectstats = add_percentages(translation_project.getquickstats())
    info = {
        'code': project.code,
        'href': href,
        'icon': 'folder',
        'title': project.fullname,
        'description': project.description,
        'data': projectstats,
        'lastactivity': get_last_action(translation_project),
        'isproject': True,
        'tooltip': _('%(percentage)d%% complete',
                     {'percentage': projectstats['translatedpercentage']})
    }
    errors = projectstats.get('errors', 0)
    if errors:
        info['errortooltip'] = ungettext('Error reading %d file', 'Error reading %d files', errors, errors)
    info.update(stats_descriptions(projectstats))
    return info

def language_index(request, language_code):
    language = get_object_or_404(Language, code=language_code)
    request.permissions = get_matching_permissions(get_profile(request.user), language.directory)

    if not check_permission("view", request):
        raise PermissionDenied

    projects = language.translationproject_set.order_by('project__fullname')
    projectcount = len(projects)
    items = (make_project_item(translate_project) for translate_project in projects.iterator())

    totals = language.getquickstats()
    average = nice_percentage(totals['translatedsourcewords'] * 100.0 / max(totals['totalsourcewords'], 1))
    topstats = gentopstats_language(language)

    templatevars = {
        'language': {
          'code': language.code,
          'name': tr_lang(language.fullname),
          'stats': ungettext('%(projects)d project, %(average)d%% translated',
                             '%(projects)d projects, %(average)d%% translated',
                             projectcount, {"projects": projectcount, "average": average}),
        },
        'feed_path': '%s/' % language.code,
        'projects': items,
        'statsheadings': get_stats_headings(),
        'topstats': topstats,
        'instancetitle': pagelayout.get_title(),
        }
    return render_to_response("language/language_index.html", templatevars, context_instance=RequestContext(request))

def language_admin(request, language_code):
    # Check if the user can access this view
    language = get_object_or_404(Language, code=language_code)
    request.permissions = get_matching_permissions(get_profile(request.user),
                                                   language.directory)
    if not check_permission('administrate', request):
        raise PermissionDenied(_("You do not have rights to administer this language."))

    template_vars = {
        "language":               { 'code': language_code,
                                    'name': tr_lang(language.fullname) },
        "directory":              language.directory,
        "feed_path":              '%s/' % language.code,
    }
    return admin_permissions(request, language.directory, "language/language_admin.html", template_vars)
