#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
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

from functools import wraps

from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect

from pootle_app.models.permissions import get_matching_permissions
from pootle_profile.models import get_profile
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_translationproject.models import TranslationProject


def get_path_obj(func):
    @wraps(func)
    def wrapped(request, *args, **kwargs):
        language_code = kwargs.pop('language_code', None)
        project_code = kwargs.pop('project_code', None)

        if language_code and project_code:
            try:
                translation_project = TranslationProject.objects.get(
                    language__code=language_code,
                    project__code=project_code
                )
            except TranslationProject.DoesNotExist:
                translation_project = None

            if translation_project is None:
                # Explicit selection via the UI: redirect either to
                # ``/language_code/`` or ``/projects/project_code/``
                user_choice = request.COOKIES.get('user-choice', None)
                if user_choice and user_choice in ('language', 'project',):
                    url = {
                        'language': reverse('pootle-language-overview',
                                            args=[language_code]),
                        'project': reverse('pootle-project-overview',
                                           args=[project_code]),
                    }
                    response = redirect(url[user_choice])
                    response.delete_cookie('user-choice')

                    return response

                raise Http404

            return func(request, translation_project, *args, **kwargs)

        if language_code:
            language = get_object_or_404(Language, code=language_code)
            return func(request, language, *args, **kwargs)

        if project_code:
            project = get_object_or_404(Project, code=project_code)
            return func(request, project, *args, **kwargs)

    return wrapped


def set_tp_request_context(f):
    """Sets up the request object with a common context for translation
    projects.
    """
    @wraps(f)
    def decorated_f(request, translation_project, *args, **kwargs):
        # For now, all permissions in a translation project are
        # relative to the root of that translation project.
        request.profile = get_profile(request.user)
        request.permissions = get_matching_permissions(
            request.profile, translation_project.directory
        )
        request.translation_project = translation_project

        return f(request, translation_project, *args, **kwargs)

    return decorated_f
