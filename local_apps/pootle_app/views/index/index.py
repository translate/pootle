#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

from django.utils.translation import ugettext as _
from django.shortcuts import render_to_response
from django.template import RequestContext

from pootle_app.models.profile import get_profile
from pootle_app.models import Project, Directory, Submission, Language
from pootle_app.models.permissions import get_matching_permissions, check_permission
from pootle_app.views import pagelayout
from pootle_app.views.top_stats import gentopstats
from pootle.i18n.gettext import tr_lang
from pootle_app.views.language.item_dict import add_percentages

def limit(query):
    return query[:5]

def get_items(request, model, get_last_action, name_func):

    items = []
    if not check_permission('view', request):
        return items

    for item in model.objects.all():
        stats = item.getquickstats()
        stats = add_percentages(stats)

        lastact = get_last_action(item)
        items.append({
            'code': item.code,
            'name': name_func(item.fullname),
            'lastactivity': lastact,
            'trans': stats["translatedsourcewords"],
            'fuzzy': stats["fuzzysourcewords"],
            'untrans': stats["untranslatedsourcewords"],
            'total': stats["totalsourcewords"],
            'transper': stats["translatedpercentage"],
            'fuzzyper': stats["fuzzypercentage"],
            'untransper': stats["untranslatedpercentage"],
            'completed_title': _("%(percentage)d%% complete" %
                                 {'percentage': stats['translatedpercentage']}),
            })
    items.sort(lambda x, y: locale.strcoll(x['name'], y['name']))
    return items

def getlanguages(request):
    def get_last_action(item):
        try:
            return Submission.objects.filter(translation_project__language=item).latest()
        except:
            return ''

    return get_items(request, Language, get_last_action, tr_lang)

def getprojects(request):
    def get_last_action(item):
        try:
            return Submission.objects.filter(translation_project__project=item).latest()
        except:
            return ''

    return get_items(request, Project, get_last_action, lambda name: name)


def view(request):
    request.permissions = get_matching_permissions(get_profile(request.user), Directory.objects.root)
    topstats = gentopstats(lambda query: query)

    templatevars = {
        'description': pagelayout.get_description(),
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
        'languagelink': _('Languages'),
        'languages': getlanguages(request),
        'projectlink': _('Projects'),
        'projects': getprojects(request),
        'topstats': topstats,
        'instancetitle': pagelayout.get_title(),
        'translationlegend': {'translated': _('Translations are complete'),
                    'fuzzy': _('Translations need to be checked (they are marked fuzzy)'
                    ), 'untranslated': _('Untranslated')},
        }

    return render_to_response('index/index.html', templatevars, RequestContext(request))
