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

from pootle.core.browser import get_children, get_table_headings, get_parent
from pootle.core.decorators import (get_path_obj, get_resource,
                                    permission_required)
from pootle.core.helpers import (get_export_view_context,
                                 get_overview_context,
                                 get_translation_context)
from pootle_app.views.admin.permissions import admin_permissions as admin_perms
from pootle_misc.util import jsonify
from staticpages.models import StaticPage


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

    # TODO: cleanup and refactor, retrieve from cache
    try:
        ann_virtual_path = 'announcements/projects/' + project.code
        announcement = StaticPage.objects.live(request.user).get(
            virtual_path=ann_virtual_path,
        )
    except StaticPage.DoesNotExist:
        announcement = None

    has_announcement = announcement is not None
    has_sidebar = has_announcement
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

    if has_announcement:
        ann_mtime = dateformat.format(announcement.modified_on, 'U')
        if ann_mtime != stored_mtime:
            is_sidebar_open = True
            new_mtime = ann_mtime

    ctx = get_overview_context(request)

    # TODO improve plugin logic
    if "import_export" in settings.INSTALLED_APPS and request.user.is_authenticated():
        from import_export.views import handle_upload_form
        from pootle_app.models.permissions import check_permission

        ctx.update(handle_upload_form(request))

        has_download = (check_permission('translate', request) or
                        check_permission('suggest', request))
        ctx.update({
            'display_download': has_download,
        })
        has_sidebar = True

    ctx.update({
        'translation_project': translation_project,
        'project': project,
        'language': language,
        'stats': jsonify(request.resource_obj.get_stats()),

        'browser_extends': 'translation_projects/base.html',

        'announcement': announcement,
        'is_sidebar_open': is_sidebar_open,
        'has_sidebar': has_sidebar,
    })

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
