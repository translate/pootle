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
#This module is working on the display of TM in a table

from PyQt4 import QtCore, QtGui
from pootling.ui.Ui_TableTM import Ui_Form
import sys, os
import pootling.modules.World as World


class tableTM(QtGui.QDockWidget):
    """
    This class works with the display of translation memory in a table
    
    @signal itemDoubleClicked(QTableWidgetItem *): emitted when doubled clicking on tableWidgetItem
    @signal translation2target: emitted with target as string when itemDoubleClicked(QTableWidgetItem *) is emitted.
    @signal openFile: emitted with filename together with the findUnit signal
    @signal findUnit: emitted with the current source.
    @signal visible: emitted with the bool value to toggleViewAction
    
    """
    def __init__(self, parent):
        QtGui.QDockWidget.__init__(self, parent)
        self.setObjectName("miscDock")
        self.setWindowTitle(self.tr("TM Lookup"))
        self.form = QtGui.QWidget(self)
        self.ui = Ui_Form()
        self.ui.setupUi(self.form)
        self.setWidget(self.form)
        self.ui.tblTM.setEnabled(False)
        self.headerLabels = [self.tr("Match"),self.tr("Source"), self.tr("Target")]
        self.ui.tblTM.setColumnCount(len(self.headerLabels))
        self.ui.tblTM.setHorizontalHeaderLabels(self.headerLabels)
        self.ui.tblTM.horizontalHeader().resizeSection(0, 60)
        self.ui.tblTM.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.Interactive)
        self.ui.tblTM.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.Stretch)
        self.ui.tblTM.verticalHeader().hide()
        self.ui.tblTM.resizeRowsToContents()
        self.ui.tblTM.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.ui.tblTM.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.normalState = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        self.ui.tblTM.selectRow(0)
        self.infoIcon = QtGui.QIcon("../images/TM_info.png")
        
        self.connect(self.ui.tblTM, QtCore.SIGNAL("itemDoubleClicked(QTableWidgetItem *)"), self.emitTarget)
        self.createContextMenu()
        self.allowUpdate = True
        self.applySettings()
        
    def applySettings(self):
        """
        set color and font to the TM table.
        """
        TMColor = World.settings.value("TMColor")
        if (TMColor.isValid()):
            colorObj = QtGui.QColor(TMColor.toString())
            palette = self.ui.tblTM.palette()
            palette.setColor(QtGui.QPalette.Active, QtGui.QPalette.ColorRole(QtGui.QPalette.Text), colorObj)
            palette.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.ColorRole(QtGui.QPalette.Text), colorObj)
            self.ui.tblTM.setPalette(palette)

        font = World.settings.value("TMFont")
        if (font.isValid()):
            fontObj = QtGui.QFont()
            if (fontObj.fromString(font.toString())):
              self.ui.tblTM.setFont(fontObj)
              
        self.ui.tblTM.resizeRowsToContents()
        
    def createContextMenu(self):
        """
        context menu of items
        """
        self.menu = QtGui.QMenu()
        actionCopyResult = self.menu.addAction(QtGui.QIcon("../images/source.png"), self.tr("Copy Translation To Target"))
        actionEditFile = self.menu.addAction(QtGui.QIcon("../images/open.png"),self.tr("Edit File"))
        self.connect(actionCopyResult, QtCore.SIGNAL("triggered()"), self.emitTarget)
        self.connect(actionEditFile, QtCore.SIGNAL("triggered()"), self.emitOpenFile)
        
    def contextMenuEvent(self, e):
        self.menu.exec_(e.globalPos())
        
    def fillTable(self, candidates):
        """
        Fill table with candidates source and target.
        
        @param candidates: list of unit.
        """
        if (not self.allowUpdate):
            self.allowUpdate = True
            return
        if (not self.isVisible()):
            return
            
        if (not candidates):
            return
        self.newUnit()
        for unit in candidates:
            row = self.ui.tblTM.rowCount()
            self.ui.tblTM.setRowCount(row + 1)
            
            match = (unit.getnotes("translator"))[:-1]
            try:
                match = int(match)
                match = (str(match) + "%").rjust(4)
            except ValueError:
                match = ""
            item = QtGui.QTableWidgetItem(match)
            item.setData(QtCore.Qt.UserRole, QtCore.QVariant(unit.filepath))
            item.setFlags(self.normalState)
            item.setTextAlignment(QtCore.Qt.AlignRight + QtCore.Qt.AlignVCenter)
            self.ui.tblTM.setItem(row, 0, item)
            
            source = self.shorten(unit.source)
            item = QtGui.QTableWidgetItem(source)
            item.setData(QtCore.Qt.UserRole, QtCore.QVariant(unit.source))
            item.setFlags(self.normalState)
            self.ui.tblTM.setItem(row, 1, item)
            
            target = self.shorten(unit.target)
            item = QtGui.QTableWidgetItem(target)
            item.setData(QtCore.Qt.UserRole, QtCore.QVariant(unit.target))
            item.setFlags(self.normalState)
            self.ui.tblTM.setItem(row, 2, item)
            tooltips = "<h5>Found in: </h5>" + unit.filepath + "<h5> Translator: </h5>" + unit.translator + "<h5> Date: </h5>" + unit.date
            self.setToolTip(row, 0, tooltips, self.infoIcon)
            self.setToolTip(row, 1, unit.source )
            self.setToolTip(row, 2, unit.target)
            
        self.ui.tblTM.setSortingEnabled(True)
        self.ui.tblTM.horizontalHeader().setSortIndicatorShown(False)
        self.ui.tblTM.sortItems(0, QtCore.Qt.DescendingOrder)
        self.ui.tblTM.resizeRowsToContents()
        self.show()
        self.createContextMenu()
        self.ui.tblTM.setCurrentCell(0,0)
    
    def emitTarget(self):
        """
        Send "targetChanged" signal with target as string.
        """
        # don't allow fill table since the unit's target is same from here.
        self.allowUpdate = False
        row = self.ui.tblTM.currentRow()
        item = self.ui.tblTM.item(row, 2)
        if (item):
            target = item.data(QtCore.Qt.UserRole).toString()
            self.emit(QtCore.SIGNAL("translation2target"), unicode(target))
    
    def emitOpenFile(self):
        """
        Send "openFile" signal with filename together with the findUnit signal
        with the current source.
        """
        row = self.ui.tblTM.currentRow()
        item = self.ui.tblTM.item(row, 0)
        itemSource = self.ui.tblTM.item(row, 1)
        source = None
        if (item and itemSource):
            source = unicode(itemSource.data(QtCore.Qt.UserRole).toString())
            filepath = unicode(item.data(QtCore.Qt.UserRole).toString())
            self.emit(QtCore.SIGNAL("openFile"), filepath)
            self.emit(QtCore.SIGNAL("findUnit"), source)
        
    def setToolTip(self, index = None, col = 0, tooltips = "", icon = QtGui.QIcon()):
        """
        mark icon indicate unit has more info and add tooltips.
        
        @param index: row in table.
        @param col: column to set tooltips.
        @param tooltips: more info about candidates such as which file the 
            candidate locates, who is the translator and when.
        @param icon: icon to set to col.
        """
        # get the current row
        if (not index):
            item = self.ui.tblTM.item(0, col)
        else:
            item = self.ui.tblTM.item(index, col)
        
        if (not item):
            return
        if (tooltips):
            item.setIcon(icon)
            item.setToolTip(unicode(tooltips))

    def closeEvent(self, event):
        """
        Unchecked the TM Lookup view action.
        
        @param QCloseEvent Object: received close event when closing widget
        """
        QtGui.QDockWidget.closeEvent(self, event)
        self.toggleViewAction().setChecked(False)
        self.emit(QtCore.SIGNAL("visible"), False)
        
    def showEvent(self, event):
        """
        Checked the TM Lookup view action.
        
        @param QShowEvent Object: received show event when showing widget
        """
        QtGui.QDockWidget.showEvent(self, event)
        self.toggleViewAction().setChecked(True)
        self.emit(QtCore.SIGNAL("visible"), True)
    
    def newUnit(self):
        """
        Clear table to be filled by a new unit.
        """
        if (not self.allowUpdate):
            return
        self.ui.tblTM.setEnabled(True)
        self.ui.tblTM.clear()
        self.ui.tblTM.setHorizontalHeaderLabels(self.headerLabels)
        self.ui.tblTM.setSortingEnabled(False)
        self.ui.tblTM.setRowCount(0)
    
    def shorten(self, text):
        """
        Return the first part of text, seperated by new line and filled with three dots.
        """
        line = text.find("\n")
        if (line >= 0):
            text = text[:line] + "..."
        return text

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    table = tableTM(None)
    table.show()
    sys.exit(app.exec_())

