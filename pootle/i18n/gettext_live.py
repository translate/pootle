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

from django.conf import settings
from django.utils import translation

from pootle.i18n.gettext import override_gettext
from pootle_app.models.translation_project import TranslationProject


_translation_project_cache = {}

def hijack_translation():
    """Replace django's gettext functions with functions from the
    appropriate TranslationProject, allowing live translation of
    Pootle's UI from in memory stores"""

    language = translation.get_language()

    if language in ('en', 'en-us'):
        return None
    
    global _translation_project_cache
    if not language in _translation_project_cache:
        try:
            _translation_project_cache[language] = TranslationProject.objects.get(language__code=language, project__code="pootle")
        except:
            try:
                _translation_project_cache[language] = TranslationProject.objects.get(language_code=settings.LANGUAGE_CODE, project__code="pootle")
            except:
                _translation_project_cache[language] = None
                
    if _translation_project_cache[language] is not None:
        override_gettext(_translation_project_cache[language])
            
