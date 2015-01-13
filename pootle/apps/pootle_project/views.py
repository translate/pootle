#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2013 Zuza Software Foundation
# Copyright 2013-2014 Evernote Corporation
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

import locale

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader, RequestContext
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST

from pootle.core.browser import (get_table_headings, make_language_item,
                                 make_project_list_item, make_xlanguage_item)
from pootle.core.decorators import (get_path_obj, get_resource,
                                    permission_required)
from pootle.core.helpers import (get_export_view_context, get_overview_context,
                                 get_translation_context)
from pootle.core.url_helpers import split_pootle_path
from pootle_app.models.permissions import check_permission
from pootle_app.views.admin import util
from pootle_app.views.admin.permissions import admin_permissions
from pootle_misc.util import ajax_required, jsonify
from pootle_project.forms import (TranslationProjectFormSet,
                                  tp_form_factory)
from pootle_project.models import Project
from pootle_translationproject.models import TranslationProject


@get_path_obj
@permission_required('view')
@get_resource
def overview(request, project, dir_path, filename):
    """Languages overview for a given project."""
    item_func = (make_xlanguage_item if dir_path or filename
                                     else make_language_item)
    items = [item_func(item) for item in request.resource_obj.get_children()]
    items.sort(lambda x, y: locale.strcoll(x['title'], y['title']))

    table_fields = ['name', 'progress', 'total', 'need-translation',
                    'suggestions', 'critical', 'last-updated', 'activity']

    ctx = get_overview_context(request)
    ctx.update({
        'project': project,
        'can_edit': check_permission("administrate", request),
        'table': {
            'id': 'project',
            'fields': table_fields,
            'headings': get_table_headings(table_fields),
            'items': items,
        },

        'browser_extends': 'projects/base.html',
    })

    if ctx['can_edit']:
        from pootle_project.forms import DescriptionForm
        ctx.update({
            'form': DescriptionForm(instance=project),
            'form_action': reverse('pootle-project-admin-settings',
                                   args=[project.code]),
        })

    return render(request, 'browser/overview.html', ctx)


@require_POST
@ajax_required
@get_path_obj
@permission_required('administrate')
def project_settings_edit(request, project):
    from pootle_project.forms import DescriptionForm
    form = DescriptionForm(request.POST, instance=project)

    response = {}
    status = 400

    if form.is_valid():
        form.save()
        status = 200

        response["description"] = u"".join([
            u'<p class="placeholder muted">',
            _(u"No description yet."),
            u"</p>",
        ])

    ctx = {
        "form": form,
        "form_action": reverse('pootle-project-admin-settings',
                               args=[project.code]),
    }

    template = loader.get_template('admin/_settings_form.html')
    response['form'] = template.render(RequestContext(request, ctx))

    return HttpResponse(jsonify(response), status=status,
                        content_type="application/json")


@get_path_obj
@permission_required('view')
@get_resource
def translate(request, project, dir_path, filename):
    ctx = get_translation_context(request)
    ctx.update({
        'language': None,
        'project': project,

        'editor_extends': 'projects/base.html',
    })

    return render(request, 'editor/main.html', ctx)


@get_path_obj
@permission_required('view')
@get_resource
def export_view(request, project, dir_path, filename):
    language = None

    ctx = get_export_view_context(request)
    ctx.update({
        'source_language': 'en',
        'language': language,
        'project': project,
    })

    return render(request, 'editor/export_view.html', ctx)


@get_path_obj
@permission_required('administrate')
def project_admin(request, current_project):
    """Adding and deleting project languages."""
    tp_form_class = tp_form_factory(current_project)

    queryset = TranslationProject.objects.filter(project=current_project)
    queryset = queryset.order_by('pootle_path')

    ctx = {
        'page': 'admin-languages',

        'project': {
            'code': current_project.code,
            'name': current_project.fullname,
        }
    }

    def generate_link(tp):
        path_args = split_pootle_path(tp.pootle_path)[:2]
        perms_url = reverse('pootle-tp-admin-permissions', args=path_args)
        return '<a href="%s">%s</a>' % (perms_url, tp.language)

    return util.edit(request, 'projects/admin/languages.html',
                     TranslationProject, ctx, generate_link,
                     linkfield="language", queryset=queryset,
                     can_delete=True, form=tp_form_class,
                     formset=TranslationProjectFormSet)


@get_path_obj
@permission_required('administrate')
def project_admin_permissions(request, project):
    ctx = {
        'page': 'admin-permissions',

        'project': project,
        'directory': project.directory,
        'feed_path': project.pootle_path[1:],
    }
    return admin_permissions(request, project.directory,
                             'projects/admin/permissions.html', ctx)


@get_path_obj
@permission_required('view')
def projects_overview(request, project_set):
    """Page listing all projects."""
    items = [make_project_list_item(project)
             for project in project_set.get_children()]

    table_fields = ['name', 'progress', 'total', 'need-translation',
                    'suggestions', 'critical', 'last-updated', 'activity']

    ctx = get_overview_context(request)
    ctx.update({
        'table': {
            'id': 'projects',
            'fields': table_fields,
            'headings': get_table_headings(table_fields),
            'items': items,
        },

        'browser_extends': 'projects/all/base.html',
    })

    response = render(request, 'browser/overview.html', ctx)
    response.set_cookie('pootle-language', 'projects')

    return response


@get_path_obj
@permission_required('view')
def projects_translate(request, project_set):
    ctx = get_translation_context(request)
    ctx.update({
        'language': None,
        'project': None,

        'editor_extends': 'projects/all/base.html',
    })

    return render(request, 'editor/main.html', ctx)


@get_path_obj
@permission_required('view')
def projects_export_view(request, project_set):
    ctx = get_export_view_context(request)
    ctx.update({
        'source_language': 'en',
        'language': None,
        'project': None,
    })

    return render(request, 'editor/export_view.html', ctx)
