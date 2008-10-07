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

import gtk
import pango

import pan_app

_font_descriptions = {}

def get_font_description(description):
    """Provide a pango.FontDescription and keep it for reuse."""
    global _font_descriptions
    if not description in _font_descriptions:
        _font_descriptions[description] = pango.FontDescription(description)
    return _font_descriptions[description]

def get_source_font_description():
    return get_font_description(pan_app.settings.language["sourcefont"])

def get_target_font_description():
    return get_font_description(pan_app.settings.language["targetfont"])


_languages = {}

def get_language(language):
    """Provide a pango.Language and keep it for reuse."""
    global _languages
    if not language in _languages:
        _languages[language] = pango.Language(language)
    return _languages[language]

def get_source_language():
    return get_language(pan_app.settings.language["sourcelang"])

def get_target_language():
    return get_language(pan_app.settings.language["contentlang"])

