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
#This module is working on the display of TM in a talbe

from PyQt4 import QtCore, QtGui
from pootling.ui.Ui_TableGlossary import Ui_Form
import sys, os
import pootling.modules.World as World


class TableGlossary(QtGui.QDockWidget):
    def __init__(self, parent):
        QtGui.QDockWidget.__init__(self, parent)
        self.setObjectName("glossaryDock")
        self.setWindowTitle(self.tr("Glossary Lookup"))
        self.form = QtGui.QWidget(self)
        self.ui = Ui_Form()
        self.ui.setupUi(self.form)
        self.setWidget(self.form)
        self.ui.tblGlossary.setEnabled(False)
        self.headerLabels = [self.tr("Term"),self.tr("Definition")]
        self.ui.tblGlossary.setColumnCount(len(self.headerLabels))
        self.ui.tblGlossary.setHorizontalHeaderLabels(self.headerLabels)
        for i in range(len(self.headerLabels)):
            self.ui.tblGlossary.resizeColumnToContents(i)
            self.ui.tblGlossary.horizontalHeader().setResizeMode(i, QtGui.QHeaderView.Stretch)
        self.ui.tblGlossary.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.ui.tblGlossary.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.normalState = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        self.toggleViewAction().setChecked(True)
        self.ui.tblGlossary.resizeRowsToContents()
        self.same = False
        self.applySettings()
        
    def applySettings(self):
        """
        set color and font to the TM table.
        """
        glossaryColor = World.settings.value("glossaryColor")
        if (glossaryColor.isValid()):
            colorObj = QtGui.QColor(glossaryColor.toString())
            palette = self.ui.tblGlossary.palette()
            palette.setColor(QtGui.QPalette.Active, QtGui.QPalette.ColorRole(QtGui.QPalette.Text), colorObj)
            palette.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.ColorRole(QtGui.QPalette.Text), colorObj)
            self.ui.tblGlossary.setPalette(palette)

        font = World.settings.value("glossaryFont")
        if (font.isValid()):
            fontObj = QtGui.QFont()
            if (fontObj.fromString(font.toString())):
              self.ui.tblGlossary.setFont(fontObj)
              
        self.ui.tblGlossary.resizeRowsToContents()

    def newUnit(self):
        self.ui.tblGlossary.clear()
        self.ui.tblGlossary.setEnabled(True)
        self.ui.tblGlossary.setHorizontalHeaderLabels(self.headerLabels)
        self.ui.tblGlossary.setRowCount(0)
                
    def fillTable(self, candidates):
        """
        fill each found unit into table
        @param candidates:list of pofile object
        """
        row = self.ui.tblGlossary.rowCount()
        table = self.ui.tblGlossary
        if (not candidates):
            return
        for unit in candidates:
            for r in range(row):
                if (table.item(r,0).text() ==  unit.source):
                    self.same = True
                    break
            if self.same:
                self.same = False
                continue
            row = self.ui.tblGlossary.rowCount()
            table.setRowCount(row + 1)
            item = QtGui.QTableWidgetItem(unit.source)
            item.setFlags(self.normalState)
            table.setItem(row, 0, item)
            
            item = QtGui.QTableWidgetItem(unit.target)
            item.setFlags(self.normalState)
            table.setItem(row, 1, item)

    def closeEvent(self, event):
        """
        Unchecked the Glossary view action.
        @param QCloseEvent Object: received close event when closing widget
        """
        QtGui.QDockWidget.closeEvent(self, event)
        self.toggleViewAction().setChecked(False)
        self.emit(QtCore.SIGNAL("closed"))
        
    def showEvent(self, event):
        """
        Checked the Glossary view action.
        @param QShowEvent Object: received show event when showing widget
        """
        QtGui.QDockWidget.showEvent(self, event)
        self.toggleViewAction().setChecked(True)
        self.emit(QtCore.SIGNAL("shown"))
        
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    table = TableGlossary(None)
    table.show()
    sys.exit(table.exec_())

