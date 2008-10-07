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
# This module is working on tests for tmSetting classes

from PyQt4 import QtCore, QtGui
from pootling.ui.Ui_tmSetting import Ui_tmsetting
import os, sys
import unittest
import tempfile
from pootling.modules import tmSetting
from translate.search import match
        
class Test_tmSetting(unittest.TestCase):
    
    def setUp(self):
        self.tm = tmSetting.tmSetting(None)
        self.glossary = tmSetting.glossarySetting(None)
        self.tm.lazyInit()
        self.glossary.lazyInit()
        self.tm.filenames = []
        
    def testAddLocation(self):
        """
        Test Add TMpath to TM list.
        """
    
        # Test that the items in the list same as the path that we add into.
        TMpath = '/tmp/a.po'
        self.tm.addLocation(TMpath, QtCore.Qt.Checked)
        items = self.tm.getPathList(QtCore.Qt.Checked)
        self.assertEqual(str(items[0]), TMpath)
        
        # Test that the path cannot be duplicated.
        TMpath = '/tmp/a.po'
        self.tm.addLocation(TMpath, QtCore.Qt.Checked)
        items = self.tm.getPathList(QtCore.Qt.Checked)
        self.assertEqual(str(items[0]), TMpath)
        
        # Test with different path
        TMpath = '/tmp/b.xlf'
        self.tm.addLocation(TMpath, QtCore.Qt.Checked)
        items = self.tm.getPathList(QtCore.Qt.Checked)
        self.assertEqual(str(items[0]), '/tmp/a.po')
        self.assertEqual(len(items), 2)
        self.assertEqual(str(items[1]), '/tmp/b.xlf')
        
        # Test addlocation with GlossarySetting
        self.glossary.addLocation(TMpath, QtCore.Qt.Checked)
        items = self.glossary.getPathList(QtCore.Qt.Checked)
        self.assertEqual(str(items[0]), TMpath)
    
    def testRemoveLocation(self):
        """
        Test Remove selected TMpath from TM list.
        """
        self.tm.ui.listWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        TMpath = '/tmp/b.xlf'
        self.tm.addLocation(TMpath, QtCore.Qt.Checked)
        item = self.tm.ui.listWidget.item(0)
        self.tm.ui.listWidget.setCurrentItem(item)
        self.tm.removeLocation()
        items = self.tm.getPathList(QtCore.Qt.Checked)
        self.assertEqual(len(items), 0)
    
    def testGetFiles(self):
        """
        Test that we get the correct filenames and includeSub is working correctly.
        """
        filepaths = []
        # Test that it include only the supported files.
        for i in range(2):
            handle, filepath = tempfile.mkstemp('.xlf')
            filepaths.append(filepath)
            self.tm.getFiles(filepath, True)
        self.assertEqual(self.tm.filenames[0], filepaths[0])
        self.assertEqual(self.tm.filenames[1], filepaths[1])
        handle, filepath = tempfile.mkstemp('.po')
        filepaths.append(filepath)
        self.tm.getFiles(filepath, True)
        self.assertEqual(self.tm.filenames[2], filepaths[2])
        # Test that the unsupported filetype is not included.
        handle, filepath = tempfile.mkstemp('.exe')
        filepaths.append(filepath)
        self.tm.getFiles(filepath, True)
        self.assertEqual(len(self.tm.filenames), 3)
        for filepath in filepaths:
            os.remove(filepath)
        # Test test if it is a directrory and includeSub is True, dive into sub
        dirpathTop = tempfile.mkdtemp('','TEST','/tmp')
        dirpath = tempfile.mkdtemp('','TEST', dirpathTop)
        self.tm.getFiles(dirpath, True)
        # No supported file in the folder, so the number of files remains unchanged.
        self.assertEqual(len(self.tm.filenames), 3)
        handle, filepath = tempfile.mkstemp('.po','',dirpath)
        # Have supported file in the chile folder, but we choose not to include sub, so the number of files remains unchanged.
        self.tm.getFiles(dirpathTop, False)
        self.assertEqual(len(self.tm.filenames), 3)
        # Have supported file in the chile folder, but we choose to include sub, so the number of files changed.
        self.tm.getFiles(dirpathTop, True)
        self.assertEqual(len(self.tm.filenames), 4)
        os.remove(filepath)
        os.rmdir(dirpath)
        os.rmdir(dirpathTop)
        
    def testGetPathList(self):
        """
        Test that it returns a list of path according to the parameter isChecked or unChecked.
        """
        TMpath = '/tmp/a.po'
        self.tm.addLocation(TMpath, QtCore.Qt.Checked)
        # If the path is checked
        itemList = self.tm.getPathList(QtCore.Qt.Checked)
        self.assertEqual(str(itemList[0]), TMpath)
        
         # If the path is not checked
        itemList = self.tm.getPathList(QtCore.Qt.Unchecked)
        self.assertEqual(len(itemList), 0)
        
    def testCreateStore(self):
        """
        Test that it creates a store object from file.
        add translator, date, and filepath properties to store object.
        """
        message = '''msgid ""
msgstr ""
"POT-Creation-Date: 2005-05-18 21:23+0200\n"
"PO-Revision-Date: 2006-11-27 11:50+0700\n"
"Project-Id-Version: cupsdconf\n"
""
# aaaaa
#: kfaximage.cpp:189
msgid "Unable to open file for reading."
msgstr "unable to read file"
'''

        fp, filename = tempfile.mkstemp('.po')
        fp = open(filename,'w')
        fp.write(message)
        fp.close()
        store = self.tm.createStore(filename)
        self.assertEqual(store.translator, "")
        self.assertEqual(store.date,"2006-11-27 11:50+0700")
        self.assertEqual(store.filepath, filename)
        self.assertEqual(store.filepath, filename)
        self.assertEqual(store.units[1].source, "Unable to open file for reading.")
        self.assertEqual(store.units[1].target, "unable to read file")
        os.remove(filename)
        
    def testBuildMatcher(self):
        """
        Test that we can build the correct matcher.
        """
        self.tm.section = 'TM'
        self.tm.ui.spinSimilarity.setValue(75)
        self.tm.ui.spinMaxCandidate.setValue(10)
        self.tm.ui.spinMaxLen.setValue(70)
        handle, self.tm.pickleFile = tempfile.mkstemp('','PKL')
        dirpathTop = tempfile.mkdtemp('','TEST','/tmp')
        dirpath = tempfile.mkdtemp('','TEST', dirpathTop)
        
        # Test that it do nothing if no filename
        self.tm.buildMatcher(QtCore.QStringList(dirpath), True)
        self.assertEqual(self.tm.matcher, None)
        self.assertEqual(isinstance(self.tm.matcher,match.matcher), False)
        self.assertEqual(isinstance(self.tm.matcher,match.terminologymatcher), False)
        
        # Test that it starts to build matcher with given file
        handle, path = tempfile.mkstemp('.po','',dirpath)
        self.tm.buildMatcher(QtCore.QStringList(path), True)
        self.assertEqual(isinstance(self.tm.matcher,match.matcher), True)
        self.assertEqual(isinstance(self.tm.matcher,match.terminologymatcher), False)
        os.remove(path)
        os.rmdir(dirpath)
        os.rmdir(dirpathTop)
        
        os.remove(self.tm.pickleFile)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    unittest.main()
    
