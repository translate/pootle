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
# This module is working on tests for catalogSetting classes

from PyQt4 import QtCore, QtGui
from pootling.ui.Ui_CatalogSetting import Ui_catalogSetting
import os, sys
import unittest
from pootling.modules import CatalogSetting
        
class Test_catalogSetting(unittest.TestCase):
    
    def setUp(self):
        self.catalog = CatalogSetting.CatalogSetting(None)
        self.catalog.ui.listWidget.clear()
        
    def getPathList(self):
        """return paths in Catalog list."""
        CatalogPaths = QtCore.QStringList()
        for i in range(self.catalog.ui.listWidget.count()):
            CatalogPaths.append(self.catalog.ui.listWidget.item(i).text())
        return CatalogPaths
    
    
    def testAddLocation(self):
        """Test Add TMpath to TM list."""
    
        #Test that the items in the list same as the path that we add into.
        path = '/tmp/a.po'
        self.catalog.addLocation(QtCore.QString(path))
        CatalogPaths = self.getPathList()
        self.assertEqual(str(CatalogPaths[0]), path)
        
        #Test that the path cannot be duplicated.
        TMpath = '/tmp/a.po'
        self.catalog.addLocation(QtCore.QString(path))
        CatalogPaths = self.getPathList()
        self.assertEqual(str(CatalogPaths[0]), path)

        #Test with different path
        path = '/tmp/b.xlf'
        self.catalog.addLocation(QtCore.QString(path))
        CatalogPaths = self.getPathList()
        self.assertEqual(str(CatalogPaths[0]), '/tmp/a.po')
        self.assertEqual(len(CatalogPaths), 2)
        self.assertEqual(str(CatalogPaths[1]), '/tmp/b.xlf')

    def testRemoveLocation(self):
        """Test Remove selected path from Catalog list."""
        self.catalog.ui.listWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        path = '/tmp/b.xlf'
        self.catalog.addLocation(QtCore.QString(path))
        item = self.catalog.ui.listWidget.item(0)
        self.catalog.ui.listWidget.setCurrentItem(item)
        self.catalog.removeLocation()
        CatalogPaths = self.getPathList()
        self.assertEqual(len(CatalogPaths), 0)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    unittest.main()
    
