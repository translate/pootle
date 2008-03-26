#!/usr/bin/python
# -*- coding: utf-8 -*-

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

 
# This module is working on tests for TUview classes

import unittest
import sys
import os.path
sys.path.append(os.path.join(sys.path[0], ".."))
import TUview
import Status
import World
from PyQt4 import QtGui, QtCore
from translate.misc import wStringIO
from translate.storage import po

class TestTUview(unittest.TestCase):
    def setUp(self):
        self.tuview = TUview.TUview(None)
        self.slotReached = False
        self.message = '''# aaaaa
#: kfaximage.cpp:189
#, fuzzy
msgid "Unable to open file for reading."
msgstr "unable to read file"

#: archivedialog.cpp:126
msgid "Could not open a temporary file"
msgstr "Could not open"
'''
        self.store = po.pofile.parsestring(self.message)
        self.currentunit = self.store.units[0]
        self.status = Status.Status(self.store)

    def testCloseEvent(self):
        """
        Test that after closing the tuviewDock, uncheck TUview in submenu.
        """
        close_event = QtGui.QCloseEvent()
        self.tuview.closeEvent(close_event)
        self.assertEqual(self.tuview.toggleViewAction().isChecked(), False)
        
    def testEmitCurrentIndex(self):
        """
        Test that the slot is reached.
        """
        QtCore.QObject.connect(self.tuview, QtCore.SIGNAL("scrollToRow"), self.slot)
        self.tuview.emitCurrentIndex(4)
        self.tuview.ui.fileScrollBar.setValue(4)
        self.assertEqual(self.slotReached, True)
        
    def testEmitGlossaryWords(self):
        """
        Test that the single 'term' is emitted.
        """
        QtCore.QObject.connect(self.tuview, QtCore.SIGNAL("term"), self.slot)
        self.tuview.sourceHighlighter.glossaryWords = ['pootling','translation','editor']
        self.tuview.emitGlossaryWords()
        self.assertEqual(self.slotReached, True)
        
#    def testEmitTermRequest(self):
#        """
#        Test that the single 'lookupTerm' is emitted.
#        """
#        QtCore.QObject.connect(self.tuview, QtCore.SIGNAL("lookupTerm"), self.slot)
#        self.tuview.ui.txtSource.setPlainText("Pootling is an offline translation editor")
#        self.tuview.sourceHighlighter.glossaryWords = ['Pootling','offline translation','editor']
#
#        pos = QtCore.QPoint(5,16)
#        self.tuview.emitTermRequest(pos)
#        # test with word with space
#        self.assertEqual(self.slotReached, True)
#        #TODO: test with word without space
    
    def testFilterChanged(self):
        """
        Test that we can adjust the scrollbar maximum according to lenFilter.
        """
        filter = World.fuzzy + World.translated + World.untranslated
        self.tuview.filterChanged(filter, 2)
        self.assertEqual(self.tuview.ui.fileScrollBar.maximum(), 1)  #fileScrollBar start from 0
        
    def testUpdateView(self):
        """
        Test that we can
        1. Update the text in source and target, set the scrollbar position,
        2. Remove a value from scrollbar if the unit is not in filter.
        3. Recalculate scrollbar maximum value.
        """
        
        self.currentunit.x_editor_row = 0
        self.tuview.updateView(self.currentunit)
        self.assertEqual(self.tuview.ui.txtSource.toPlainText(), self.currentunit.source)
        self.assertEqual(self.tuview.ui.txtTarget.toPlainText(), self.currentunit.target)
        
    def testEmitTargetChanged(self):
        """
        Test that signal targetChanged is emitted and reach the specific slot.
        """
        QtCore.QObject.connect(self.tuview, QtCore.SIGNAL("targetChanged"), self.slot)
        QtCore.QObject.connect(self.tuview, QtCore.SIGNAL("textChanged"), self.slot)
        self.tuview.ui.txtTarget.document().setModified(True)
        self.tuview.emitTextChanged()
        self.tuview.emitTargetChanged()
        self.assertEqual(self.slotReached, True)
        
    def testEmitTextChanged(self):
        """
        Test that signal emitTextChanged is emitted while typing.
        """
        QtCore.QObject.connect(self.tuview, QtCore.SIGNAL("textChanged"), self.slot)
        self.tuview.ui.txtTarget.document().setModified(True)
        self.tuview.emitTextChanged()
        self.assertEqual(self.slotReached, True)
    
    def testSource2Target(self):
        """
        Test that text in source and target are the same after copying from source to target.
        """
        self.tuview.ui.txtSource.setPlainText('a')
        # test with single unit
        self.tuview.secondpage = False
        self.tuview.source2target()
        self.assertEqual(self.tuview.ui.txtSource.toPlainText(), self.tuview.ui.txtTarget.toPlainText())
        
        # TODO: test with plural unit

        
    def testSetSearchString(self):
        """
        Test that it takes the right string and the correct fondPosition to search for.
        """
        self.currentunit.x_editor_row = None
        foundPosition = 1
        self.tuview.updateView(self.currentunit)
        # send the search string in txtTarget
        self.tuview.setSearchString("ka", World.target, foundPosition)
        self.assertEqual(self.tuview.targetHighlighter.searchString, "ka")
        self.assertEqual(self.tuview.targetHighlighter.foundPosition, foundPosition )
        
        # send the search string in txtSource
        self.tuview.setSearchString("kaka", World.source, foundPosition)
        self.assertEqual(self.tuview.sourceHighlighter.searchString, "kaka")
        self.assertEqual(self.tuview.sourceHighlighter.foundPosition, foundPosition )
        
    def testReplaceText(self):
        """
        Test that the replacing text is correct at the right position and length.
        """
        position = 0
        length = 2
        self.tuview.ui.txtTarget.setPlainText('hello')
        self.tuview.replaceText(World.target, position, length, 'k')
        self.assertEqual(str(self.tuview.ui.txtTarget.toPlainText()), 'kllo')
        
    def testViewSetting(self):
        """
        Test that view status of txtSource and txtTarget is correct.
        """
        self.currentunit.x_editor_row = None
        self.tuview.toggleViewAction().setChecked(True)
        #Test for single unit
        self.tuview.updateView(self.currentunit)
        self.tuview.viewSetting(self.currentunit)
        self.assertEqual(self.tuview.ui.txtSource.isEnabled(), True)
        self.assertEqual(self.tuview.ui.txtTarget.isEnabled(), True)
        # TODO: Test for plural units
        
        # TODO: Test for unit that have developer comment
        
        # TODO: Test for unit that doesn't have developer comment
    
    def slot(self):
        self.slotReached = True
        
if __name__== '__main__':
    app = QtGui.QApplication(sys.argv)
    unittest.main()
