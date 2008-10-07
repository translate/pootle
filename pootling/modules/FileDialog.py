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
# This module is providing a selecting-file/folder dialog 

import sys, os
from PyQt4 import QtCore, QtGui

class fileDialog(QtGui.QDialog):
    """
    Code for choosing path of translation memory
    """
    def changeMode(self, path):
        """
        Change mode to allow dialog to accept file or directory.
        """
        if (os.path.isfile(path)) and (self.dialog.fileMode() != self.dialog.ExistingFiles):
            self.dialog.setFileMode(self.dialog.ExistingFiles)
        elif (os.path.isdir(path)) and (self.dialog.fileMode() != self.dialog.Directory):
            self.dialog.setFileMode(self.dialog.Directory)
    
    def getExistingPath(self, parent, directory, filter):
        self.dialog = QtGui.QFileDialog(parent, self.tr("Choose file or directory"))
        self.dialog.setDirectory(directory)
        
        if (not filter):
            self.dialog.setFilter("All files (*.*)")
        elif isinstance(filter, QtCore.QString) or isinstance(filter, str):
            self.dialog.setFilter(filter)
        elif isinstance(filter, list):
            filters = QtCore.QStringList(filter)
            self.dialog.setFilters(filters)
        
        self.dialog.setViewMode(self.dialog.List)
        self.dialog.setReadOnly(False)
        self.dialog.setAcceptMode(self.dialog.AcceptOpen)
        self.connect(self.dialog, QtCore.SIGNAL("currentChanged(QString)"), self.changeMode)
        self.dialog.setFileMode(self.dialog.ExistingFiles)
        if (self.dialog.exec_()):
            filenames = self.dialog.selectedFiles()
            return filenames
        return None
    
    def exec_(self):
        self.getExistingPath(self, "", "")
        sys.exit()
    
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    filedialog = fileDialog(None)
    sys.exit(filedialog.exec_())
    
