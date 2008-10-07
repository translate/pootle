#!/usr/bin/env python
# -*- coding: utf-8 -*

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
# This module is working on tests for Highlighter classes


import sys
import os
import unittest
import World
import tableTM
from translate.storage import factory
from translate.search import match
from translate.misc import wStringIO
from translate.storage import po
from PyQt4 import QtCore, QtGui

class TestTableTM(unittest.TestCase):
    def setUp(self):
        self.tableTM = tableTM.tableTM(None)
        self.slotReached = False
        self.call = 0
        message = '''# aaaaa
#: kfaximage.cpp:189
#, fuzzy
msgid "Unable to open file for reading."
msgstr "unable, to read file"

#: archivedialog.cpp:126
msgid "Could not open a temporary file"
msgstr "Could not open any"

#: archivedialog.cpp:126
msgid "temporary file"
msgstr "open any"
'''
        store = po.pofile.parsestring(message)
        self.matcher = match.matcher(store, 10, 75, 300)
        
    def testfillTable(self):
        """
        Test that the candidates is filled correctly in the table.
        """
        
        # Test with no candidates
        candidates = []
        self.tableTM.fillTable(candidates)
        self.assertEqual(len(candidates), 0)
        
        # Test with candidates
        candidates = self.matcher.candidates.units
        self.tableTM.setVisible(True)
        for i in range(len(candidates)):
            self.matcher.candidates.units[i].filepath = "/tmp/a.po"
        
        self.tableTM.fillTable(candidates)
        self.assertEqual(len(candidates), 2)
        self.assertEqual(len(candidates), self.tableTM.ui.tblTM.rowCount())
    
    def testEmitSignal(self):
        """
        Test that the signal is emitted only have item.
        """
        QtCore.QObject.connect(self.tableTM, QtCore.SIGNAL("translation2target"), self.slot)
        QtCore.QObject.connect(self.tableTM, QtCore.SIGNAL("openFile"), self.slot)
        QtCore.QObject.connect(self.tableTM, QtCore.SIGNAL("findUnit"), self.slot)
        
        # Test that if there is no candidates, the signal is not emitted
        candidates = []
        self.tableTM.setVisible(True)
        self.tableTM.fillTable(candidates)
        self.tableTM.emitTarget()
        self.assertEqual(self.slotReached, False)
        
        #Test with candidates
        candidates = self.matcher.candidates.units
        self.tableTM.allowUpdate = True
        for i in range(len(candidates)):
            self.matcher.candidates.units[i].filepath = "/tmp/a.po"
        
        self.tableTM.fillTable(candidates)
        self.assertEqual(len(candidates), 2)
        self.assertEqual(len(candidates), self.tableTM.ui.tblTM.rowCount())
        self.tableTM.ui.tblTM.selectRow(0)
        self.tableTM.emitTarget()
        self.tableTM.emitOpenFile()
        self.assertEqual(self.slotReached, True)
        self.assertEqual(self.call, 3)
    
    def testShorten(self):
        """
        Test that it returns only the first part of text, seperated by new line and filled with three dots. 
        """
        text = "first line \n second line\n"
        text = self.tableTM.shorten(text)
        self.assertEqual(text, "first line ...")
        
        text = "first line \n second line\n third line "
        text = self.tableTM.shorten(text)
        self.assertEqual(text, "first line ...")
        
    def slot(self):
        self.slotReached = True
        self.call +=1
        
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    unittest.main()
