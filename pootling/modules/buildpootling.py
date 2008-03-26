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

from PyQt4 import QtCore, QtGui
import sys
from pootling.modules.MainEditor import MainWindow

class Pootling(QtGui.QApplication):
    """build Pootling back to any localized language."""
    def __init__(self):
        """ fsfa"""
        QtGui.QApplication.__init__(self,sys.argv)
        self.mainWindow = MainWindow()
        self.translator = QtCore.QTranslator()
        self.translator.load("pootling.qm", "/home/k-da/Documents/poxole/trunk/pootling")
        self.installTranslator(self.translator)
        print "already built"
        self.mainWindow.show()
        self.exec_()

if __name__ == "__main__":
    print "building..."
    P = Pootling()
    sys.exit(P.exec_())
