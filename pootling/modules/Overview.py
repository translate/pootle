#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#Copyright (c) 2006 - 2007 by The WordForge Foundation
#                    www.wordforge.org
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
# This module is working on overview of source and target

from PyQt4 import QtCore, QtGui
from pootling.ui.Ui_Overview import Ui_Form
import pootling.modules.World as World

class OverviewDock(QtGui.QDockWidget):
    def __init__(self, parent):
        QtGui.QDockWidget.__init__(self, parent)
        self.setObjectName("overviewDock")
        self.setWindowTitle(self.tr("Overview"))
        self.form = QtGui.QWidget(self)
        self.ui = Ui_Form()
        self.ui.setupUi(self.form)
        self.setWidget(self.form)
        
        # set up table appearance and behavior
        self.viewSetting()
        self.ui.tableOverview.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.ui.tableOverview.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.ui.tableOverview.horizontalHeader().setSortIndicatorShown(True)
        self.ui.tableOverview.resizeColumnToContents(0)
        self.ui.tableOverview.resizeColumnToContents(3)
        self.ui.tableOverview.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.Stretch)
        self.ui.tableOverview.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.Stretch)
        self.ui.tableOverview.horizontalHeader().setHighlightSections(False)
        self.ui.tableOverview.verticalHeader().hide()
        self.applySettings()
        
        self.fuzzyColor = QtGui.QColor(246, 238, 156, 140)
        self.blankColor = QtGui.QColor(255, 255, 255, 0)
        
        self.fuzzyIcon = QtGui.QIcon("../images/fuzzy.png")
        self.noteIcon = QtGui.QIcon("../images/note.png")
        self.approvedIcon = QtGui.QIcon("../images/approved.png")
        self.pluralIcon = QtGui.QIcon("../images/plural.png")
        self.pluralFuzzyIcon = QtGui.QIcon("../images/pluralfuzzy.png")
        self.blankIcon = QtGui.QIcon()
        self.normalState = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        self.indexMaxLen = 0
        self.units = []
        self.visibleRow = []
        self.filter = None
        
        self.changedSignal = QtCore.SIGNAL("currentCellChanged(int, int, int, int)")
        self.connect(self.ui.tableOverview, self.changedSignal, self.emitCurrentIndex)
        self.connect(self.ui.tableOverview.model(), QtCore.SIGNAL("layoutChanged()"), self.showFilteredItems)
        self.connect(self.ui.tableOverview, QtCore.SIGNAL("cellDoubleClicked(int, int)"), self.fillTarget)
        
        self.ui.tableOverview.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        if (obj == self.ui.tableOverview):
            if (event.type() == QtCore.QEvent.ContextMenu):
                """
                Request a translation for unit's source.
                """
                self.tableContextMenu(event)
                return True
            elif (event.type() == QtCore.QEvent.FocusIn):
                """
                Check to see if target has modified, item focus out
                and table widget focus in.
                """
                self.emitTargetChanged()
                return False
            else:
                return False
        else:
            return self.eventFilter(obj, event)
    
    def tableContextMenu(self, event):
        """
        Save the position of mouse, and emit "requestUnit" signal.
        """
        self.globalPos = event.globalPos()
        self.emit(QtCore.SIGNAL("requestUnit"))
    
    def popupTranslation(self, candidates):
        """
        Popup menu of translation.
        """
        menu = QtGui.QMenu()
        if (not candidates):
            menuAction = menu.addAction(self.tr("(no translation)"))
            menu.exec_(self.globalPos)
            return
        
        for candidate in candidates:
            strCopy = unicode(self.tr("Copy \"%s\" to target.")) % unicode(candidate.target)
            menuAction = menu.addAction(strCopy)
            menuAction.setData(QtCore.QVariant(candidate.target))
            self.connect(menuAction, QtCore.SIGNAL("triggered()"), self.copyToTarget)
        menu.exec_(self.globalPos)
        self.disconnect(menuAction, QtCore.SIGNAL("triggered()"), self.copyToTarget)
    
    def copyToTarget(self):
        """
        emit "targetChanged" signal with self.sender().text().
        """
        text = self.sender().data().toString()
        self.emit(QtCore.SIGNAL("targetChanged"), unicode(text))
    
    def closeEvent(self, event):
        """
        set text of action object to 'show Overview' before closing Overview
        @param QCloseEvent Object: received close event when closing widget
        """
        QtGui.QDockWidget.closeEvent(self, event)
        self.toggleViewAction().setChecked(False)
        
    def slotNewUnits(self, units):
        """
        set the filter to filterAll, fill the table with units.
        @param units: list of unit class.
        """
        self.targetBeforeEdit = None
        self.viewSetting(units)
        if (not units):
            self.emitFirstLastUnit()
            return
        self.indexMaxLen = len(str(len(units)))
        self.filter = World.filterAll
        self.units = units
        self.ui.tableOverview.setSortingEnabled(False)
        
        self.setUpdatesEnabled(False)
        oldValue = None
        lenUnit = len(units)
        i = 0.0
        for unit in units:
            if (self.filter & unit.x_editor_state):
                self.addUnit(unit)
            i += 1
            value = int((i / lenUnit) * 100)
            # emit signal when only percentage changed
            if (oldValue != value):
                self.emit(QtCore.SIGNAL("progressBarValue"), value)
                oldValue = value
        self.ui.tableOverview.setSortingEnabled(True)
        self.ui.tableOverview.sortItems(0)
        self.setUpdatesEnabled(True)
    
    def filterChanged(self, filter, lenFilter):
        """
        show the items which are in filter.
        @param filter: helper constants for filtering.
        @param lenFilter: len of filtered items.
        """
        if (filter == self.filter):
            return
        self.filter = filter
        self.showFilteredItems()
        
    def addUnit(self, unit):
        """
        add the unit to table.
        @param unit: unit class.
        """
        row = self.ui.tableOverview.rowCount()
        self.ui.tableOverview.setRowCount(row + 1)
        item = QtGui.QTableWidgetItem(self.indexString(row + 1))
        item.setTextAlignment(QtCore.Qt.AlignRight + QtCore.Qt.AlignVCenter)
        item.setFlags(self.normalState)
        item.setData(QtCore.Qt.UserRole, QtCore.QVariant(row))
        unit.x_editor_tableItem = item
        self.ui.tableOverview.setItem(row, 0, item)
        self.markComment(row, unit.getnotes())
        # source field
        source = unit.source
        line = source.find("\n")
        if (line >= 0):
            source = source[:line] + "..."
        item = QtGui.QTableWidgetItem(source)
        item.setFlags(self.normalState)
        self.ui.tableOverview.setItem(row, 1, item)
        # target field
        target = unit.target or ""
        line = target.find("\n")
        if (line >= 0):
            target = target[:line] + "..."
        item = QtGui.QTableWidgetItem(target)
        self.ui.tableOverview.setItem(row, 2, item)
        # note field
        item = QtGui.QTableWidgetItem()
        item.setFlags(self.normalState)
        self.ui.tableOverview.setItem(row, 3, item)
        self.markState(row, unit.x_editor_state)
    
    def emitCurrentIndex(self, row, col, preRow, preCol):
        """
        emit filteredIndex signal with selected unit's index.
        """
        # do not emit signal when select the same row.
        if (row == preRow):
            return
        # emit the index of current unit.
        item = self.ui.tableOverview.item(row, 0)
        if (hasattr(item, "data")):
            index = item.data(QtCore.Qt.UserRole).toInt()[0]
            self.emit(QtCore.SIGNAL("filteredIndex"), index)
        
    def emitTargetChanged(self):
        """
        emit targetChanged signal if target column has changed.
        """
        targetItem = self.ui.tableOverview.item(self.ui.tableOverview.currentRow(), 2)
        if (not hasattr(targetItem, "text")):
            return
        targetAfterEdit = targetItem.text()
        if (targetAfterEdit != self.targetBeforeEdit) and (self.targetBeforeEdit != None):
            # target has changed
            target = unicode(targetAfterEdit)
            if (self.unit and self.unit.hasplural()):
                # change only the first string of plural
                string0 = target
                target = []
                for string in self.unit.target.strings:
                    target.append(string)
                target[0] = string0
                
            self.emit(QtCore.SIGNAL("targetChanged"), target)
            if (self.unit):
                self.updateText(self.unit.target or "")
    
    def fillTarget(self, row, column):
        """
        Fill current item row #2 with self.unit.target.
        This call when user double click on target field to edit.
        """
        targetItem = self.ui.tableOverview.item(self.ui.tableOverview.currentRow(), 2)
        # unmark item fuzzy when text changed
        row = self.ui.tableOverview.row(targetItem)
        if (targetItem and self.unit):
            self.targetBeforeEdit = self.unit.target
            targetItem.setText(self.targetBeforeEdit)
    
    def updateText(self, text, plural = 0):
        """
        Set text to current item.
        @param text: text to set in target column.
        @param plural: bool to indicate a current text need to update.
        """
        if (plural) or (not self.unit):
            # do not update plural strings.
            return
        targetItem = self.ui.tableOverview.item(self.ui.tableOverview.currentRow(), 2)
        # unmark item fuzzy when text changed
        row = self.ui.tableOverview.row(targetItem)
        self.unit.x_editor_state &= ~World.fuzzy
        self.markState(row, self.unit.x_editor_state)
        if (targetItem) and (not self.ui.tableOverview.isRowHidden(row)):
            # shorten text for display only.
            line = text.find("\n")
            if (line >= 0):
                text = text[:line] + "..."
            targetItem.setText(text)
    
    def updateView(self, unit):
        """
        highlight the table's row, mark comment icon, mark state icon,
        and set the target text according to unit.
        @param unit: unit class
        """
        if (not unit) or (not hasattr(unit, "x_editor_tableItem")):
            self.unit = None
            return
        self.targetBeforeEdit = None
        self.unit = unit
        row = self.ui.tableOverview.row(unit.x_editor_tableItem)
        unit.x_editor_row = self.visibleRow.index(row)
        targetItem = self.ui.tableOverview.item(row, 2)
        
        # update target column only if text has changed.
        if (targetItem.text() != unit.target):
            target = self.shorten(unit.target or "")
            targetItem.setText(target)
        
        self.markComment(row, unit.getnotes())
        self.markState(row, unit.x_editor_state)
        
        self.disconnect(self.ui.tableOverview, self.changedSignal, self.emitCurrentIndex)
        self.ui.tableOverview.selectRow(row)
        self.connect(self.ui.tableOverview, self.changedSignal, self.emitCurrentIndex)
        
        self.ui.tableOverview.scrollToItem(unit.x_editor_tableItem)
        self.emitFirstLastUnit()
    
    def markState(self, index, state):
        """
        mark icon indicate state of unit on note column.
        @param index: row in table.
        @param state: unit's state.
        """
        item = self.ui.tableOverview.item(index, 3)
        if (not item):
            return
        
        if (state & World.fuzzy):
            if (state & World.plural):
                item.setIcon(self.pluralFuzzyIcon)
                item.setToolTip("Plural string is fuzzy")
            else:
                item.setIcon(self.fuzzyIcon)
                item.setToolTip("String is fuzzy")
            self.ui.tableOverview.item(index, 0).setBackgroundColor(self.fuzzyColor)
            self.ui.tableOverview.item(index, 1).setBackgroundColor(self.fuzzyColor)
            self.ui.tableOverview.item(index, 2).setBackgroundColor(self.fuzzyColor)
            item.setBackgroundColor(self.fuzzyColor)
        
        else:
            # TODO: do not setBackgroundColor when item is not dirty yet.
            if (state & World.plural):
                item.setIcon(self.pluralIcon)
                item.setToolTip("Plural strings")
            else:
                item.setIcon(self.blankIcon)
                item.setToolTip("")
            self.ui.tableOverview.item(index, 0).setBackgroundColor(self.blankColor)
            self.ui.tableOverview.item(index, 1).setBackgroundColor(self.blankColor)
            self.ui.tableOverview.item(index, 2).setBackgroundColor(self.blankColor)
            item.setBackgroundColor(self.blankColor)
    
    def applySettings(self):
        """
        set color and font to the table.
        """
        overviewColor = World.settings.value("overviewColor")
        if (overviewColor.isValid()):
            colorObj = QtGui.QColor(overviewColor.toString())
            palette = self.ui.tableOverview.palette()
            palette.setColor(QtGui.QPalette.Active, QtGui.QPalette.ColorRole(QtGui.QPalette.Text), colorObj)
            palette.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.ColorRole(QtGui.QPalette.Text), colorObj)
            self.ui.tableOverview.setPalette(palette)

        font = World.settings.value("overviewFont")
        if (font.isValid()):
            fontObj = QtGui.QFont()
            if (fontObj.fromString(font.toString())):
              self.ui.tableOverview.setFont(fontObj)
              
        font = World.settings.value("overviewHeaderFont")
        if (font.isValid()):
            fontObj = QtGui.QFont()
            if (fontObj.fromString(font.toString())):
              self.ui.tableOverview.horizontalHeader().setFont(fontObj)
              
        self.ui.tableOverview.resizeRowsToContents()
        
    def showFilteredItems(self):
        """
        hide and show the item in the table according to filter.
        calculating the visibleRow for navigation.
        """
        self.setUpdatesEnabled(False)
        i = 0
        self.visibleRow = []
        for unit in self.units:
            if hasattr(unit, "x_editor_tableItem"):
                item = unit.x_editor_tableItem
                row = self.ui.tableOverview.row(item)
                if (unit.x_editor_state & self.filter):
                    self.ui.tableOverview.showRow(row)
                    self.visibleRow.append(row)
                    item.setData(QtCore.Qt.UserRole, QtCore.QVariant(i))
                    i += 1
                else:
                    self.ui.tableOverview.hideRow(row)
        self.setUpdatesEnabled(True)
        self.ui.tableOverview.repaint()
        self.visibleRow.sort()
        self.emitFirstLastUnit()
    
    def indexString(self, index):
        """converting index which is integer string."""
        return str(index).rjust(self.indexMaxLen) + "  "
    
    def markComment(self, index = None, note = ""):
        """
        mark icon indicate unit has comment on index column, and add tooltips.
        @param index: row in table.
        @param note: unit's comment as tooltips in index column.
        """
        if (type(index) != int):
            note = index
            index = None
            
        # get the current row
        if (not index):
            item = self.ui.tableOverview.item(self.ui.tableOverview.currentRow(), 0)
        else:
            item = self.ui.tableOverview.item(index, 0)
        
        if (not item):
            return
        if (note):
            item.setIcon(self.noteIcon)
            item.setToolTip(unicode(note))
        else:
            item.setIcon(self.blankIcon)
            item.setToolTip("")
    
    def scrollPrevious(self):
        """move to previous row inside the table."""
        currentRow = self.ui.tableOverview.currentRow()
        currentIndex = self.visibleRow.index(currentRow)
        preRow = self.visibleRow[currentIndex - 1]
        self.ui.tableOverview.selectRow(preRow)
    
    def scrollNext(self):
        """move to next row inside the table."""
        currentRow = self.ui.tableOverview.currentRow()
        currentIndex = self.visibleRow.index(currentRow)
        nextRow = self.visibleRow[currentIndex + 1]
        self.ui.tableOverview.selectRow(nextRow)
    
    def scrollFirst(self):
        """move to first row of the table."""
        self.ui.tableOverview.selectRow(0)
    
    def scrollLast(self):
        """move to last row of the table."""
        self.ui.tableOverview.selectRow(self.visibleRow[-1])
    
    def scrollToRow(self, value):
        """move to row number specified by value.
        @param value: row number."""
        if (len(self.visibleRow) > 0):
            nextRow = self.visibleRow[value]
            self.ui.tableOverview.selectRow(nextRow)
    
    def emitFirstLastUnit(self):
        currentRow = self.ui.tableOverview.currentRow()
        lenSelItem = len(self.ui.tableOverview.selectedItems())
        firstUnit = (lenSelItem == 0) or (currentRow == self.visibleRow[0])
        lastUnit = (lenSelItem == 0) or (currentRow == self.visibleRow[-1])
        self.emit(QtCore.SIGNAL("toggleFirstLastUnit"), firstUnit, lastUnit)
    
    def gotoRow(self, value):
        item = self.ui.tableOverview.findItems(self.indexString(value), QtCore.Qt.MatchExactly)
        if (len(item) > 0):
            row = self.ui.tableOverview.row(item[0])
            if (not self.ui.tableOverview.isRowHidden(row)):
                self.ui.tableOverview.selectRow(row)
    
    def getCurrentIndex(self):
        """
        return the current (selected) unit index.
        """
        row = self.ui.tableOverview.currentRow()
        item = self.ui.tableOverview.item(row, 0)
        return int(item.text())
    
    def viewSetting(self, argc = None):
        bool = (argc and True or False)
        self.ui.tableOverview.clear()
        self.headerLabels = [self.tr("Index"), self.tr("Source"), self.tr("Target"), self.tr("Status")]
        self.ui.tableOverview.setColumnCount(len(self.headerLabels))
        self.ui.tableOverview.setHorizontalHeaderLabels(self.headerLabels)
        self.ui.tableOverview.setRowCount(0)
        self.ui.tableOverview.setEnabled(bool)
    
    def shorten(self, text):
        """
        Cut the text which has more than one line and append with three dots.
        """
        line = text.find("\n") 
        if (line >= 0):
            text = text[:line] + "..."
        return text
    
if __name__ == "__main__":
    import sys, os
    # set the path for QT in order to find the icons
    QtCore.QDir.setCurrent(os.path.join(sys.path[0], "..", "ui"))
    app = QtGui.QApplication(sys.argv)
    overview = OverviewDock(None)
    overview.show()
    sys.exit(app.exec_())
