#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#Copyright (c) 2006 - 2007 by The WordForge Foundation
#                       www.wordforge.org
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
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
# This module is working on tests for Comment classes


import sys
import Comment
from translate.misc import wStringIO
from translate.storage import po
from PyQt4 import QtCore, QtGui
import unittest
import World

class TestComment(unittest.TestCase):
    def setUp(self):
        self.commentObj = Comment.CommentDock(None)
        self.slotReached = False
        self.message = '''# aaaaa
#: kfaximage.cpp:189
#, fuzzy
msgid "Unable to open file for reading."
msgstr "unable to read file"
'''
        self.pofile = self.poparse(self.message)
        self.currentunit = self.pofile.units[0]

    def testEmitCommentChanged(self):
        """Test that signal commentChanged is emitted and reach the specific slot."""
        QtCore.QObject.connect(self.commentObj, QtCore.SIGNAL("commentChanged"), self.slot)
        QtCore.QObject.connect(self.commentObj, QtCore.SIGNAL("textChanged"), self.slot)
        self.commentObj.ui.txtTranslatorComment.selectAll()
        self.commentObj.ui.txtTranslatorComment.insertPlainText('text')
        self.commentObj.textChanged()
        self.commentObj.emitCommentChanged()
        self.assertEqual(self.slotReached, True)
        
    def testTextChanged(self):
        """Test that signal textchanged is emitted while typing."""
        QtCore.QObject.connect(self.commentObj, QtCore.SIGNAL("textChanged"), self.slot)
        self.commentObj.ui.txtTranslatorComment.selectAll()
        self.commentObj.ui.txtTranslatorComment.insertPlainText('text')
        self.commentObj.textChanged()
        self.assertEqual(self.slotReached, True)
        
    def testCloseEvent(self):
        """Test that after closing the commentDock, uncheck Comment in submenu."""
        close_event = QtGui.QCloseEvent()
        self.commentObj.closeEvent(close_event)
        self.assertEqual(self.commentObj.toggleViewAction().isChecked(), False)
    
    def testUpdateView(self):
        """Test that the text in comment view obtained from the getnotes of currentunit.
        and the view is also editable."""
        self.commentObj.updateView(self.currentunit)
        self.assertEqual(str(self.commentObj.ui.txtTranslatorComment.toPlainText()), "aaaaa")
        self.assertEqual(str(self.commentObj.ui.txtTranslatorComment.toPlainText()), self.currentunit.getnotes())
        self.assertEqual(self.commentObj.ui.txtTranslatorComment.isEnabled(), True)
        
    def testViewSetting(self):
        """Test that view status of txtTranslatorComment and txtLocationComment is correct."""
        self.commentObj.toggleViewAction().setChecked(True)
        self.commentObj.updateView(self.currentunit)
        self.commentObj.viewSetting(self.currentunit)
        self.assertEqual(self.commentObj.ui.txtLocationComment.isHidden(), False)
        self.assertEqual(str(self.commentObj.ui.txtTranslatorComment.toPlainText()), "aaaaa")

    def testSetSearchString(self):
        """Test that it takes the right string and the correct fondPosition to search for."""
        foundPosition = 1
        self.commentObj.updateView(self.currentunit)
        self.commentObj.setSearchString("ka", World.comment, foundPosition)
        self.assertEqual(self.commentObj.highlighter.searchString, "ka")
        self.assertEqual(self.commentObj.highlighter.foundPosition, foundPosition )

    def testReplaceText(self):
        """Test that the replacing text is correct at the right position and length."""
        position = 0
        length = 2
        self.commentObj.updateView(self.currentunit)
        self.commentObj.replaceText(World.comment, position, length, 'ka')
        self.assertEqual(str(self.commentObj.ui.txtTranslatorComment.toPlainText()), 'kaaaa')
        self.commentObj.replaceText(World.comment, 5, length, 'ka')
        self.assertEqual(str(self.commentObj.ui.txtTranslatorComment.toPlainText()), 'kaaaaka')
        
    def poparse(self, posource):
        """helper that parses po source without requiring files"""
        dummyfile = wStringIO.StringIO(posource)
        return po.pofile(dummyfile)
        
    def slot(self):
        """Slot to test if it gets called by a specific signal."""
        self.slotReached = True
    
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    unittest.main()
