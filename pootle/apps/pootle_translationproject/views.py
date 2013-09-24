#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2012 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
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

from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ungettext

from pootle.core.decorators import (get_path_obj, get_resource_context,
                                    permission_required)
from pootle.core.helpers import (get_export_view_context,
                                 get_translation_context)
from pootle_app.views.admin.permissions import admin_permissions as admin_perms
from pootle_misc.browser import get_children, get_table_headings
from pootle_misc.checks import get_quality_check_failures
from pootle_misc.stats import (get_raw_stats, get_translation_stats,
                               get_translate_actions)
from pootle_misc.util import ajax_required


@get_path_obj
@permission_required('administrate')
def admin_permissions(request, translation_project):
    language = translation_project.language
    project = translation_project.project

    template_vars = {
        'translation_project': translation_project,
        "project": project,
        "language": language,
        "directory": translation_project.directory,
    }

    return admin_perms(request, translation_project.directory,
                       "translation_projects/admin/permissions.html",
                       template_vars)


@get_path_obj
@permission_required('view')
@get_resource_context
def overview(request, translation_project, dir_path, filename=None):
    project = translation_project.project
    language = translation_project.language

    directory = request.directory
    store = request.store
    resource_obj = store or directory

    path_stats = get_raw_stats(resource_obj, include_suggestions=True)
    checks_stats = resource_obj.getcompletestats()

    translate_actions = get_translate_actions(resource_obj, path_stats, checks_stats)

    # Build URL for getting more summary information for the current path
    url_args = [language.code, project.code, resource_obj.path]
    url_path_summary_more = reverse('pootle-tp-summary', args=url_args)

    summary_text = ungettext(
        '%(num)d word, %(percentage)d%% translated',
        '%(num)d words, %(percentage)d%% translated',
        path_stats['total']['words'],
        {
            'num': path_stats['total']['words'],
            'percentage': path_stats['translated']['percentage']
        }
    )

    ctx = {
        'translation_project': translation_project,
        'project': project,
        'language': language,
        'resource_obj': resource_obj,
        'resource_path': request.resource_path,
        'translate_actions': translate_actions,
        'stats': path_stats,
        'url_path_summary_more': url_path_summary_more,
        'summary': summary_text,
    }

    if store is None:
        table_fields = ['name', 'progress', 'total', 'need-translation',
                        'suggestions', 'activity']
        ctx.update({
            'table': {
                'id': 'tp',
                'proportional': True,
                'fields': table_fields,
                'headings': get_table_headings(table_fields),
                'items': get_children(translation_project, directory),
            }
        })

    return render_to_response("translation_projects/overview.html", ctx,
                              context_instance=RequestContext(request))


@get_path_obj
@permission_required('view')
@get_resource_context
def translate(request, translation_project, dir_path, filename):
    language = translation_project.language
    project = translation_project.project

    is_terminology = (project.is_terminology or request.store and
                                                request.store.is_terminology)
    context = get_translation_context(request, is_terminology=is_terminology)
    context.update({
        'language': language,
        'project': project,
        'translation_project': translation_project,

        'editor_extends': 'translation_projects/base.html',
        'editor_body_id': 'tptranslate',
    })

    return render_to_response('editor/main.html', context,
                              context_instance=RequestContext(request))


@get_path_obj
@permission_required('view')
@get_resource_context
def export_view(request, translation_project, dir_path, filename=None):
    """Displays a list of units with filters applied."""
    ctx = get_export_view_context(request)
    ctx.update({
        'source_language': translation_project.project.source_language,
        'language': translation_project.language,
        'project': translation_project.project,
    })

    return render_to_response('editor/export_view.html', ctx,
                              context_instance=RequestContext(request))


@ajax_required
@get_path_obj
@get_resource_context
def path_summary_more(request, translation_project, dir_path, filename=None):
    """Returns an HTML snippet with more detailed summary information
       for the current path."""
    path_obj = request.ctx_obj

    path_stats = get_raw_stats(path_obj)
    translation_stats = get_translation_stats(path_obj, path_stats)
    quality_checks = get_quality_check_failures(path_obj, path_stats)

    context = {
        'check_failures': quality_checks,
        'trans_stats': translation_stats,
    }

    return render_to_response('translation_projects/xhr_path_summary.html',
                              context, RequestContext(request))
