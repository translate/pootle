#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2010,2012 Zuza Software Foundation
#
# This file is part of translate.
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

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import loader, RequestContext
from django.utils.translation import ugettext as _, ungettext

from pootle.i18n.gettext import tr_lang
from pootle_app.models.permissions import (get_matching_permissions,
                                           check_permission)
from pootle_app.views.admin.permissions import admin_permissions
from pootle_app.views.language import dispatch
from pootle_app.views.language.item_dict import stats_descriptions
from pootle_app.views.language.view import get_stats_headings
from pootle_app.views.top_stats import gentopstats_language
from pootle_language.models import Language
from pootle_misc.stats import get_raw_stats
from pootle_misc.util import nice_percentage, jsonify, ajax_required
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
    href = translation_project.pootle_path
    href_todo = dispatch.translate(translation_project, state='incomplete')

    project_stats = get_raw_stats(translation_project)

    info = {
        'code': project.code,
        'href': href,
        'href_todo': href_todo,
        'title': project.fullname,
        'description_html': project.description_html,
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

def language_index(request, language_code):
    language = get_object_or_404(Language, code=language_code)
    request.permissions = get_matching_permissions(get_profile(request.user),
                                                   language.directory)

    if not check_permission("view", request):
        raise PermissionDenied

    can_edit = check_permission('administrate', request)

    projects = language.translationproject_set.order_by('project__fullname')
    projectcount = len(projects)
    items = (make_project_item(translate_project) for translate_project in projects.iterator())

    totals = language.getquickstats()
    average = nice_percentage(totals['translatedsourcewords'] * 100.0 / max(totals['totalsourcewords'], 1))
    topstats = gentopstats_language(language)

    templatevars = {
        'language': {
          'code': language.code,
          'name': tr_lang(language.fullname),
          'description_html': language.description_html,
          'summary': ungettext('%(projects)d project, %(average)d%% translated',
                               '%(projects)d projects, %(average)d%% translated',
                               projectcount, {
                                   "projects": projectcount,
                                   "average": average}),
        },
        'feed_path': '%s/' % language.code,
        'projects': items,
        'statsheadings': get_stats_headings(),
        'topstats': topstats,
        'can_edit': can_edit,
        }

    if can_edit:
        from pootle_language.forms import DescriptionForm
        templatevars['form'] = DescriptionForm(instance=language)

    return render_to_response("language/language_index.html", templatevars,
                              context_instance=RequestContext(request))

@ajax_required
def language_settings_edit(request, language_code):
    language = get_object_or_404(Language, code=language_code)
    request.permissions = get_matching_permissions(
            get_profile(request.user), language.directory
    )
    if not check_permission('administrate', request):
        raise PermissionDenied

    from pootle_language.forms import DescriptionForm
    form = DescriptionForm(request.POST, instance=language)

    response = {}
    rcode = 400

    if form.is_valid():
        form.save()
        rcode = 200

        if language.description_html:
            the_html = language.description_html
        else:
            the_html = u"".join([
                u'<p class="placeholder muted">',
                _(u"No description yet."), u"</p>"
            ])

        response["description_html"] = the_html

    context = {
        "form": form,
        "form_action": language.pootle_path + "edit_settings.html",
    }
    t = loader.get_template('admin/general_settings_form.html')
    c = RequestContext(request, context)
    response['form'] = t.render(c)

    return HttpResponse(jsonify(response), status=rcode,
                        mimetype="application/json")


def language_admin(request, language_code):
    # Check if the user can access this view
    language = get_object_or_404(Language, code=language_code)
    request.permissions = get_matching_permissions(get_profile(request.user),
                                                   language.directory)
    if not check_permission('administrate', request):
        raise PermissionDenied(_("You do not have rights to administer this language."))

    template_vars = {
        "language": language,
        "directory": language.directory,
        "feed_path": '%s/' % language.code,
    }
    return admin_permissions(request, language.directory, "language/language_admin.html", template_vars)
