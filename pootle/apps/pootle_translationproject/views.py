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

from itertools import groupby

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import loader, RequestContext
from django.utils.translation import ugettext as _, ungettext

from pootle.core.decorators import (get_path_obj, get_resource_context,
                                    permission_required)
from pootle.core.helpers import get_filter_name, get_translation_context
from pootle.core.url_helpers import split_pootle_path
from pootle_app.models.permissions import check_permission
from pootle_app.models import Directory
from pootle_app.views.admin.permissions import admin_permissions as admin_perms
from pootle_misc.browser import get_children, get_table_headings
from pootle_misc.checks import get_quality_check_failures
from pootle_misc.stats import (get_raw_stats, get_translation_stats,
                               get_translate_actions)
from pootle_misc.util import jsonify, ajax_required
from pootle_statistics.models import Submission
from pootle_store.models import Store
from pootle_store.views import get_step_query


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
    can_edit = check_permission('administrate', request)

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
        'can_edit': can_edit,
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

    if can_edit:
        from pootle_translationproject.forms import DescriptionForm
        ctx['form'] = DescriptionForm(instance=translation_project)

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
def export_view(request, translation_project, dir_path, filename=None):
    """Displays a list of units with filters applied."""
    current_path = translation_project.directory.pootle_path + dir_path

    if filename:
        current_path = current_path + filename
        store = get_object_or_404(Store, pootle_path=current_path)
        units_qs = store.units
    else:
        store = None
        units_qs = translation_project.units.filter(
            store__pootle_path__startswith=current_path,
        )

    filter_name, filter_extra = get_filter_name(request.GET)

    units = get_step_query(request, units_qs)
    unit_groups = [(path, list(units)) for path, units in
                   groupby(units, lambda x: x.store.path)]

    ctx = {
        'source_language': translation_project.project.source_language,
        'language': translation_project.language,
        'project': translation_project.project,
        'unit_groups': unit_groups,
        'filter_name': filter_name,
        'filter_extra': filter_extra,
    }

    return render_to_response('translation_projects/export_view.html', ctx,
                              context_instance=RequestContext(request))


@ajax_required
@get_path_obj
def path_summary_more(request, translation_project, dir_path, filename=None):
    """Returns an HTML snippet with more detailed summary information
       for the current path."""
    current_path = translation_project.directory.pootle_path + dir_path

    if filename:
        current_path = current_path + filename
        store = get_object_or_404(Store, pootle_path=current_path)
        directory = store.parent
    else:
        directory = get_object_or_404(Directory, pootle_path=current_path)
        store = None

    path_obj = store or directory

    path_stats = get_raw_stats(path_obj)
    translation_stats = get_translation_stats(path_obj, path_stats)
    quality_checks = get_quality_check_failures(path_obj, path_stats)

    context = {
        'check_failures': quality_checks,
        'trans_stats': translation_stats,
    }

    return render_to_response('translation_projects/xhr_path_summary.html',
                              context, RequestContext(request))


@ajax_required
@get_path_obj
@permission_required('administrate')
def edit_settings(request, translation_project):
    from pootle_translationproject.forms import DescriptionForm
    form = DescriptionForm(request.POST, instance=translation_project)

    response = {}
    rcode = 400

    if form.is_valid():
        form.save()
        rcode = 200

        if translation_project.description:
            the_html = translation_project.description
        else:
            the_html = u"".join([
                u'<p class="placeholder muted">',
                _(u"No description yet."),
                u"</p>"
            ])

        response["description"] = the_html

    path_args = split_pootle_path(translation_project.pootle_path)[:2]
    action_url = reverse('pootle-tp-admin-settings', args=path_args)
    context = {
        "form": form,
        "form_action": action_url,
    }
    t = loader.get_template('admin/_settings_form.html')
    c = RequestContext(request, context)
    response['form'] = t.render(c)

    return HttpResponse(jsonify(response), status=rcode,
                        mimetype="application/json")
