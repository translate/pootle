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
                                 get_browser_context,
                                 get_translation_context)
from pootle.core.utils.json import jsonify
from pootle_app.models.permissions import check_permission
from pootle_app.views.admin.permissions import admin_permissions as admin_perms
from staticpages.models import StaticPage


SIDEBAR_COOKIE_NAME = 'pootle-browser-sidebar'


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


def get_sidebar_announcements_context(request, project_code, language_code):
    announcements = []
    new_cookie_data = {}
    cookie_data = {}

    if SIDEBAR_COOKIE_NAME in request.COOKIES:
        json_str = unquote(request.COOKIES[SIDEBAR_COOKIE_NAME])
        cookie_data = json.loads(json_str)

    is_sidebar_open = cookie_data.get('isOpen', True)

    def _get_announcement(language_code=None, project_code=None):
        if language_code is None:
            virtual_path = u'announcements/projects/%s' % project_code
        else:
            path = u'/'.join(filter(None, [language_code, project_code]))
            virtual_path = u'announcements/%s' % path

        try:
            return StaticPage.objects.live(request.user).get(
                virtual_path=virtual_path,
            )
        except StaticPage.DoesNotExist:
            return None

    args_list = [
        (None, project_code),
        (language_code, None),
        (language_code, project_code),
    ]

    for args in args_list:
        announcement = _get_announcement(*args)

        if announcement is None:
            continue

        announcements.append(announcement)
        # The virtual_path cannot be used as is for JSON.
        ann_key = announcement.virtual_path.replace('/', '_')
        ann_mtime = dateformat.format(announcement.modified_on, 'U')
        stored_mtime = cookie_data.get(ann_key, None)

        if ann_mtime != stored_mtime:
            new_cookie_data[ann_key] = ann_mtime

    if new_cookie_data:
        # Some announcement has been changed or was never displayed before, so
        # display sidebar and save the changed mtimes in the cookie to not
        # display it next time unless it is necessary.
        is_sidebar_open = True
        cookie_data.update(new_cookie_data)
        new_cookie_data = quote(json.dumps(cookie_data))

    ctx = {
        'announcements': announcements,
        'is_sidebar_open': is_sidebar_open,
        'has_sidebar': len(announcements) > 0,
    }

    return ctx, new_cookie_data


@get_path_obj
@permission_required('view')
@get_resource
def browse(request, translation_project, dir_path, filename=None):
    project = translation_project.project
    language = translation_project.language

    directory = request.directory
    store = request.store
    is_admin = check_permission('administrate', request)

    ctx, cookie_data = get_sidebar_announcements_context(request, project.code,
                                                         language.code)

    ctx.update(get_browser_context(request))

    # TODO improve plugin logic
    if "import_export" in settings.INSTALLED_APPS and request.user.is_authenticated():
        from import_export.views import handle_upload_form

        ctx.update(handle_upload_form(request))

        has_download = (not translation_project.is_terminology_project and
                        (check_permission('translate', request) or
                         check_permission('suggest', request)))
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

                #FIXME: set vfolders stats in the resource, don't inject them here.
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
