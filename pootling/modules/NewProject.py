#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2006 - 2007 by The WordForge Foundation
# www.wordforge.org
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
# This module is working on Project of Catatog File.


from PyQt4 import QtCore, QtGui
from pootling.ui.Ui_NewProject import Ui_NewProject
from pootling.modules import FileDialog
import translate.lang.data as data
import pootling.modules.World as World
import os

class newProject(QtGui.QDialog):
    """
    This module implementation with newProject, openProject and openrecentProject
    """
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.ui = Ui_NewProject()
        self.ui.setupUi(self)
        self.ui.entryName.setFocus()
        self.ui.btnOK.setEnabled(False)
        self.ui.lblprojecttype.hide()
        self.ui.comboProject.hide()
        self.fileExtension = ".ini"
        
        self.connect(self.ui.btnOK, QtCore.SIGNAL("clicked()"), self.accept)
        self.connect(self.ui.btnCancel, QtCore.SIGNAL("clicked()"), QtCore.SLOT("close()"))
        
        # call dialog box of FileDialog
        self.connect(self.ui.btnBrowse, QtCore.SIGNAL("clicked()"), self.getFilename)
        self.connect(self.ui.btnAdd, QtCore.SIGNAL("clicked()"), self.getFileOrDiretory)
        self.connect(self.ui.btnDelete, QtCore.SIGNAL("clicked()"), self.removeLocation)
        self.connect(self.ui.btnClear, QtCore.SIGNAL("clicked()"), self.clearLocation)
        self.connect(self.ui.btnMoveUp, QtCore.SIGNAL("clicked(bool)"), self.moveUp)
        self.connect(self.ui.btnMoveDown, QtCore.SIGNAL("clicked(bool)"), self.moveDown)
        
        # enable/diable ok button
        self.connect(self.ui.entryName, QtCore.SIGNAL("textChanged(QString)"), self.enableOkButton)
        self.connect(self.ui.entryPath, QtCore.SIGNAL("textChanged(QString)"), self.enableOkButton)
        
        # add item to project type
        self.ui.comboProject.addItem(self.tr("KDE"))
        self.ui.comboProject.addItem(self.tr("GNOME"))
        self.ui.comboProject.addItem(self.tr("Other"))
        
        # language code of the country
        language = []
        for langCode, langInfo in data.languages.iteritems():
            language.append(langInfo[0])
            language.sort()
        self.ui.comboLanguage.addItems(language)
        
        self.name = ""
        self.filename = ""
        self.lang = ""
        self.path = []
        self.includeSub = False
        
        self.modified = False
    
    def getFileOrDiretory(self):
        """
        Open the file dialog where you can choose both file and directory.
        Add path to Catalog list.
        """
        directory = World.settings.value("workingDir").toString()
        filenames = FileDialog.fileDialog().getExistingPath(
                self,
                directory,
                World.fileFilters)
        if (filenames):
            for filename in filenames:
                self.addLocation(filename)
            directory = os.path.dirname(unicode(filenames[0]))
            World.settings.setValue("workingDir", QtCore.QVariant(directory))
    
    def getFilename(self):
        directory = World.settings.value("workingDir").toString()
        filename = QtGui.QFileDialog.getSaveFileName(self,
                    self.tr("Save File As"),
                    directory,
                    self.tr("Ini file fomat (*.ini)"))
        if (filename):
            if (not filename.endsWith(".ini", QtCore.Qt.CaseInsensitive)):
                filename = filename + ".ini"
            self.ui.entryPath.setText(filename)
            
            directory = os.path.dirname(unicode(filename))
            World.settings.setValue("workingDir", QtCore.QVariant(directory))
    
    def addLocation(self, path):
        """
        Add path to location list.
        """
        items = self.ui.listLocation.findItems(path, QtCore.Qt.MatchCaseSensitive)
        if (not items):
            item = QtGui.QListWidgetItem(path)
            self.ui.listLocation.addItem(item)
    
    def clearLocation(self):
        """
        Clear all paths from location list, uncheck include sub combobox.
        """
        self.ui.listLocation.clear()
        self.ui.checkIncludeSub.setChecked(False)
    
    def removeLocation(self):
        """
        Remove the selected path from the location list.
        """
        self.ui.listLocation.takeItem(self.ui.listLocation.currentRow())
    
    def moveItem(self, distance):
        """
        Move an item up or down depending on distance
        
        @param distance: int
        """
        currentrow = self.ui.listLocation.currentRow()
        currentItem = self.ui.listLocation.item(currentrow)
        distanceItem = self.ui.listLocation.item(currentrow + distance)
        if (distanceItem and currentItem):
            temp = distanceItem.text()
            distanceItem.setText(currentItem.text())
            currentItem.setText(temp)
            self.ui.listLocation.setCurrentRow(currentrow + distance)
    
    def moveUp(self):
        """
        Move item up by 1 distance.
        """
        self.moveItem(-1)
    
    def moveDown(self):
        """
        Move item down by 1 distance
        """
        self.moveItem(1)
    
    def accept(self):
        """
        Save and open new project, or emit project's properties depend on
        show mode.
        """
        pathModified = False
        if (self.name != self.ui.entryName.text()):
            self.name = self.ui.entryName.text()
            pathModified = True
            self.modified = True
        
        if (self.filename != self.ui.entryPath.text()):
            self.filename = self.ui.entryPath.text()
            self.modified = True
        
        if (self.lang != self.ui.comboLanguage.currentText()):
            self.lang = self.ui.comboLanguage.currentText()
            self.modified = True
        
        path = []
        for i in range(self.ui.listLocation.count()):
            path.append(self.ui.listLocation.item(i).text())
        if (self.path != path):
            self.path = path
            self.modified = True
            pathModified = True
            
        if (self.includeSub != self.ui.checkIncludeSub.isChecked()):
            self.includeSub = self.ui.checkIncludeSub.isChecked()
            self.modified = True
            pathModified = True
        
        if (self.mode == World.projectNew):
            if (self.filename):
                self.saveProject(self.filename)
                self.openProject(self.filename)
        
        # emit updateCatalog only path has modified.
        if (self.mode == World.projectProperty) and (pathModified):
            self.emit(QtCore.SIGNAL("updateCatalog"), self.path, self.includeSub, self.name)
        
        self.emit(QtCore.SIGNAL("hasModified"), self.modified)
        self.close()
    
    def openProject(self, filename = None):
        """
        Open filename and store properties. Store CurrentProject entry to World.
        
        @param filename: the project file (.ini) to read.
        @return bool: indicates the function has accept or reject.
        """
        if (not filename):
            filename = self.getOpenFileName()
            if (not filename):
                return False
        
        if (not self.closeProject()):
            return False
        
        # Set current project
        World.settings.setValue("CurrentProject", QtCore.QVariant(filename))
        
        # Get project properties
        catalog = QtCore.QSettings(filename, QtCore.QSettings.IniFormat)
        self.name = catalog.value("name").toString()
        self.filename = filename
        self.lang = catalog.value("language").toString()
        self.path = catalog.value("path").toStringList()
        self.includeSub = catalog.value("includeSub").toBool()
        
        self.emit(QtCore.SIGNAL("updateCatalog"), self.path, self.includeSub, self.name)
        return True
    
    def closeProject(self):
        """
        Clear properties. Remove CurrentProject entry from World.
        """
        if (self.modified):
            ret = QtGui.QMessageBox.question(self, self.tr("Project Modified"),
                self.tr("The project has been modified.\n"
                "Do you want to save changes?"),
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.Default,
                QtGui.QMessageBox.No,
                QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Escape)
            
            if (ret == QtGui.QMessageBox.Yes):
                self.saveProject(self.filename)
            elif (ret == QtGui.QMessageBox.Cancel):
                return False
        
        World.settings.setValue("CurrentProject", QtCore.QVariant(""))
        
        # Clear project properties
        self.name = ""
        self.filename = ""
        self.lang = ""
        self.path = []
        self.includeSub = False
        
        self.modified = False
        self.emit(QtCore.SIGNAL("updateCatalog"), self.path, self.includeSub, self.name)
        return True
    
    def saveProject(self, filename = None):
        """
        Save project in filename. Project will have; name, language, path,
        and includeSub.
        
        @param filename: file name to save.
        """
        
        # open save as dialog
        if (not self.filename) and (not filename):
            directory = World.settings.value("workingDir").toString()
            filename = QtGui.QFileDialog.getSaveFileName(self,
                    self.tr("Save File As"),
                    directory,
                    self.tr("Ini file fomat (*.ini)"))
            if (filename):
                if (not filename.endsWith(".ini", QtCore.Qt.CaseInsensitive)):
                    filename = filename + ".ini"
            else:
                return
            self.filename = filename
        
        elif (self.filename):
            filename = self.filename
        
        World.settings.setValue("CurrentProject", QtCore.QVariant(filename))
        proSettings = QtCore.QSettings(filename, QtCore.QSettings.IniFormat)
        proSettings.setValue("name", QtCore.QVariant(self.name))
        proSettings.setValue("language", QtCore.QVariant(self.lang))
        proSettings.setValue("path", QtCore.QVariant(self.path))
        proSettings.setValue("includeSub", QtCore.QVariant(self.includeSub))
        
        self.modified = False
        self.emit(QtCore.SIGNAL("hasModified"), self.modified)
    
    def getOpenFileName(self):
        """
        Open a file dialog for choosing project file as .ini format.
        """
        directory = World.settings.value("workingDir").toString()
        filename = QtGui.QFileDialog.getOpenFileName(self, self.tr("Open File"),
                    directory,
                    self.tr("Ini file fomat (*.ini)"))
        if (filename):
            self.openProject(filename)
            directory = os.path.dirname(unicode(filename))
            World.settings.setValue("workingDir", QtCore.QVariant(directory))
        
        return filename
    
    def enableOkButton(self):
        """
        Enable or disable ok button.
        """
        name = self.ui.entryName.text()
        filePath = self.ui.entryPath.text()
        if (name and filePath):
            self.ui.btnOK.setEnabled(True)
        else:
            self.ui.btnOK.setEnabled(False)
    
    def showNew(self):
        """
        Show new project.
        """
        self.mode = World.projectNew
        self.setWindowTitle(self.tr("New Project"))
        self.ui.btnOK.setText(self.tr("Save"))
        
        self.ui.entryName.setText("")
        self.ui.entryPath.setText("")
        self.ui.comboLanguage.setCurrentIndex(0)
        self.clearLocation()
        self.ui.checkIncludeSub.setChecked(False)
        
        self.show()
    
    def showProperties(self):
        """
        Show current project properties.
        """
        if (not self.filename):
            filename = World.settings.value("CurrentProject").toString()
            if (filename):
                # Get project properties
                catalog = QtCore.QSettings(filename, QtCore.QSettings.IniFormat)
                self.name = catalog.value("name").toString()
                self.filename = filename
                self.lang = catalog.value("language").toString()
                self.path = catalog.value("path").toStringList()
                self.includeSub = catalog.value("includeSub").toBool()
        
        self.mode = World.projectProperty
        self.setWindowTitle(self.tr("Project Properties"))
        self.ui.btnOK.setText(self.tr("OK"))
        
        self.ui.entryName.setText(self.name)
        self.ui.entryPath.setText(self.filename)
        langIndex = self.ui.comboLanguage.findText(self.lang)
        langIndex = ((langIndex > -1) and langIndex) or 0
        self.ui.comboLanguage.setCurrentIndex(langIndex)
        
        self.clearLocation()
        for location in self.path:
            self.addLocation(location)
        self.ui.checkIncludeSub.setChecked(self.includeSub)
        
        self.show()
    
if __name__ == "__main__":
    import os, sys
    app = QtGui.QApplication(sys.argv)
    Newpro = newProject(None)
    Newpro.showProperties()
    sys.exit(Newpro.exec_())
