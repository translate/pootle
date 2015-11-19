#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf import settings
from django.shortcuts import render

from import_export.views import handle_upload_form
from pootle.core.browser import (get_children, get_table_headings, get_parent,
                                 get_vfolders)
from pootle.core.decorators import (get_path_obj, get_resource,
                                    permission_required)
from pootle.core.helpers import (get_export_view_context, get_browser_context,
                                 get_sidebar_announcements_context,
                                 get_translation_context, SIDEBAR_COOKIE_NAME)
from pootle.core.utils.json import jsonify
from pootle_app.models.permissions import check_permission
from pootle_app.views.admin.permissions import admin_permissions as admin_perms


@get_path_obj
@permission_required('administrate')
def admin_permissions(request, translation_project):
    language = translation_project.language
    project = translation_project.project

    ctx = {
        'page': 'admin-permissions',

        'translation_project': translation_project,
        'project': project,
        'language': language,
        'directory': translation_project.directory,
    }

    return admin_perms(request, translation_project.directory,
                       'translation_projects/admin/permissions.html', ctx)


@get_path_obj
@permission_required('view')
@get_resource
def browse(request, translation_project, dir_path, filename=None):
    project = translation_project.project
    language = translation_project.language

    directory = request.directory
    store = request.store
    is_admin = check_permission('administrate', request)

    ctx, cookie_data = get_sidebar_announcements_context(
        request,
        (project, language, translation_project, ),
    )

    ctx.update(get_browser_context(request))

    # TODO improve plugin logic
    if "import_export" in settings.INSTALLED_APPS:
        if request.user.is_authenticated():
            if check_permission('translate', request):
                ctx.update(handle_upload_form(request, project))
            ctx.update({'display_download': True,
                        'has_sidebar': True})

    stats = request.resource_obj.get_stats()

    if store is None:
        table_fields = ['name', 'progress', 'total', 'need-translation',
                        'suggestions', 'critical', 'last-updated', 'activity']
        ctx.update({
            'table': {
                'id': 'tp',
                'fields': table_fields,
                'headings': get_table_headings(table_fields),
                'items': get_children(directory),
            }
        })

        if 'virtualfolder' in settings.INSTALLED_APPS:
            vfolders = get_vfolders(directory, all_vfolders=is_admin)
            if len(vfolders) > 0:
                table_fields = ['name', 'priority', 'progress', 'total',
                                'need-translation', 'suggestions', 'critical',
                                'last-updated', 'activity']
                ctx.update({
                    'vfolders': {
                        'id': 'vfolders',
                        'fields': table_fields,
                        'headings': get_table_headings(table_fields),
                        'items': vfolders,
                    },
                })

                # FIXME: set vfolders stats in the resource, don't inject them
                # here.
                stats['vfolders'] = {}

                for vfolder_treeitem in directory.vf_treeitems.iterator():
                    if request.user.is_superuser or vfolder_treeitem.is_visible:
                        stats['vfolders'][vfolder_treeitem.code] = \
                            vfolder_treeitem.get_stats(include_children=False)

    ctx.update({
        'parent': get_parent(directory if store is None else store),
        'translation_project': translation_project,
        'project': project,
        'language': language,
        'stats': jsonify(stats),
        'is_admin': is_admin,
        'is_store': store is not None,

        'browser_extends': 'translation_projects/base.html',
    })

    response = render(request, 'browser/index.html', ctx)

    if cookie_data:
        response.set_cookie(SIDEBAR_COOKIE_NAME, cookie_data)

    return response


@get_path_obj
@permission_required('view')
@get_resource
def translate(request, translation_project, dir_path, filename):
    project = translation_project.project

    ctx = get_translation_context(request)

    ctx.update({
        'language': translation_project.language,
        'project': project,
        'translation_project': translation_project,

        'editor_extends': 'translation_projects/base.html',
    })

    return render(request, "editor/main.html", ctx)


@get_path_obj
@permission_required('view')
@get_resource
def export_view(request, translation_project, dir_path, filename=None):
    """Displays a list of units with filters applied."""
    ctx = get_export_view_context(request)
    ctx.update({
        'source_language': translation_project.project.source_language,
        'language': translation_project.language,
        'project': translation_project.project,
    })

    return render(request, 'editor/export_view.html', ctx)
