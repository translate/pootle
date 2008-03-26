#!/usr/bin/env python
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
# # Developed by:
#       Hok Kakada (hokkakada@khmeros.info)
#       Keo Sophon (keosophon@khmeros.info)
#       San Titvirak (titvirak@khmeros.info)
#       Seth Chanratha (sethchanratha@khmeros.info)
# 
# This module is working on tests for Find classes

import sys
import unittest
import os.path
sys.path.append(os.path.join(sys.path[0], ".."))
import  Find
from PyQt4 import QtCore, QtGui

class TestFind(unittest.TestCase):
    def setUp(self):
        self.find = Find.Find(None)
        self.slotReached = False
    
    def test_TextChanged(self):
        QtCore.QObject.connect(self.find, QtCore.SIGNAL("initSearch"), self.slot)
        self.find.ui.insource.setChecked(True)
        self.find.ui.intarget.setChecked(True)
        self.find.ui.incomment.setChecked(True)
        self.find.ui.lineEdit.setText('a')
        self.assertEqual(self.slotReached, True)
        
    def testInitSearch(self):
        QtCore.QObject.connect(self.find, QtCore.SIGNAL("initSearch"), self.slot)
        #test if search in source, target, and comment are checked
        self.find.ui.insource.setChecked(True)
        self.find.ui.intarget.setChecked(True)
        self.find.ui.incomment.setChecked(True)
        self.find.initSearch()
        self.assertEqual(self.slotReached, True)
        
        #test if search in source, target, and comment are not checked
        self.find.ui.insource.setChecked(False)
        self.find.ui.intarget.setChecked(False)
        self.find.ui.incomment.setChecked(False)
        self.assertEqual(type(self.find.statusTip()), type(QtCore.QString()))
    
    def testFindPrevious(self):
        QtCore.QObject.connect(self.find, QtCore.SIGNAL("searchPrevious"), self.slot)
        self.find.findPrevious()
        self.assertEqual(self.slotReached, True)
    
    def testFindNext(self):
        QtCore.QObject.connect(self.find, QtCore.SIGNAL("searchNext"), self.slot)
        self.find.findNext()
        self.assertEqual(self.slotReached, True)
    
    def testReplace(self):
        QtCore.QObject.connect(self.find, QtCore.SIGNAL("replace"), self.slot)
        self.find.replace()
        self.assertEqual(self.slotReached, True)
    
    def testReplaceAll(self):
        QtCore.QObject.connect(self.find, QtCore.SIGNAL("replaceAll"), self.slot)
        self.find.replaceAll()
        self.assertEqual(self.slotReached, True)
    
    def slot(self):
        self.slotReached = True

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    unittest.main()
