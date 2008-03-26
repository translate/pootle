#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
# This module stores status

import pootling.modules.World as World

class Status:
    
    # FIXME: toggle unit's fuzzy is not working
    def __init__(self, store):
        """
        Set the number of translated, fuzzy, untranslated units to global variables.
        
        @param store: the new storage class.
        """
        self.store = store
        self.numTranslated = store.translated_unitcount()
        self.numFuzzy = store.fuzzy_unitcount()
        self.numUntranslated = store.untranslated_unitcount()
        self.numTotal = self.numTranslated + self.numFuzzy + self.numUntranslated
        self.nplurals = World.settings.value("nPlural").toInt()[0]
    
    def unitState(self, unit):
        """
        return bitwise indicating state of unit.
        bitwises are defined in World class.
        
        @param unit: a class unit whose state is returned.
        """
        state = 0
        if (unit.isheader()):
            return state
        if (unit.isfuzzy()):
            state += World.fuzzy
        elif (unit.istranslated()):
            state += World.translated
        else:
            state += World.untranslated
        
        if (unit.hasplural() and (self.nplurals > 1)):
            state += World.plural
        
        return state
        
    def markFuzzy(self, unit, fuzzy):
        """
        toggle fuzzy status of a given unit.
        
        @param unit: a class unit whose fuzzy status is toggled.
        @param fuzzy: type as bool.
        """
        if (unit.isfuzzy() and fuzzy):
            return
            
        unit.markfuzzy(fuzzy)
        if (fuzzy):
            self.numFuzzy += 1
            self.numTranslated -= 1
            unit.x_editor_state |= World.fuzzy
            unit.x_editor_state &= ~World.translated
        else:
            self.numFuzzy -= 1
            self.numTranslated += 1
            unit.x_editor_state &= ~World.fuzzy
            unit.x_editor_state |= World.translated

    def markTranslated(self, unit, translated):
        """
        toggle translated status of a given unit.
        
        @param unit: a class unit whose translated status is toggled.
        @param translated: type as bool.
        """
        if (unit.isfuzzy()):
            self.markFuzzy(unit, False)

        if (translated):
            if (not hasattr(unit, "x_editor_state")) or (unit.x_editor_state & World.translated):
                return
            self.numTranslated += 1
            unit.x_editor_state |= World.translated
            unit.x_editor_state &= ~World.untranslated
        else:
            if (unit.x_editor_state & World.untranslated):
                return
            self.numTranslated -= 1
            unit.x_editor_state &= ~World.translated
            unit.x_editor_state |= World.untranslated

    def getStatus(self):
        """
        Return number of untranslated, fuzzy, and translated units as list.
        """
        untranslated = self.numTotal - self.numTranslated - self.numFuzzy
        return [untranslated, self.numFuzzy, self.numTranslated]
