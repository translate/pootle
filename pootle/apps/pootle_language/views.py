#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2010, 2012-2013 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import loader, RequestContext
from django.utils.translation import ugettext as _, ungettext

from pootle.core.decorators import get_path_obj, permission_required
from pootle.core.helpers import get_translation_context
from pootle.i18n.gettext import tr_lang
from pootle_app.models.permissions import check_permission
from pootle_app.views.admin.permissions import admin_permissions
from pootle_app.views.top_stats import gentopstats_language
from pootle_language.models import Language
from pootle_misc.browser import get_table_headings
from pootle_misc.stats import (get_raw_stats, nice_percentage,
                               stats_descriptions)
from pootle_misc.util import jsonify, ajax_required
from pootle_profile.models import get_profile
from pootle_statistics.models import Submission


def get_last_action(translation_project):
    try:
        return Submission.objects.filter(
            translation_project=translation_project).latest().as_html()
    except Submission.DoesNotExist:
        return ''


def make_project_item(translation_project):
    project = translation_project.project
    href = translation_project.get_absolute_url()
    href_all = translation_project.get_translate_url()
    href_todo = translation_project.get_translate_url(state='incomplete')

    project_stats = get_raw_stats(translation_project)

    info = {
        'code': project.code,
        'href': href,
        'href_all': href_all,
        'href_todo': href_todo,
        'title': project.fullname,
        'description': project.description,
        'stats': project_stats,
        'lastactivity': get_last_action(translation_project),
        'isproject': True,
        'tooltip': _('%(percentage)d%% complete',
                     {'percentage': project_stats['translated']['percentage']}),
    }

    errors = project_stats.get('errors', 0)

    if errors:
        info['errortooltip'] = ungettext('Error reading %d file',
                                         'Error reading %d files',
                                         errors, errors)

    info.update(stats_descriptions(project_stats))

    return info


@get_path_obj
@permission_required('view')
def overview(request, language):
    can_edit = check_permission('administrate', request)

    projects = language.translationproject_set.order_by('project__fullname')
    projectcount = len(projects)
    items = (make_project_item(translate_project) for translate_project in projects.iterator())

    totals = language.getquickstats()
    average = nice_percentage(totals['translatedsourcewords'],
                              totals['totalsourcewords'])
    topstats = gentopstats_language(language)

    table_fields = ['name', 'progress', 'total', 'need-translation', 'activity']
    table = {
        'id': 'language',
        'proportional': False,
        'fields': table_fields,
        'headings': get_table_headings(table_fields),
        'items': items,
    }

    templatevars = {
        'language': {
          'code': language.code,
          'name': tr_lang(language.fullname),
          'description': language.description,
          'summary': ungettext('%(projects)d project, %(average)d%% translated',
                               '%(projects)d projects, %(average)d%% translated',
                               projectcount, {
                                   "projects": projectcount,
                                   "average": average}),
        },
        'feed_path': '%s/' % language.code,
        'topstats': topstats,
        'can_edit': can_edit,
        'table': table,
    }

    if can_edit:
        from pootle_language.forms import DescriptionForm
        templatevars['form'] = DescriptionForm(instance=language)

    return render_to_response("language/overview.html", templatevars,
                              context_instance=RequestContext(request))


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

        if language.description:
            the_html = language.description
        else:
            the_html = u"".join([
                u'<p class="placeholder muted">',
                _(u"No description yet."), u"</p>"
            ])

        response["description"] = the_html

    context = {
        "form": form,
        "form_action": language.pootle_path + "edit_settings.html",
    }
    t = loader.get_template('admin/general_settings_form.html')
    c = RequestContext(request, context)
    response['form'] = t.render(c)

    return HttpResponse(jsonify(response), status=rcode,
                        mimetype="application/json")


@get_path_obj
@permission_required('view')
def translate(request, language):
    request.pootle_path = language.pootle_path
    request.ctx_path = language.pootle_path
    request.resource_path = ''

    request.store = None
    request.directory = language.directory

    project = None

    context = get_translation_context(request)
    context.update({
        'language': language,
        'project': project,

        'editor_extends': 'language_base.html',
        'editor_body_id': 'languagetranslate',
    })

    return render_to_response('editor/main.html', context,
                              context_instance=RequestContext(request))


@get_path_obj
@permission_required('administrate')
def language_admin(request, language):
    template_vars = {
        "language": language,
        "directory": language.directory,
        "feed_path": '%s/' % language.code,
    }
    return admin_permissions(request, language.directory,
                             "language/language_admin.html", template_vars)
