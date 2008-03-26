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
# This module is working on tests for FileAction classes


import sys
import FileAction
from PyQt4 import QtCore, QtGui
import unittest

class TestFileAction(unittest.TestCase):
    def setUp(self):
        self.fileActionObj = FileAction.FileAction(None)
        self.slotReached = False
        self.fileName = ""
        
    def testOpenFile(self):
        """Test that if the Ok button on OpenFile dialog is clicked, return True."""
        QtCore.QObject.connect(self.fileActionObj, QtCore.SIGNAL("fileOpened"), self.slot)
        isFileName = self.fileActionObj.openFile()
        if isFileName:
            self.assertEqual(self.slotReached, True)
            self.assertEqual(len(self.fileName) > 0, True)
        else:
            self.assertEqual(self.slotReached, False)
    
    def testSave(self):
        """Test that the file for save and the opened file are the same."""
        QtCore.QObject.connect(self.fileActionObj, QtCore.SIGNAL("fileSaved"), self.slot)
        self.fileActionObj.fileName = QtCore.QString("example")
        self.fileActionObj.save()
        self.assertEqual(self.fileName, self.fileActionObj.fileName)
        
    def testSaveAs(self):
        """Test that we can save to the same format as opened file."""
        QtCore.QObject.connect(self.fileActionObj, QtCore.SIGNAL("fileSaved"), self.slot)
        # test with po file
        self.fileActionObj.fileName = "example.po"
        self.fileActionObj.fileExtension = ".po"
        self.fileActionObj.saveAs()
        if (len(self.fileName) > 0):
            self.assertEqual(QtCore.QString(self.fileName).endsWith("po",  QtCore.Qt.CaseInsensitive), True)
     
        # test with xliff file
        self.fileActionObj.fileName = "example.xliff"
        self.fileActionObj.fileExtension = ".xliff"
        self.fileActionObj.saveAs()
        if (len(self.fileName) > 0):
            self.assertEqual(QtCore.QString(self.fileName).endsWith("xliff",  QtCore.Qt.CaseInsensitive), True)
            
    def slot(self, fileName):
        self.fileName = fileName
        self.slotReached = True
        
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    unittest.main()
