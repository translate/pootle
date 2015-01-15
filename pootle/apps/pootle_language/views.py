#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2010,2012 Zuza Software Foundation
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

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader, RequestContext
from django.utils.translation import ugettext as _

from pootle.core.browser import get_table_headings, make_project_item
from pootle.core.decorators import get_path_obj, permission_required
from pootle.core.helpers import (get_export_view_context, get_overview_context,
                                 get_translation_context)
from pootle.i18n.gettext import tr_lang
from pootle_app.models.permissions import check_permission
from pootle_app.views.admin.permissions import admin_permissions
from pootle_misc.util import jsonify, ajax_required


@get_path_obj
@permission_required('view')
def overview(request, language):
    can_edit = check_permission('administrate', request)

    translation_projects = language.get_children() \
                                   .order_by('project__fullname')
    user_tps = filter(lambda x: x.is_accessible_by(request.user),
                      translation_projects)
    items = (make_project_item(tp) for tp in user_tps)

    table_fields = ['name', 'progress', 'total', 'need-translation',
                    'suggestions', 'critical', 'last-updated', 'activity']
    table = {
        'id': 'language',
        'fields': table_fields,
        'headings': get_table_headings(table_fields),
        'items': items,
    }

    ctx = get_overview_context(request)
    ctx.update({
        'language': {
          'code': language.code,
          'name': tr_lang(language.fullname),
        },
        'feed_path': '%s/' % language.code,
        'can_edit': can_edit,
        'table': table,

        'browser_extends': 'languages/base.html',
    })

    if can_edit:
        from pootle_language.forms import DescriptionForm
        ctx.update({
            'form': DescriptionForm(instance=language),
            'form_action': reverse('pootle-language-admin-settings',
                                   args=[language.code]),
        })

    response = render(request, 'browser/overview.html', ctx)
    response.set_cookie('pootle-language', language.code)

    return response


@ajax_required
@get_path_obj
@permission_required('administrate')
def language_settings_edit(request, language):
    from pootle_language.forms import DescriptionForm
    form = DescriptionForm(request.POST, instance=language)

    response = {}
    rcode = 400

    if form.is_valid():
        form.save()
        rcode = 200

        response["description"] = u"".join([
            u'<p class="placeholder muted">',
            _(u"No description yet."),
            u"</p>"
        ])

    context = {
        "form": form,
        "form_action": reverse('pootle-language-admin-settings',
                               args=[language.code]),
    }
    t = loader.get_template('admin/_settings_form.html')
    c = RequestContext(request, context)
    response['form'] = t.render(c)

    return HttpResponse(jsonify(response), status=rcode,
                        content_type="application/json")


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
        'feed_path': '%s/' % language.code,
    }
    return admin_permissions(request, language.directory,
                             'languages/admin/permissions.html', ctx)
