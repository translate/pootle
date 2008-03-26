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
# This module is working on Find string in files of source and target


from PyQt4 import QtCore, QtGui
from pootling.ui.Ui_FindInCatalog import Ui_frmFind
import pootling.modules.World as World

class FindInCatalog(QtGui.QDockWidget):

    def __init__(self, parent):
        QtGui.QDockWidget.__init__(self, parent)
        self.setObjectName("findDock")
        self.form = QtGui.QWidget(self)
        self.ui = Ui_frmFind()
        self.ui.setupUi(self.form)
        self.setWidget(self.form)
        self.setWindowTitle(self.tr("Find In Catalog"))
        action = self.toggleViewAction()
        action.setText("&Find String")
        action.setStatusTip("Toggle Find In Catalog")
        self.setFeatures(QtGui.QDockWidget.DockWidgetClosable)
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.connect(self.ui.find, QtCore.SIGNAL("clicked()"), self.findNext)
        self.connect(self.ui.lineEdit, QtCore.SIGNAL("textChanged(QString)"), self.setColorStatus)
        self.setVisible(self.isHidden())
        self.possible = True
        
        self.defaultBase = False

    def showFind(self):
        if (self.possible):
            self.setVisible(self.isHidden())
            self.setWindowTitle(self.tr("Find In Catalog"))
            self.ui.lineEdit.setFocus()
            self.possible = False
        else:
            self.hide()
            self.possible = True
            self.emit(QtCore.SIGNAL("returnSignal"))
        self.ui.lineEdit.setFocus()

    def keyReleaseEvent(self, event):
        """
        A subclass for keyReleaseEvent.
        """
        # press Enter key to open the file.
        if (event.key() == 16777220):
            self.findNext()

    def findNext(self):
        """
        Start the search process, if possible
        manage the UI elements for search
        @signal findNext.
        """
        searchOptions = 0
        if (self.ui.chbsource.isChecked()):
            searchOptions |= World.source
        if (self.ui.chbtarget.isChecked()):
            searchOptions |= World.target

        if (searchOptions):
            self.setToolTip("")
            self.setStatusTip("")
            self.ui.lineEdit.setFocus()
            self.ui.lineEdit.setWhatsThis("Here you can enter the text you want to search for!")
            searchString = unicode(self.ui.lineEdit.text())
            self.emit(QtCore.SIGNAL("findNext"), searchString, searchOptions)
        else:
            msg = QtCore.QString(self.tr("Please select first of source or target checkbox or both of them!"))
            self.setToolTip(msg)
            self.setStatusTip(msg)

    def closeEvent(self, event):
        """
        @param QCloseEvent Object: received close event when closing widget
        """
        QtGui.QDockWidget.closeEvent(self, event)
        self.emit(QtCore.SIGNAL("returnSignal"))

    def setColorStatus(self, message):
        """
        colorize the search text box; yellow for reached end, red for not found.
        """
        
        if (message == "notFound"):
            color = QtGui.QColor(255, 85, 85)
            palette = self.ui.lineEdit.palette()
            palette.setColor(QtGui.QPalette.Active, QtGui.QPalette.Base, color)
            self.ui.lineEdit.update()
            self.defaultBase = False
        
        elif (message) and (not self.defaultBase):
            color = QtGui.QColor(255, 255, 255)
            palette = self.ui.lineEdit.palette()
            palette.setColor(QtGui.QPalette.Active, QtGui.QPalette.Base, color)
            self.ui.lineEdit.update()
            self.defaultBase = True


if __name__ == "__main__":
    import sys, os
    # set the path for QT in order to FindInCatalog
    QtCore.QDir.setCurrent(os.path.join(sys.path[0], "..", "ui"))
    app = QtGui.QApplication(sys.argv)
    Form = FindInCatalog(None)
    Form.show()
    sys.exit(app.exec_())
