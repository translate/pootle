#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2012 Zuza Software Foundation
# Copyright 2013 Zuza Software Foundation
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

import locale

from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _

from pootle.core.decorators import get_path_obj
from pootle.i18n.gettext import tr_lang
from pootle_app.models import Directory
from pootle_app.models.permissions import (get_matching_permissions,
                                           check_permission)
from pootle_app.views.top_stats import gentopstats_root
from pootle_language.models import Language
from pootle_misc.browser import get_table_headings
from pootle_misc.stats import get_raw_stats
from pootle_profile.models import get_profile
from pootle_project.models import Project
from pootle_statistics.models import Submission


def get_items(request, model, get_last_action, name_func):
    items = []
    if not check_permission('view', request):
        return items

    for item in model.objects.iterator():
        stats = get_raw_stats(item)

        translated_percentage = stats['translated']['percentage']
        items.append({
            'code': item.code,
            'name': name_func(item.fullname),
            'lastactivity': get_last_action(item),
            'stats': stats,
            'completed_title': _("%(percentage)d%% complete",
                                 {'percentage': translated_percentage}),
        })

    items.sort(lambda x, y: locale.strcoll(x['name'], y['name']))

    return items


def getlanguages(request):
    def get_last_action(item):
        try:
            return Submission.objects.filter(
                translation_project__language=item).latest().as_html()
        except Submission.DoesNotExist:
            return ''

    return get_items(request, Language, get_last_action, tr_lang)


def getprojects(request):
    def get_last_action(item):
        try:
            return Submission.objects.filter(
                translation_project__project=item).latest().as_html()
        except Submission.DoesNotExist:
            return ''

    return get_items(request, Project, get_last_action, lambda name: name)


@get_path_obj
def view(request, root_dir):
    request.permissions = get_matching_permissions(get_profile(request.user),
                                                   root_dir)
    can_edit = request.user.is_superuser

    languages = getlanguages(request)
    languages_table_fields = ['language', 'progress', 'activity']
    languages_table = {
        'id': 'index-languages',
        'proportional': False,
        'fields': languages_table_fields,
        'headings': get_table_headings(languages_table_fields),
        'items': filter(lambda x: x['stats']['total']['words'] != 0, languages),
    }

    projects = getprojects(request)
    projects_table_fields = ['project', 'progress', 'activity']
    projects_table = {
        'id': 'index-projects',
        'proportional': False,
        'fields': projects_table_fields,
        'headings': get_table_headings(projects_table_fields),
        'items': projects,
    }

    templatevars = {
        'description': _(settings.DESCRIPTION),
        'keywords': [
            'Pootle',
            'translate',
            'translation',
            'localisation',
            'localization',
            'l10n',
            'traduction',
            'traduire',
        ],
        'topstats': gentopstats_root(),
        'permissions': request.permissions,
        'can_edit': can_edit,
        'languages_table': languages_table,
        'projects_table': projects_table,
    }
    visible_langs = [l for l in languages if l['stats']['total']['words'] != 0]
    templatevars['moreprojects'] = (len(projects) > len(visible_langs))

    if can_edit:
        from pootle_misc.siteconfig import load_site_config
        from pootle_app.forms import GeneralSettingsForm
        siteconfig = load_site_config()
        setting_form = GeneralSettingsForm(siteconfig)
        templatevars['form'] = setting_form

    return render_to_response('index/index.html', templatevars,
                              RequestContext(request))
