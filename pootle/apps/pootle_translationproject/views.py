#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2014 Zuza Software Foundation
# Copyright 2013-2014 Evernote Corporation
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


ANN_COOKIE_NAME = 'project-announcements'


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

    display_announcement = True
    stored_mtime = None
    new_mtime = None
    cookie_data = {}

    if ANN_COOKIE_NAME in request.COOKIES:
        json_str = unquote(request.COOKIES[ANN_COOKIE_NAME])
        cookie_data = json.loads(json_str)

        if 'isOpen' in cookie_data:
            display_announcement = cookie_data['isOpen']

        if project.code in cookie_data:
            stored_mtime = cookie_data[project.code]

    if announcement is not None:
        ann_mtime = dateformat.format(announcement.modified_on, 'U')
        if ann_mtime != stored_mtime:
            display_announcement = True
            new_mtime = ann_mtime

    ctx = get_overview_context(request)

    if settings.POOTLE_ENABLE_OFFLINE and request.user.is_authenticated():
        from pootle_app.models.permissions import check_permission

        if (check_permission("translate", request) or
            check_permission("suggest", request)):

            ctx.update({
                'display_download': True,
            })

    ctx.update({
        'translation_project': translation_project,
        'project': project,
        'language': language,
        'stats': jsonify(request.resource_obj.get_stats()),

        'browser_extends': 'translation_projects/base.html',

        'announcement': announcement,
        'announcement_displayed': display_announcement,
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
        response.set_cookie(ANN_COOKIE_NAME, cookie_data)

    return response


@get_path_obj
@permission_required('view')
@get_resource
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
    })

    return render(request, "editor/main.html", context)


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
