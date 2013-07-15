#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
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
from django.shortcuts import redirect

from pootle_app.models.permissions import get_matching_permissions
from pootle_profile.models import get_profile
from pootle_translationproject.models import TranslationProject


def get_translation_project(f):
    """Retrieves a :cls:`TranslationProject` matching `language_code` and
    `project_code`.

    If there's no match for a translation project, a 404 response is
    returned.
    Alternatively, if a user made a explicit selection via the UI and
    there's no match for a translation project, a redirect to
    ``/language_code/`` or ``/projects/project_code/`` will be performed.
    """
    @wraps(f)
    def decorated_f(request, language_code, project_code, *args, **kwargs):
        try:
            translation_project = TranslationProject.objects.get(
                language__code=language_code,
                project__code=project_code
            )
        except TranslationProject.DoesNotExist:
            translation_project = None

        if not translation_project:
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

        return f(request, translation_project, *args, **kwargs)

    return decorated_f


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
