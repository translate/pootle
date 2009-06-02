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
from django.utils.thread_support import currentThread
from django.utils.functional import lazy

from pootle_app.models.translation_project import TranslationProject
from pootle_app.models.language import Language
from pootle.i18n.util import language_dir

# START BOOTSTRAPPING TRANSLATION CODE

# We need to hijack Django's translation machinery very early in
# Pootle's initialization process. If we don't then some Django
# modules will be initialized before we hijack then and they'll hold
# references to the original Django translation functions.
#
# In Pootle, translations are done using Project instances. We
# get these instances from the global POTree instance. 
#
# During Pootle's initialization we first hijack Django's translation
# functions. But some modules will attempt to call our translation functions 
# before the potree module is initialized (and this must happen for us to
# get hold of the POTree class).
#
# Thus, we have to bootstrap the localization system and provide dummy
# a dummy translation object which implements the Project interface that
# our localization system relies on.
#
# It's the responsibility of Pootle's initialization code to initialize the
# global POTree object and then to replace get_lang and check_for_language
# with their real implementations.

class DummyLanguage(object):
    code = 'en'

class DummyTranslation(object):
    language = DummyLanguage()

    def gettext(self, message):
        return message

    def ugettext(self, message):
        return message

    def ngettext(self, singular, plural, number):
        if number == 1:
            return singular
        else:
            return plural

    def ungettext(self, singular, plural, number):
        if number == 1:
            return singular
        else:
            return plural

#def get_lang(language):
#    return DummyTranslation()

# Must be replaced after the bootstrapping phase by a function that returns
# an actual pootle Project object for the language code.
def check_for_language(language):
    try:
        return TranslationProject.objects.get(language=language, project__code='pootle')
    except TranslationProject.DoesNotExist:
        return False

# END BOOTSTRAPPING TRANSLATION CODE

_active_translations = {} # Contains a mapping of threads to Pootle translation projects
_default_translation = DummyTranslation() # See get_default_translation

def activate_for_profile(profile):
    activate(get_lang(profile.ui_lang_id))

def activate(ui_lang_project):
    """Associate the thread in which we are running with the Pootle project
    object ui_lang_project."""
    _active_translations[currentThread()] = ui_lang_project

def get_active():
    """Return the Pootle project object associated with the thread in which we
    are running."""
    try:
        return _active_translations[currentThread()]
    except KeyError:
        return DummyTranslation()

def deactivate():
    """Remove the associate between the thread in which are running
    and its associated Pootle translation project."""
    try:
        del _active_translations[currentThread()]
    except KeyError:
        pass

def get_default_translation():
    """If Django needs to translate anything, but it's not busy serving
    an HTTP request, then the thread in which we are running won't be
    associated with a Pootle project object (remember that this association
    is stored in _active_translations).

    In this case, the default translation is looked up in settings.LANGUAGE.
    If we have a project named 'pootle' for that language, then we return
    its project object. Otherwise, we just return an English project object.
    """
    global _default_translation
    if isinstance(_default_translation, DummyTranslation):
        try:
            _default_translation = get_lang(Language.objects.get(code=settings.LANGUAGE_CODE))
        except Language.DoesNotExist, e:
            pass
    return _default_translation

def get_translation():
    """Return the Pootle project object associated with the thread in
    which we are running. If there is no associated project object
    (which happens if either the localization middleware isn't being
    used, or if Django code is being used outside of an HTTP request,
    such as on the terminal)."""
    t = _active_translations.get(currentThread(), None)
    if t is not None:
        return t
    else:
        return get_default_translation()

def as_unicode(val):
    if isinstance(val, unicode):
        return val
    else:
        return val.decode('utf-8')

def as_str(val):
    if isinstance(val, str):
        return val
    else:
        return val.encode('utf-8')

def _format_gettext(message, vars):
    """since python and gettext stupidly have no way of expanding
    format variables without throwing exceptions, try formatting here
    and return format string if expansion fails."""
    if vars is not None:
        try:
            return message % vars
        except:
            pass
    return message

def gettext(message, vars=None):
    return _format_gettext(as_str(ugettext(message)), vars)

def ugettext(message, vars=None):
    return _format_gettext(as_unicode(get_translation().ugettext(message)), vars)

def ngettext(singular, plural, number, vars=None):
    return _format_gettext(as_str(ungettext(singular, plural, number)), vars)

def ungettext(singular, plural, number, vars=None):
    return _format_gettext(as_unicode(get_translation().ungettext(singular, plural, number)), vars)

def get_language():
    """A function in the translation module to be used in the templates with
        get_current_language as LANGUAGE_CODE
    Since we hijack everything else, we have to hijack this as well."""
    return _active_translations[currentThread()].language.code

def get_language_bidi():
    """A stupidly named Django function to indicate if the current language is
    RTL. We have to hijack it, but just as well, since their implimentation
    covers far less languages than we do."""
    base_lang = get_language().split('-')[0]
    return language_dir(base_lang) == "rtl"

def hijack_django_translation_functions():
    # Here is where we hijack the Django localization functions.
    # These lines are crucial, since they ensure that all translation
    # requests go via our translation functions.
    translation.gettext   = gettext
    translation.ugettext  = ugettext
    translation.ngettext  = ngettext
    translation.ungettext = ungettext

    translation.gettext_lazy   = lazy(gettext, str)
    translation.ngettext_lazy  = lazy(ngettext, str)
    translation.ugettext_lazy  = lazy(ugettext, unicode)
    translation.ungettext_lazy = lazy(ungettext, unicode)

    translation.get_language = get_language
    translation.get_language_bidi = get_language_bidi

hijack_django_translation_functions()


def get_lang(language):
    """Used by the localization system to get hold of a
    TranslationProject which can used to do UI translations"""
    try:
        return TranslationProject.objects.get(language=language, project__code='pootle')
    except TranslationProject.DoesNotExist:
        return None
