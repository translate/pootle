#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
#
# This file is part of Virtaal.
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

__all__ = ['get_terminology_matcher',
           'set_terminology_source']

import os
import os.path as path

from translate.storage import factory

import pan_app
from translate.search import match


match_store = None # This is if the user specifies a terminology file (as opposed to a directory) on the commmand line
matchers = {}

def get_terminology_directory():
    return pan_app.settings.general["terminology-dir"]

def get_suggestion_stores(lang_code):
    """Return a suggestion store which is an amalgamation of all the translation
    stores under <termininology_directory>/<lang_code>."""
    if match_store != None:
        yield match_store
    else:
        for base, _dirnames, filenames in os.walk(path.join(get_terminology_directory(), lang_code)):
            for filename in filenames:
                try: # Try to load filename as a translation store...
                    yield factory.getobject(path.join(base, filename))
                except ValueError: # If filename isn't a translation store, we just do nothing
                    pass

def get_terminology_matcher(lang_code):
    """Return a terminology matcher based on a translation store which is an
    amalgamation of all translation stores under
    <termininology_directory>/<lang_code>

    <termininology_directory> is the globally specified termininology directory.
    <lang_code> is the supplied parameter.

    @return: a translate.search.match.terminologymatcher"""
    if lang_code not in matchers:
        stores = list(get_suggestion_stores(pan_app.settings.language["contentlang"]))
        matchers[lang_code] = match.terminologymatcher(stores)
    return matchers[lang_code]

def set_terminology_source(src):
    global match_store
    if isinstance(src, (str, unicode)):
        pan_app.settings.general["terminology-dir"] = src
    else:
        match_store = src
