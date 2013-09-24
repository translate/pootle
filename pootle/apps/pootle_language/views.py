#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2010,2012 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
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

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _, ungettext

from pootle.core.decorators import get_path_obj, permission_required
from pootle.core.helpers import (get_export_view_context,
                                 get_translation_context)
from pootle.i18n.gettext import tr_lang
from pootle_app.views.admin.permissions import admin_permissions
from pootle_misc.browser import get_table_headings
from pootle_misc.stats import (get_raw_stats, stats_descriptions)
from pootle_misc.util import nice_percentage
from pootle_statistics.models import Submission


def get_last_action(translation_project):
    try:
        return Submission.objects.filter(
            translation_project=translation_project).latest().as_html()
    except Submission.DoesNotExist:
        return ''


def make_project_item(translation_project):
    project = translation_project.project
    href = translation_project.get_absolute_url()
    href_all = translation_project.get_translate_url()
    href_todo = translation_project.get_translate_url(state='incomplete')
    href_sugg = translation_project.get_translate_url(state='suggestions')

    project_stats = get_raw_stats(translation_project,
                                  include_suggestions=True)

    info = {
        'code': project.code,
        'href': href,
        'href_all': href_all,
        'href_todo': href_todo,
        'href_sugg': href_sugg,
        'icon': 'project',
        'title': project.fullname,
        'stats': project_stats,
        'lastactivity': get_last_action(translation_project),
        'tooltip': _('%(percentage)d%% complete',
                     {'percentage': project_stats['translated']['percentage']}),
    }

    errors = project_stats.get('errors', 0)

    if errors:
        info['errortooltip'] = ungettext('Error reading %d file',
                                         'Error reading %d files',
                                         errors, errors)

    info.update(stats_descriptions(project_stats))

    return info


@get_path_obj
@permission_required('view')
def overview(request, language):
    translation_projects = language.translationproject_set \
                                   .order_by('project__fullname')
    user_tps = filter(lambda x: x.is_accessible_by(request.user),
                      translation_projects)
    tp_count = len(user_tps)
    items = (make_project_item(tp) for tp in user_tps)

    totals = language.getquickstats()
    translated = nice_percentage(totals['translatedsourcewords'] * 100.0 / max(totals['totalsourcewords'], 1))
    fuzzy   = nice_percentage(totals['fuzzysourcewords'] * 100.0 / max(totals['totalsourcewords'], 1))

    table_fields = ['name', 'progress', 'total', 'need-translation',
                    'suggestions', 'activity']
    table = {
        'id': 'language',
        'proportional': False,
        'fields': table_fields,
        'headings': get_table_headings(table_fields),
        'items': items,
    }

    templatevars = {
        'language': {
          'code': language.code,
          'name': tr_lang(language.fullname),
          'summary': ungettext('%(projects)d project, %(translated)d%% translated',
                               '%(projects)d projects, %(translated)d%% translated',
                               tp_count, {
                                   "projects": tp_count,
                                   "translated": translated}),
        },
        'stats': {
            'translated': {
                'percentage': translated,
            },
            'fuzzy': {
                'percentage': fuzzy,
            },
            'untranslated': {
                'percentage': 100 - translated - fuzzy,
            },
        },
        'table': table,
    }

    return render_to_response("languages/overview.html", templatevars,
                              context_instance=RequestContext(request))


@get_path_obj
@permission_required('view')
def translate(request, language):
    request.pootle_path = language.pootle_path
    request.ctx_path = language.pootle_path
    request.resource_path = ''

    request.store = None
    request.directory = language.directory

    project = None

    context = get_translation_context(request)
    context.update({
        'language': language,
        'project': project,

        'editor_extends': 'languages/base.html',
        'editor_body_id': 'languagetranslate',
    })

    return render_to_response('editor/main.html', context,
                              context_instance=RequestContext(request))


@get_path_obj
@permission_required('view')
def export_view(request, language):
    """Displays a list of units with filters applied."""
    request.pootle_path = language.pootle_path
    request.ctx_path = language.pootle_path
    request.resource_path = ''

    request.store = None
    request.directory = language.directory

    project = None

    ctx = get_export_view_context(request)
    ctx.update({
        'source_language': 'en',
        'language': language,
        'project': project,
    })

    return render_to_response('editor/export_view.html', ctx,
                              context_instance=RequestContext(request))


@get_path_obj
@permission_required('administrate')
def language_admin(request, language):
    template_vars = {
        "language": language,
        "directory": language.directory,
    }
    return admin_permissions(request, language.directory,
                             'languages/admin/permissions.html', template_vars)
