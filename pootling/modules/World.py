#!/usr/bin/python
# -*- coding: utf8 -*-
#Copyright (c) 2006 - 2007 by The WordForge Foundation
#                       www.wordforge.org
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# See the LICENSE file for more details. 
# 
# Developed by:
#       Hok Kakada (hokkakada@khmeros.info)
#       Keo Sophon (keosophon@khmeros.info)
#       San Titvirak (titvirak@khmeros.info)
#       Seth Chanratha (sethchanratha@khmeros.info)
# 
# This module stores global variables for use in whole applicaion.

from PyQt4 import QtCore

# helper constants for filtering
header = 0
fuzzy = 1
translated = 2
untranslated = 4
plural = 8
filterAll = 4 + 2 + 1

source = 1
target = 2
comment = 4

searchForward = 1
searchBackward = 2
searchStatic = 4

searchFormat = 1
glossaryFormat = 2

# this is the global settings object, use only this for saving and restoring settings

settingOrg = "WordForge"
settingApp = "Pootling"
settings = QtCore.QSettings(QtCore.QSettings.IniFormat, QtCore.QSettings.UserScope,settingOrg, settingApp)

# maximum number of files in the recent file menu
MaxRecentFiles = 9

fileFilters = ["All Supported Files (*.po *.pot *.xliff *.xlf *.tmx *.tbx)", 
        "PO Files and PO Template Files (*.po *.pot)",
        "XLIFF Files (*.xliff *.xlf)",
        "Translation Memory eXchange (TMX) Files (*.tmx)",
        "TermBase eXchange (TBX) Files (*.tbx)",
        "All Files (*)"]

# Project mode
projectNew = 1
projectProperty = 2
