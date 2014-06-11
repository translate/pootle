#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Zuza Software Foundation
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

from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import render

from pootle.i18n.gettext import tr_lang
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_statistics.models import Submission
from pootle_store.models import Suggestion
from pootle_translationproject.models import TranslationProject


User = get_user_model()


def view(request):
    """Render a nested list like this::

        contributors = [
          ('french', [
            ('Hackaraus', ['Auser Name', 'username2', ...]),
            ('Project 2', ['username1', 'usernameX', ...]),
            ...
            ]),
          ('spanish', [
            ('Project 1', ['User 1', 'User2', ...]),
            ('Project 2', ['User 1', 'UserX', ...]),
            ...
            ]),
        ]
    """

    exclude_project_names = getattr(
        settings,
        'CONTRIBUTORS_EXCLUDED_PROJECT_NAMES',
        []
    )
    excluded_names = set(getattr(
        settings,
        'CONTRIBUTORS_EXCLUDED_NAMES',
        []
    ))

    user_names = {}  # user id -> name
    _skip_users = set()
    for user in (User.objects.all()
                 .values("id", "full_name", "username")):
        if excluded_names:
            names = [user[e] for e in ["username", "full_name"]]
            if set(names) & excluded_names:
                _skip_users.add(user['id'])
                continue
        name = user["full_name"].strip()
        if not name:
            name = user['username']
        user_names[user['id']] = name

    language_names = {}  # language id -> name
    for language in Language.objects.all().values('id', 'fullname'):
        language_names[language['id']] = tr_lang(language['fullname'])

    project_names = {}  # project id -> name
    for project in (Project.objects
                    .exclude(fullname__in=exclude_project_names)
                    .values('id', 'fullname')):
        project_names[project['id']] = project['fullname']

    # map users to projects per language across:
    # submitters, suggesters and reviewers
    languages = {}
    tp_to_lang_id = {}
    tp_to_proj_id = {}

    # prepare a map of TranslationProject IDs to
    # language and project to save queries for later
    for tp in (TranslationProject.objects.all()
               .values('id', 'language_id', 'project_id')):
        tp_to_lang_id[tp['id']] = tp['language_id']
        tp_to_proj_id[tp['id']] = tp['project_id']

    for model, user_key in ((Submission, 'submitter_id'),
                            (Suggestion, 'user_id'),
                            (Suggestion, 'reviewer_id')):
        for item in (model.objects.all()
                     .values('translation_project_id', user_key)
                     .distinct()):
            lang_id = tp_to_lang_id[item['translation_project_id']]
            proj_id = tp_to_proj_id[item['translation_project_id']]
            user_id = item[user_key]
            if not user_id:  # bad paste on_delete cascades
                continue
            if lang_id not in languages:
                languages[lang_id] = {}
            if proj_id not in languages[lang_id]:
                languages[lang_id][proj_id] = set()
            languages[lang_id][proj_id].add(user_id)

    # finally, turn this massive dict into a list of lists of lists
    # to be used in the template to loop over.
    # also change from IDs to real names
    contributors = []
    for lang_id, projectsmap in languages.items():
        language = language_names[lang_id]
        projects = []
        users = None
        for proj_id, user_ids in projectsmap.items():
            usersset = [user_names[x] for x in user_ids
                                      if x not in _skip_users]
            users = sorted(usersset, lambda x, y: cmp(x.lower(), y.lower()))
            try:
                projectname = project_names[proj_id]
            except KeyError:
                # some legacy broken project or excluded
                continue
            if users:
                projects.append((projectname, users))
        if projects:
            contributors.append((language, projects))
    contributors.sort()

    ctx = {
        'contributors': contributors,
    }

    return render(request, 'about/contributors.html', ctx)
