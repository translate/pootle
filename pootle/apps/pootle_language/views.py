#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.shortcuts import render

from pootle.core.browser import (make_project_item,
                                 get_table_headings)
from pootle.core.decorators import get_path_obj, permission_required
from pootle.core.helpers import (get_export_view_context,
                                 get_browser_context,
                                 get_translation_context)
from pootle.core.utils.json import jsonify
from pootle.i18n.gettext import tr_lang
from pootle_app.views.admin.permissions import admin_permissions


@get_path_obj
@permission_required('view')
def browse(request, language):
    user_tps = language.get_children_for_user(request.user)
    items = (make_project_item(tp) for tp in user_tps)

    table_fields = ['name', 'progress', 'total', 'need-translation',
                    'suggestions', 'critical', 'last-updated', 'activity']

    ctx = get_browser_context(request)
    ctx.update({
        'language': {
          'code': language.code,
          'name': tr_lang(language.fullname),
        },
        'table': {
            'id': 'language',
            'fields': table_fields,
            'headings': get_table_headings(table_fields),
            'items': items,
        },
        'stats': jsonify(request.resource_obj.get_stats_for_user(request.user)),

        'browser_extends': 'languages/base.html',
    })

    response = render(request, 'browser/index.html', ctx)
    response.set_cookie('pootle-language', language.code)

    return response


@get_path_obj
@permission_required('view')
def translate(request, language):
    request.pootle_path = language.pootle_path
    request.ctx_path = language.pootle_path

    request.store = None
    request.directory = language.directory

    project = None

    context = get_translation_context(request)
    context.update({
        'language': language,
        'project': project,

        'editor_extends': 'languages/base.html',
    })

    return render(request, "editor/main.html", context)


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

    return render(request, "editor/export_view.html", ctx)


@get_path_obj
@permission_required('administrate')
def language_admin(request, language):
    ctx = {
        'page': 'admin-permissions',

        'language': language,
        'directory': language.directory,
    }
    return admin_permissions(request, language.directory,
                             'languages/admin/permissions.html', ctx)
