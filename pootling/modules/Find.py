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
# This module is working on source and target of current TU.

from PyQt4 import QtCore, QtGui
from pootling.ui.Ui_Find import Ui_frmFind
import pootling.modules.World as World

class Find(QtGui.QDockWidget):
    """
    Code for Find and Replace dock
    
    @signal initSearch(QString, list, bool): emitted when starting to search a nex text.
    @signal searchNext(): emitted when searching the text in next.
    @signal searchPrevious(): emitted when searching the text in previous.
    @signal replace(QString): emitted when replacing a text with a new text
    @signal replaceAll(QString): emitted when replacing all.
    """
    def __init__(self, parent):
        QtGui.QDockWidget.__init__(self, parent)
        self.setObjectName("findDock")
        self.form = QtGui.QWidget(self)
        self.ui = Ui_frmFind()
        self.ui.setupUi(self.form)
        self.setWidget(self.form)
        self.ui.insource.setEnabled(False)
        self.setWindowTitle(self.tr("Find and Replace"))
        self.toggleViewAction().setVisible(False)
        self.setFeatures(QtGui.QDockWidget.DockWidgetClosable)
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.connect(self.ui.findNext, QtCore.SIGNAL("clicked()"), self.findNext)
        self.connect(self.ui.findPrevious, QtCore.SIGNAL("clicked()"), self.findPrevious)
        self.connect(self.ui.replace, QtCore.SIGNAL("clicked()"), self.replace)
        self.connect(self.ui.replaceAll, QtCore.SIGNAL("clicked()"), self.replaceAll)
        self.connect(self.ui.insource, QtCore.SIGNAL("stateChanged(int)"), self.initSearch)
        self.connect(self.ui.intarget, QtCore.SIGNAL("stateChanged(int)"), self.initSearch)
        self.connect(self.ui.incomment, QtCore.SIGNAL("stateChanged(int)"), self.initSearch)
        self.connect(self.ui.matchcase, QtCore.SIGNAL("stateChanged(int)"), self.initSearch)
        self.connect(self.ui.lineEdit, QtCore.SIGNAL("textChanged(const QString &)"), self._textChanged)
        
        self.defaultBase = False

    def _textChanged(self, txt):
        """ private slot
        @param txt: new value in the widget """
        self.initSearch()
        self.findNext()

    def initSearch(self):
        """ start the search process, if possible
        manage the UI elements for search
        @signal initSearch """
        # create the filter
        filter = []
        if (self.ui.insource.isChecked()):
            filter.append(World.source)
        if (self.ui.intarget.isChecked()):
            filter.append(World.target)
        if (self.ui.incomment.isChecked()):
            filter.append(World.comment)
        
        if (filter):
            self.setToolTip("")
            self.setStatusTip("")
            self._enableSearch(True)
            self.ui.lineEdit.setFocus()
            searchString = self.ui.lineEdit.text()
            self.emit(QtCore.SIGNAL("initSearch"), searchString, filter, self.ui.matchcase.isChecked())
        else:
            msg = QtCore.QString(self.tr("Please select first where to search!"))
            self.setToolTip(msg)
            self.setStatusTip(msg)
            self._enableSearch(False)
        
        if (not self.defaultBase):
            self.defaultBase = True
            color = QtGui.QColor(255, 255, 255)
            palette = self.ui.lineEdit.palette()
            palette.setColor(QtGui.QPalette.Active, QtGui.QPalette.Base, color)
            self.ui.lineEdit.update()
        

    def _enableSearch(self, enabled):
        """ enable or disable the means to search 
        @param enabled: True or False"""
        self.ui.lineEdit.setEnabled(enabled)
        self.ui.findNext.setEnabled(enabled)
        self.ui.findPrevious.setEnabled(enabled)
        self.ui.lineEdit_2.setEnabled(enabled)
        self.ui.replace.setEnabled(enabled)
        self.ui.replaceAll.setEnabled(enabled)

    def showFind(self):
        if not ((self.isHidden() or not self.ui.lineEdit_2.isHidden())):
            self.hide()
        else:
            self.ui.insource.setEnabled(True)
            if ((not self.ui.intarget.isChecked()) and (not self.ui.incomment.isChecked())):
                self.ui.insource.setChecked(True)
            self.setWindowTitle(self.tr("Find"))
            self.initSearch()
            self._hideReplace(True)
            self.show()

    def showReplace(self):
        if not ((self.isHidden() or self.ui.lineEdit_2.isHidden())):
            self.hide()
        else:
            self.ui.insource.setChecked(False)
            self.ui.insource.setEnabled(False)
            if (not self.ui.incomment.isChecked()):
                self.ui.intarget.setChecked(True)
            self.setWindowTitle(self.tr("Find and Replace"))
            self.initSearch()
            self._hideReplace(False)
            self.show()

    def _hideReplace(self, hidden):
        """ hide or show the replace UI elements
        @param hidden: True or False """
        self.ui.lineEdit_2.setHidden(hidden)
        self.ui.lblReplace.setHidden(hidden)
        self.ui.replace.setHidden(hidden)
        self.ui.replaceAll.setHidden(hidden)

    def findNext(self):
        self.emit(QtCore.SIGNAL("searchNext"))
    
    def findPrevious(self):
        self.emit(QtCore.SIGNAL("searchPrevious"))
    
    def replace(self):
        self.emit(QtCore.SIGNAL("replace"), self.ui.lineEdit_2.text())
        self.ui.lineEdit_2.setFocus()
    
    def replaceAll(self):
        self.emit(QtCore.SIGNAL("replaceAll"), self.ui.lineEdit_2.text())
        self.ui.lineEdit_2.setFocus()
    
    def setColorStatus(self, message):
        """
        colorize the search text box; yellow for reached end, red for not found.
        """
        if (message == "reachedEnd"):
            color = QtGui.QColor(255, 255, 127)
            palette = self.ui.lineEdit.palette()
            palette.setColor(QtGui.QPalette.Active, QtGui.QPalette.Base, color)
            self.ui.lineEdit.update()
            self.defaultBase = False
            
        elif (message == "notFound"):
            color = QtGui.QColor(255, 85, 85)
            palette = self.ui.lineEdit.palette()
            palette.setColor(QtGui.QPalette.Active, QtGui.QPalette.Base, color)
            self.ui.lineEdit.update()
            self.defaultBase = False
        
        elif (message == "found") and (not self.defaultBase):
            color = QtGui.QColor(255, 255, 255)
            palette = self.ui.lineEdit.palette()
            palette.setColor(QtGui.QPalette.Active, QtGui.QPalette.Base, color)
            self.ui.lineEdit.update()
            self.defaultBase = True
        
    
if __name__ == "__main__":
    import sys, os
    # set the path for QT in order to find the icons
    QtCore.QDir.setCurrent(os.path.join(sys.path[0], "..", "ui"))
    app = QtGui.QApplication(sys.argv)
    Form = Find(None)
    Form.show()
    sys.exit(app.exec_())
