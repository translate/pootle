#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
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

from pootle_app.models import Project, Language, TranslationProject
from pootle_app.models.profile import get_profile

class PootlePathMiddleware(object):
    """populates request with objects relevant to current pootle_path"""
    def process_request(self, request):
        path_fragments = filter(None, request.path.split('/'))
        path_length = len(path_fragments)
        context = {}
        # Language
        if path_length > 0 and path_fragments[0] not in ['admin', 'accounts', 'projects'] and not path_fragments[0].endswith('.html'):
            try:
                context['language'] = Language.objects.get(code=path_fragments[0])
            except Language.DoesNotExist:
                pass
        # Project
        if path_length > 1 and ('language' in context or path_fragments[0] == 'projects'):
            try:
                context['project'] = Project.objects.get(code=path_fragments[1])
            except Project.DoesNotExist:
                pass
        # TranslationProject
        if 'language' in context and 'project' in context:
            try:
                context['translation_project'] = TranslationProject.objects.get(
                    language=context['language'], project=context['project'])
            except TranslationProject.DoesNotExist:
                pass

        request.pootle_context = context
        request.profile = get_profile(request.user)
