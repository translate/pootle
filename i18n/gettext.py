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

from Pootle import pan_app

_active_translations = {} # Contains a mapping of threads to Pootle translation projects
_default_translation = None # See get_default_translation

def get_lang(code):
    return pan_app.get_po_tree().getproject(code, 'pootle')

def check_for_language(code):
    return 'pootle' in pan_app.get_po_tree().projects and code in  pan_app.get_po_tree().languages

def activate(ui_lang_project):
    """Associate the thread in which we are running with the Pootle project
    object ui_lang_project."""
    _active_translations[currentThread()] = ui_lang_project

def get_active():
    """Return the Pootle project object associated with the thread in which we
    are running."""
    return _active_translations[currentThread()]

def deactivate():
    """Remove the associate between the thread in which are running
    and its associated Pootle translation project."""
    del _active_translations[currentThread()]

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
    if _default_translation is None:
        from django.conf import settings
        if check_for_language(settings.LANGUAGE_CODE):
            _default_translation = get_lang(settings.LANGUAGE_CODE)
        else:
            _default_translation = get_lang('en')
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

def gettext(message):
    return ugettext(message)

def ugettext(message):
    return get_translation().ugettext(message)

def ngettext(singular, plural, number):
    return ungettext(singular, plural, number)

def ungettext(singular, plural, number):
    return get_translation().ungettext(singular, plural, number)

# Here is where we monkey-patch the Django localization functions.
# These lines are crucial, since they ensure that all translation
# requests go via our translation functions.
translation.gettext   = gettext
translation.ugettext  = ugettext
translation.ngettext  = ngettext
translation.ungettext = ungettext


