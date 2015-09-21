#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import locale

from django.core.urlresolvers import reverse
from django.shortcuts import render

from pootle.core.browser import (make_language_item,
                                 make_xlanguage_item,
                                 make_project_list_item,
                                 get_table_headings)
from pootle.core.decorators import (get_path_obj, get_resource,
                                    permission_required)
from pootle.core.helpers import (get_export_view_context,
                                 get_browser_context,
                                 get_translation_context)
from pootle.core.url_helpers import split_pootle_path
from pootle.core.utils.json import jsonify
from pootle_app.views.admin import util
from pootle_app.views.admin.permissions import admin_permissions
from pootle_project.forms import tp_form_factory
from pootle_translationproject.models import TranslationProject


@get_path_obj
@permission_required('view')
@get_resource
def browse(request, project, dir_path, filename):
    """Languages browser for a given project."""
    item_func = (make_xlanguage_item if dir_path or filename
                                     else make_language_item)
    items = [item_func(item) for item in
             request.resource_obj.get_children_for_user(request.profile)]
    items.sort(lambda x, y: locale.strcoll(x['title'], y['title']))

    table_fields = ['name', 'progress', 'total', 'need-translation',
                    'suggestions', 'critical', 'last-updated', 'activity']
    table = {
        'id': 'project',
        'fields': table_fields,
        'headings': get_table_headings(table_fields),
        'items': items,
    }

    ctx = get_browser_context(request)
    ctx.update({
        'project': project,
        'table': table,
        'stats': jsonify(request.resource_obj.get_stats_for_user(request.user)),

        'browser_extends': 'projects/base.html',
    })

    return render(request, 'browser/index.html', ctx)


@get_path_obj
@permission_required('view')
@get_resource
def translate(request, project, dir_path, filename):
    language = None

    ctx = get_translation_context(request)
    ctx.update({
        'language': language,
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
        return u'<a href="%s">%s</a>' % (perms_url, tp.language)

    extra = (1 if current_project.get_template_translationproject() is not None
               else 0)

    return util.edit(request, 'projects/admin/languages.html',
                     TranslationProject, ctx, generate_link,
                     linkfield="language", queryset=queryset,
                     can_delete=True, extra=extra, form=tp_form_class)


@get_path_obj
@permission_required('administrate')
def project_admin_permissions(request, project):
    ctx = {
        'page': 'admin-permissions',

        'project': project,
        'directory': project.directory,
    }

    return admin_permissions(request, project.directory,
                             'projects/admin/permissions.html', ctx)


@get_path_obj
@permission_required('view')
def projects_browse(request, project_set):
    """Page listing all projects"""
    items = [make_project_list_item(project)
             for project in project_set.children]
    items.sort(lambda x, y: locale.strcoll(x['title'], y['title']))

    table_fields = ['name', 'progress', 'total', 'need-translation',
                    'suggestions', 'critical', 'last-updated', 'activity']
    table = {
        'id': 'projects',
        'fields': table_fields,
        'headings': get_table_headings(table_fields),
        'items': items,
    }

    ctx = get_browser_context(request)
    ctx.update({
        'table': table,
        'stats': jsonify(request.resource_obj.get_stats()),

        'browser_extends': 'projects/all/base.html',
    })

    response = render(request, 'browser/index.html', ctx)
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
