#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Pootling
# Copyright 2006 WordForge Foundation
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
# This module is providing an setting path of catalog dialog 

import sys, os
from PyQt4 import QtCore, QtGui
from pootling.ui.Ui_CatalogSetting import Ui_catPreferences
from pootling.modules import World
from pootling.modules import FileDialog

class CatalogSetting(QtGui.QDialog):
    """
    Code for setting path of catalog dialog
    """
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.ui = Ui_catPreferences()
        self.ui.setupUi(self)
#        self.setWindowTitle("Setting Catalog Manager")
        self.connect(self.ui.btnOk, QtCore.SIGNAL("clicked(bool)"), QtCore.SLOT("close()"))
        self.setModal(True)
        
        self.catalogModified = False
        self.catalogPath = []
        self.includeSub = False

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    tm = CatalogSetting(None)
    tm.show()
    sys.exit(tm.exec_())

