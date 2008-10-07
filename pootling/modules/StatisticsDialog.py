#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Pootling
# Copyright 2006 WordForge Foundation
#
# Version 0.1 (29 December 2006)
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
# This module is working on statistics files and folder as an dialog

from PyQt4 import QtCore, QtGui
from pootling.ui.Ui_StatisticsDialog import Ui_StatisticsDialog
import os


class StatisticDialog(QtGui.QDialog):
    """
    It will show all information of statistics files and folder

    """
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.ui = Ui_StatisticsDialog()
        self.ui.setupUi(self)
        self.setWindowTitle("Statistics")
        self.connect(self.ui.btnOk, QtCore.SIGNAL("clicked(bool)"), QtCore.SLOT("close()"))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    statis = StatisticDialog(None)
    statis.show()
    sys.exit(app.exec_())



