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

from django.utils import translation

_translation_project_cache = {}


def get_live_translation(language_code):
    from django.db import models
    TranslationProject = models.get_model('pootle_app', 'TranslationProject')
    global _translation_project_cache

    if not language_code in _translation_project_cache:
        try:
            _translation_project_cache[language_code] = TranslationProject.objects.get(language__code=language_code, project__code="pootle")
        except TranslationProject.DoesNotExist:
            _translation_project_cache[language_code] = None

    return _translation_project_cache[language_code]

def _dummy_translate(singular, plural, n):
    if plural is not None and n > 1:
        return plural
    else:
        return singular

def _translate_message(singular, plural, n):
    locale = translation.to_locale(translation.get_language())
    if locale in ('en', 'en_US'):
        return _dummy_translate(singular, plural, n)

    live_translation = get_live_translation(locale)

    if live_translation is None:
        from django.conf import settings
        default_locale = translation.to_locale(settings.LANGUAGE_CODE)
            
        if default_locale in ('en', 'en_US'):
            return _dummy_translate(singular, plural, n)

        live_translation = get_live_translation(default_locale)

    if live_translation is None:
        _dummy_translate(singular, plural, n)

    return live_translation.translate_message(singular, plural, n)

def translate_message(singular, plural=None, n=1, vars=None):
    translated = _translate_message(singular, plural, n)
    if vars is not None:
        try:
            return translated % vars
        except:
            pass
    return translated

def ugettext(message, vars=None):
    return unicode(translate_message(message, vars))

def ungettext(singular, plural, n, vars=None):
    return unicode(translate_message(singular, plural, n, vars))

def gettext(message, vars=None):
    return str(translate_message(message, vars))

def ngettext(singular, plural, n, vars=None):
    return str(translate_message(singular, plural, n, vars))
