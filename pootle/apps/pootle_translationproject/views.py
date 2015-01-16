#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json
from urllib import quote, unquote

from django.conf import settings
from django.shortcuts import render
from django.utils import dateformat

from pootle.core.browser import (get_children, get_table_headings, get_parent,
                                 get_vfolders)
from pootle.core.decorators import (get_path_obj, get_resource,
                                    permission_required)
from pootle.core.helpers import (get_export_view_context,
                                 get_overview_context,
                                 get_translation_context)
from pootle.core.utils.json import jsonify
from pootle_app.models.permissions import check_permission
from pootle_app.views.admin.permissions import admin_permissions as admin_perms
from staticpages.models import StaticPage
from virtualfolder.models import VirtualFolder


SIDEBAR_COOKIE_NAME = 'pootle-overview-sidebar'


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
def overview(request, translation_project, dir_path, filename=None):
    project = translation_project.project
    language = translation_project.language

    directory = request.directory
    store = request.store
    is_admin = check_permission('administrate', request)
    announcements = []

    # TODO: cleanup and refactor, retrieve from cache
    try:
        ann_virtual_path = 'announcements/projects/' + project.code
        announcement = StaticPage.objects.live(request.user).get(
            virtual_path=ann_virtual_path,
        )
        announcements.append(announcement)
    except StaticPage.DoesNotExist:
        announcement = None

    try:
        ann_virtual_path = 'announcements/' + language.code
        language_announcement = StaticPage.objects.live(request.user).get(
            virtual_path=ann_virtual_path,
        )
        announcements.append(language_announcement)
    except StaticPage.DoesNotExist:
        pass

    try:
        ann_virtual_path = ('announcements/' + language.code + '/' +
                            project.code)
        tp_announcement = StaticPage.objects.live(request.user).get(
            virtual_path=ann_virtual_path,
        )
        announcements.append(tp_announcement)
    except StaticPage.DoesNotExist:
        pass

    is_sidebar_open = True
    stored_mtime = None
    new_mtime = None
    cookie_data = {}

    if SIDEBAR_COOKIE_NAME in request.COOKIES:
        json_str = unquote(request.COOKIES[SIDEBAR_COOKIE_NAME])
        cookie_data = json.loads(json_str)

        if 'isOpen' in cookie_data:
            is_sidebar_open = cookie_data['isOpen']

        if project.code in cookie_data:
            stored_mtime = cookie_data[project.code]

    if announcement is not None:
        ann_mtime = dateformat.format(announcement.modified_on, 'U')
        if ann_mtime != stored_mtime:
            is_sidebar_open = True
            new_mtime = ann_mtime

    ctx = {
        'announcements': announcements,
        'is_sidebar_open': is_sidebar_open,
        'has_sidebar': len(announcements) > 0,
    }

    ctx.update(get_overview_context(request))

    # TODO improve plugin logic
    if "import_export" in settings.INSTALLED_APPS and request.user.is_authenticated():
        from import_export.views import handle_upload_form

        ctx.update(handle_upload_form(request))

        has_download = (check_permission('translate', request) or
                        check_permission('suggest', request))
        ctx.update({
            'display_download': has_download,
            'has_sidebar': True,
        })

    stats = request.resource_obj.get_stats()

    if store is None:
        table_fields = ['name', 'progress', 'total', 'need-translation',
                        'suggestions', 'critical', 'last-updated', 'activity']
        ctx.update({
            'table': {
                'id': 'tp',
                'fields': table_fields,
                'headings': get_table_headings(table_fields),
                'parent': get_parent(directory),
                'items': get_children(directory),
            }
        })

        vfolders = get_vfolders(directory)
        if len(vfolders) > 0:
            table_fields = ['name', 'priority', 'progress', 'total',
                            'need-translation', 'suggestions', 'critical',
                            'activity']
            ctx.update({
                'vfolders': {
                    'id': 'vfolders',
                    'fields': table_fields,
                    'headings': get_table_headings(table_fields),
                    'items': get_vfolders(directory, all_vfolders=is_admin),
                },
            })

            #FIXME: set vfolders stats in the resource, don't inject them here.
            stats['vfolders'] = VirtualFolder.get_stats_for(
                directory.pootle_path,
                all_vfolders=is_admin
            )

    ctx.update({
        'translation_project': translation_project,
        'project': project,
        'language': language,
        'stats': jsonify(stats),
        'is_admin': is_admin,

        'browser_extends': 'translation_projects/base.html',
    })

    response = render(request, 'browser/overview.html', ctx)

    if new_mtime is not None:
        cookie_data[project.code] = new_mtime
        cookie_data = quote(json.dumps(cookie_data))
        response.set_cookie(SIDEBAR_COOKIE_NAME, cookie_data)

    return response


@get_path_obj
@permission_required('view')
@get_resource
def translate(request, translation_project, dir_path, filename):
    project = translation_project.project

    is_terminology = (project.is_terminology or request.store and
                                                request.store.is_terminology)
    ctx = get_translation_context(request, is_terminology=is_terminology)

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
