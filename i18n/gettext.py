#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2008 Zuza Software Foundation
# 
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from django.utils import translation
from django.utils.thread_support import currentThread
from django.utils.functional import lazy

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

# Must be replaced after the bootstrapping phase by a function that returns
# and actual pootle Project object for the language code.
def get_lang_real(language):
    from pootle_app.translation_project import TranslationProject
    return TranslationProject.objects.get(language=language, project__code='pootle')

def get_lang(language):
    return DummyTranslation()

# Must be replaced after the bootstrapping phase by a function that returns
# and actual pootle Project object for the language code.
def check_for_language(code):
    return False

# END BOOTSTRAPPING TRANSLATION CODE

_active_translations = {} # Contains a mapping of threads to Pootle translation projects
_default_translation = DummyTranslation() # See get_default_translation

def activate_for_profile(profile):
    activate(get_lang(profile.ui_lang))

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
        from django.conf import settings
        try:
            _default_translation = get_lang(settings.LANGUAGE_CODE)
        except:
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

def gettext(message):
    return as_str(ugettext(message))

def ugettext(message):
    return as_unicode(get_translation().ugettext(message))

def ngettext(singular, plural, number):
    return as_str(ungettext(singular, plural, number))

def ungettext(singular, plural, number):
    return as_unicode(get_translation().ungettext(singular, plural, number))

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

hijack_django_translation_functions()
