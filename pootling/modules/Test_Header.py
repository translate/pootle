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
# This module is working on tests for Header classes

"""tests for Header classes"""

import sys
import Header
import Operator
from translate.storage import po
from PyQt4 import QtCore, QtGui
import unittest
import World

class TestHeader(unittest.TestCase):
    def setUp(self):
        self.HeaderObj = Header.Header(None, Operator.Operator())
        self.HeaderObj.showDialog()
        self.headerDic = {}
        self.HeaderObj.ui.tableHeader.setRowCount(10)
        self.HeaderObj.ui.tableHeader.setCurrentCell(1,0)

    def testNaviState(self):
        #if table has no row
        self.HeaderObj.ui.tableHeader.setRowCount(0)
        QtCore.QObject.connect(self.HeaderObj.ui.tableHeader,QtCore.SIGNAL("currentItemChanged(QTableWidgetItem *, QTableWidgetItem *)"), self.HeaderObj.naviState)
        self.assertEqual(self.HeaderObj.ui.btnUp.isEnabled(), False)
        self.assertEqual(self.HeaderObj.ui.btnDown.isEnabled(), False)
        
        self.HeaderObj.ui.tableHeader.setRowCount(10)
        self.HeaderObj.ui.btnDown.setEnabled(True)
        # if the top row is the current row
        self.HeaderObj.ui.tableHeader.setCurrentCell(0,0)
        QtCore.QObject.connect(self.HeaderObj.ui.tableHeader,QtCore.SIGNAL("currentItemChanged(QTableWidgetItem *, QTableWidgetItem *)"), self.HeaderObj.naviState)
        self.assertEqual(self.HeaderObj.ui.btnUp.isEnabled(), False)
        self.assertEqual(self.HeaderObj.ui.btnDown.isEnabled(), True)
        
        # if the current row is in the midle
        self.HeaderObj.ui.tableHeader.setCurrentCell(1,0)
        self.HeaderObj.ui.btnUp.setEnabled(True)
        QtCore.QObject.connect(self.HeaderObj.ui.tableHeader,QtCore.SIGNAL("currentItemChanged(QTableWidgetItem *, QTableWidgetItem *)"), self.HeaderObj.naviState)
        self.assertEqual(self.HeaderObj.ui.btnUp.isEnabled(), True)
        self.assertEqual(self.HeaderObj.ui.btnDown.isEnabled(), True)
        
         # if the current row is at last
        self.HeaderObj.ui.tableHeader.setCurrentCell(self.HeaderObj.ui.tableHeader.rowCount()-1,0)
        self.HeaderObj.ui.btnDown.setEnabled(False)
        QtCore.QObject.connect(self.HeaderObj.ui.tableHeader,QtCore.SIGNAL("currentItemChanged(QTableWidgetItem *, QTableWidgetItem *)"), self.HeaderObj.naviState)
        self.assertEqual(self.HeaderObj.ui.btnUp.isEnabled(), True)
        self.assertEqual(self.HeaderObj.ui.btnDown.isEnabled(), False)
        
    def testAddItemToTable(self):
        headerDic = {'a':"da", 'c':"ka", 'e': 'la', 'e':'ta'}
        self.HeaderObj.addItemToTable(headerDic)
        self.assertEqual(self.HeaderObj.ui.tableHeader.rowCount(), len(headerDic))
        
    def testDeleteRow(self):
        table = self.HeaderObj.ui.tableHeader
        self.HeaderObj.deleteRow()
        self.assertEqual(table.rowCount(), 9)
        
    def testInsertNewRow(self):
        self.HeaderObj.insertNewRow()
        self.assertEqual(self.HeaderObj.ui.tableHeader.rowCount(), 11)
        
    def testMoveUp(self):
        headerDic = {'a':"da", 'c':"ka", 'e': 'la', 'e':'ta'}
        self.HeaderObj.addItemToTable(headerDic)
        self.HeaderObj.moveUp()
        self.assertEqual(self.HeaderObj.ui.tableHeader.currentRow(), 0)
        
    def testMoveDown(self):
        headerDic = {'a':"da", 'c':"ka", 'e': 'la', 'e':'ta'}
        self.HeaderObj.addItemToTable(headerDic)
        self.HeaderObj.moveDown()
        self.assertEqual(self.HeaderObj.ui.tableHeader.currentRow(), 2)
    
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    unittest.main()
