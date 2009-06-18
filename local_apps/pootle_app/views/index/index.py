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
from django.utils.translation import ungettext
from django.shortcuts import render_to_response
from django.template import RequestContext

from pootle_app.models.profile import get_profile
from pootle_app.models import Project, Directory, Suggestion, Submission, TranslationProject, Language
from pootle_app.models.permissions import get_matching_permissions
from pootle_app.views import indexpage
from pootle_app.views import pagelayout
from pootle_app.views.indexpage import shortdescription, gentopstats
from pootle.i18n.jtoolkit_i18n import tr_lang
from pootle_app.models import metadata



def limit(query):
    return query[:5]

def get_items(request, model, latest_changes, item_index, name_func, permission_set):

    def get_percentages(trans, fuzzy):
        try:
            transper = int((100.0 * trans) / total)
            fuzzyper = int((100.0 * fuzzy) / total)
            untransper = (100 - transper) - fuzzyper
        except ZeroDivisionError:
            transper = 100
            fuzzyper = 0
            untransper = 0
        return (transper, fuzzyper, untransper)

    def get_last_action(item, latest_changes):
        if item.code in latest_changes and latest_changes[item.code]\
               is not None:
            return latest_changes[item.code]
        else:
            return ''

    items = []
    if 'view' not in permission_set:
        return items
    latest_changes = latest_changes()
    for item in [item for item in model.objects.all() if item.code in item_index]:
        trans = 0
        fuzzy = 0
        total = 0
        for translation_project in item_index[item.code]:
            stats = metadata.quick_stats(translation_project.directory, translation_project.checker)
            trans += stats['translatedsourcewords']
            fuzzy += stats['fuzzysourcewords']
            total += stats['totalsourcewords']
        untrans = (total - trans) - fuzzy
        (transper, fuzzyper, untransper) = get_percentages(trans, fuzzy)
        lastact = get_last_action(item, latest_changes)
        items.append({
            'code': item.code,
            'name': name_func(item.fullname),
            'lastactivity': lastact,
            'trans': trans,
            'fuzzy': fuzzy,
            'untrans': untrans,
            'total': total,
            'transper': transper,
            'fuzzyper': fuzzyper,
            'untransper': untransper,
            })
    items.sort(lambda x, y: locale.strcoll(x['name'], y['name']))
    return items

def getlanguages(request, language_index, permission_set):
    return get_items(request, Language, Submission.objects.get_latest_language_changes,
                          language_index, tr_lang, permission_set)

def getprojects(request, project_index, permission_set):
    return get_items(request, Project, Submission.objects.get_latest_project_changes,
                          project_index, lambda x: x, permission_set)

def getprojectnames():
    return [proj.fullname for proj in Project.objects.all()]


def view(request):
    permission_set = get_matching_permissions(get_profile(request.user), Directory.objects.root)
    (language_index, project_index) =  TranslationProject.get_language_and_project_indices()
    topsugg = limit(Suggestion.objects.get_top_suggesters())
    topreview = limit(Suggestion.objects.get_top_reviewers())
    topsub = limit(Submission.objects.get_top_submitters())
    topstats = gentopstats(topsugg, topreview, topsub)

    templatevars = {
        'pagetitle': pagelayout.get_title(),
        'description': pagelayout.get_description(),
        'meta_description': shortdescription(pagelayout.get_description()),
        'keywords': [
            'Pootle',
            'translate',
            'translation',
            'localisation',
            'localization',
            'l10n',
            'traduction',
            'traduire',
            ] + getprojectnames(),
        'languagelink': _('Languages'),
        'languages': getlanguages(request, language_index,
                                       permission_set),
        'projectlink': _('Projects'),
        'projects': getprojects(request, project_index,
                                     permission_set),
        'topstats': topstats,
        'topstatsheading': _('Top Contributors'),
        'instancetitle': pagelayout.get_title(),
        'translationlegend': {'translated': _('Translations are complete'),
                    'fuzzy': _('Translations need to be checked (they are marked fuzzy)'
                    ), 'untranslated': _('Untranslated')},
        }

    return render_to_response('index/index.html', templatevars, RequestContext(request))


