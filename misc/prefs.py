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

from Pootle.legacy.jToolkit import prefs

def set_default_preferences(prefs):
    changed = False
    if not hasattr(prefs, "title"):
        setattr(prefs, "title", "Pootle Demo")
        changed = True
    if not hasattr(prefs, "description"):
        defaultdescription = "This is a demo installation of pootle. The administrator can customize the description in the preferences."
        setattr(prefs, "description", defaultdescription)
        changed = True
    if not hasattr(prefs, "enablealtsrc"):
        setattr(prefs, "enablealtsrc", False)
        changed = True
    if changed:
        save_preferences(prefs)

def load_preferences(prefs_file):
    parser = prefs.PrefsParser()
    parser.parsefile(prefs_file)
    p = parser.Pootle
    set_default_preferences(p)
    return p

def save_preferences(prefs):
    prefsfile = prefs.__root__.__dict__["_setvalue"].im_self
    prefsfile.savefile()

def change_preferences(prefs, argdict):
    """changes options on the instance"""
    for key, value in argdict.iteritems():
        if not key.startswith("option-"):
            continue
        optionname = key.replace("option-", "", 1)
        setattr(prefs, optionname, value)
    save_preferences(prefs)
