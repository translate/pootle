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
# This module is providing an setting path of translation memory dialog 

import sys, os
import tempfile
from PyQt4 import QtCore, QtGui
from pootling.ui.Ui_tmSetting import Ui_tmsetting
from pootling.modules import World
from pootling.modules import FileDialog
from pootling.modules.pickleTM import pickleTM
from translate.storage import factory
from translate.storage import poheader
from translate.search import match

class globalSetting(QtGui.QDialog):
    """Code for setting path of translation memory and Glossary dialog.
    
    @signal matcher: emitted with self.matcher, self.section when the timer finishes the last filename in self.filenames 
    @signal buildPercentage: emitted with percentage to update progress bar
    """
    
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.ui = None
        self.title = None
        self.section = None
    
    def lazyInit(self):
        if (self.ui):
            # already has ui
            return
            
        self.ui = Ui_tmsetting()
        self.ui.setupUi(self)
        self.setModal(True)
        self.setWindowTitle(self.title)
        self.connect(self.ui.btnOk, QtCore.SIGNAL("clicked(bool)"), self.startBuild)
        self.connect(self.ui.btnCancel, QtCore.SIGNAL("clicked(bool)"), QtCore.SLOT("close()"))
        self.connect(self.ui.btnAdd, QtCore.SIGNAL("clicked(bool)"), self.showFileDialog)
        self.connect(self.ui.btnRemove, QtCore.SIGNAL("clicked(bool)"), self.removeLocation)
        self.connect(self.ui.btnRemoveAll, QtCore.SIGNAL("clicked(bool)"), self.ui.listWidget.clear)
        self.ui.listWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        
        if (self.section == "TM"):
            self.setToolWhatsThis("Translation Memory")
            self.ui.spinMaxLen.setMaximum(500)
        elif (self.section == "Glossary"):
            self.setToolWhatsThis("Glossary")
            self.ui.spinMaxLen.setMaximum(100)
        
        # timer for extend tm
        self.timer = QtCore.QTimer()
        self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.extendMatcher)
        
        # get pickleFile
        World.settings.beginGroup(self.section)
        self.pickleFile = World.settings.value("pickleFile").toString()
        World.settings.endGroup()
        if (not self.pickleFile):
            handle, self.pickleFile = tempfile.mkstemp('','PKL')

    def setToolWhatsThis(self, tool):
        """
        Set what's this for TM or glossary dialog.
        
        @param tool: whether it is a TM or Glossary, type as string.
        """
        list = "<h3>Path for " + tool + "</h3>List of path to scan for " + tool + ". Paths which are checked will be used. "
        self.ui.listWidget.setWhatsThis(self.tr(list))
        dive = "<h3>Dive into subfolders</h3>Check this option, " + tool + " will include subfolders of the above path(s)."
        self.ui.checkBox.setWhatsThis(self.tr(dive))
        sim = "<h3>Minimum similarity</h3>Minimum similarity of source strings to be include in " + tool
        self.ui.spinSimilarity.setWhatsThis(self.tr(sim))
        candidate = "<h3>Maximum search result</h3>Number of result that will be shown in the " + tool +" lookup view."
        self.ui.spinMaxCandidate.setWhatsThis(self.tr(candidate))
        self.ui.spinMaxLen.setWhatsThis(self.tr("<h3>Maximum string length</h3>Maximum number of source string to search from."))
        progress = "<h3>Build " + tool + "Process</h3>This bar shows the progression of building a " + tool + " from the above select path(s)."
        self.ui.progressBar.setWhatsThis(self.tr(progress))
    
    def showFileDialog(self):
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
    
    def showDialog(self):
        """
        Make the Translation Memory or Glossary Setting dialog visible.
        """
        self.lazyInit()
        self.ui.progressBar.setValue(0)
        
        # get application setting file, and parse it.
        self.loadSettings()
        self.ui.btnOk.setEnabled(True)
        self.show()
        
    def loadSettings(self):
        """
        Load settings of TM/Glossary
        """
        self.ui.listWidget.clear()
        World.settings.beginGroup(self.section)
        enabledPath = World.settings.value("enabledpath").toStringList()
        disabledPath = World.settings.value("disabledpath").toStringList()
        includeSub = World.settings.value("diveintosub").toBool()
        World.settings.endGroup()
        
        for path in enabledPath:
            self.addLocation(path)
        for path in disabledPath:
            self.addLocation(path, QtCore.Qt.Unchecked)
        
        if (len(enabledPath) > 0) or (len(disabledPath) > 0):
            self.ui.listWidget.setCurrentRow(0)
        
        minSim = self.getMinimumSimilarity()
        maxCan = self.getMaximumCandidates()
        maxLen = self.getMaximumLenght()
        
        self.ui.checkBox.setChecked(includeSub)
        self.ui.spinSimilarity.setValue(minSim)
        self.ui.spinMaxCandidate.setValue(maxCan)
        self.ui.spinMaxLen.setValue(maxLen)
    
    def addLocation(self, TMpath, checked = QtCore.Qt.Checked):
        """
        Add TMpath to TM list.
        
        @param TMpath: Filename as string
        """
        items = self.ui.listWidget.findItems(TMpath, QtCore.Qt.MatchCaseSensitive)
        if (not items):
            item = QtGui.QListWidgetItem(TMpath)
            item.setCheckState(checked and QtCore.Qt.Checked or QtCore.Qt.Unchecked)
            self.ui.listWidget.addItem(item)
    
    def removeLocation(self):
        """
        Remove selected path TM list.
        """
        items = self.ui.listWidget.selectedItems()
        for item in items:
            self.ui.listWidget.setCurrentItem(item)
            self.ui.listWidget.takeItem(self.ui.listWidget.currentRow())
    
    def startBuild(self):
        """
        Collect filename into self.filenames, call buildMatcher(),
        dump matcher, and save settings.
        """
        self.ui.btnOk.setEnabled(False)
        
        disabledPath = self.getPathList(QtCore.Qt.Unchecked)
        minSim = self.ui.spinSimilarity.value()
        maxCan = self.ui.spinMaxCandidate.value()
        maxLen = self.ui.spinMaxLen.value()
        # save some settings
        World.settings.beginGroup(self.section)
        World.settings.setValue("disabledpath", QtCore.QVariant(disabledPath))
        World.settings.setValue("similarity", QtCore.QVariant(minSim))
        World.settings.setValue("max_candidates", QtCore.QVariant(maxCan))
        World.settings.setValue("max_string_len", QtCore.QVariant(maxLen))
        World.settings.endGroup()
        
        # get filenames from checked list.
        enabledPath = self.getPathList(QtCore.Qt.Checked)
        includeSub = self.ui.checkBox.isChecked()
        self.buildMatcher(enabledPath, includeSub)
        
    def buildMatcher(self, paths, includeSub=True):
        """
        create matcher, start a timer for extend tm.
        """
        self.lazyInit()
        
        # save some settings
        World.settings.beginGroup(self.section)
        World.settings.setValue("enabledpath", QtCore.QVariant(paths))
        World.settings.setValue("diveintosub", QtCore.QVariant(includeSub))
        World.settings.setValue("pickleFile", QtCore.QVariant(self.pickleFile))
        World.settings.endGroup()
        
        self.matcher = None
        self.filenames = []
        for path in paths:
            self.getFiles(path, includeSub)
        
        # close dialog if no filename.
        if (len(self.filenames) <= 0):
            self.timer.stop()
            self.iterNumber = 1
            self.dumpMatcher()
            self.emitMatcher()
            self.close()
            return
        
        # start build matcher with self.filenames[0]
        store = self.createStore(self.filenames[0])
        self.matcher = None
        if (store):
            maxCan = self.getMaximumCandidates()
            minSim = self.getMinimumSimilarity()
            maxLen = self.getMaximumLenght()
            if (self.section == "TM"):
                self.matcher = match.matcher(store, maxCan, minSim, maxLen)
            else:
                self.matcher = match.terminologymatcher(store, maxCan, minSim, maxLen)
        # extend matcher, start with self.filenames[1]
        self.iterNumber = 1
        self.timer.stop()
        self.timer.start(10)
        
    def getFiles(self, path, includeSub): 
        """
        Get the filenames. Only supported files are taken into account;
        and if it's directory and includeSub is True, dive into it and add files.
        
        @param paths: file or directory path for adding to Catalog.
        @param includeSub: a bool value; dive into sub, if it is true.
        """
        path = unicode(path)
        if (os.path.isfile(path)):
            # if file is already existed in the item's child... skip.
            if (path.endswith(".po") or path.endswith(".pot") or path.endswith(".xlf") or path.endswith(".xliff")):
                self.filenames.append(path)
        
        if (os.path.isdir(path)) and (not path.endswith(".svn")):
            for root, dirs, files in os.walk(path):
                for file in files:
                    path = os.path.join(root + os.path.sep + file)
                    self.getFiles(path, includeSub)
                    
                # whether dive into subfolder
                if (includeSub):
                    for folder in dirs:
                        path = os.path.join(root + os.path.sep + folder)
                        self.getFiles(path, includeSub)
                break
    
    def extendMatcher(self):
        """
        extend TM to self.matcher through self.filenames with self.iterNumber 
        as iterator.
        
        @signal matcher: This signal is emitted with self.matcher, 
            self.section when the timer finishes the last filename in self.filenames 
        @signal buildPercentage: emitted with percentage to update progress bar
        """
        if (len(self.filenames) <= 1):
            self.timer.stop()
            self.iterNumber = 1
            self.dumpMatcher()
            self.emitMatcher()
            self.close()
            return
        
        # stop the timer for processing the extendMatcher()
        self.timer.stop()
        filename = self.filenames[self.iterNumber]
        store = self.createStore(filename)
        if (store):
            if (self.matcher):
                self.matcher.extendtm(store.units, store)
            else:
                maxCan = self.getMaximumCandidates()
                minSim = self.getMinimumSimilarity()
                maxLen = self.getMaximumLenght()
                if (self.section == "TM"):
                    self.matcher = match.matcher(store, maxCan, minSim, maxLen)
                else:
                    self.matcher = match.terminologymatcher(store, maxCan, minSim, maxLen)
        self.iterNumber += 1
        perc = int((float(self.iterNumber) / len(self.filenames)) * 100)
        self.ui.progressBar.setValue(perc)
        self.emit(QtCore.SIGNAL("buildPercentage"), perc)
        
        # resume timer
        self.timer.start(10)
        
        if (self.iterNumber == len(self.filenames)):
            self.timer.stop()
            self.iterNumber = 1
            self.dumpMatcher()
            self.emitMatcher()
            self.close()
    
    def emitMatcher(self):
        """
        emit "matcher" with self.matcher, self.section
        """
        self.emit(QtCore.SIGNAL("matcher"), self.matcher, self.section)
    
    def dumpMatcher(self):
        """
        call pickleTM.dumpMatcher()
        """
        p = pickleTM()
        p.dumpMatcher(self.matcher, self.pickleFile)
    
    def createStore(self, file):
        """
        Create a store object from file.
        add translator, date, and filepath properties to store object.
        
        @param file: as a file path or object
        @return: store as a base object
        """
        try:
            store = factory.getobject(file)
        except:
            store = None
            return None
        store.filepath = file
        if (isinstance(store, poheader.poheader)):
            headerDic = store.parseheader()
            store.translator = headerDic.get('Last-Translator') 
            store.date = headerDic.get('PO-Revision-Date') 
            if (store.translator == None):
                store.translator = ""
            if (store.date == None):
                store.date = ""
        else:
            store.translator = ""
            store.date = ""
        return store
    
    def getPathList(self, isChecked):
        """
        Return list of path according to the parameter isChecked or unChecked.
        
        @param isChecked: as bool type
        @return: itemList as list of unchecked or checked path
        """
        
        itemList = QtCore.QStringList()
        count = self.ui.listWidget.count()
        for i in range(count):
            item = self.ui.listWidget.item(i)
            if (not (item.checkState() ^ isChecked)):
                itemList.append(str(item.text()))
        return itemList
    
    def getMaximumCandidates(self):
        """
        Return the maximum candidates number as integer.
        """
        World.settings.beginGroup(self.section)
        result = World.settings.value("max_candidates", QtCore.QVariant(10)).toInt()[0]
        World.settings.endGroup()
        return result
        
    def getMinimumSimilarity(self):
        """"
        Return the minimum similarity as integer.
        """
        World.settings.beginGroup(self.section)
        result = World.settings.value("similarity", QtCore.QVariant(75)).toInt()[0]
        World.settings.endGroup()
        return result
        
    def getMaximumLenght(self):
        """
        returen the maximum string lenth
        """
        if (self.section == "TM"):
            defValue = 100
        else:
            defValue = 70
        World.settings.beginGroup(self.section)
        result = World.settings.value("max_string_len", QtCore.QVariant(defValue)).toInt()[0]
        World.settings.endGroup()
        return result
    
class tmSetting(globalSetting):
    def __init__(self, parent):
        globalSetting.__init__(self, parent)
        self.title = "Configure translation memory"
        self.section = "TM"

class glossarySetting(globalSetting):
    def __init__(self, parent):
        globalSetting.__init__(self, parent)
        self.title = "Configure glossary"
        self.section = "Glossary"

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    tm = tmSetting(None)
    tm.showDialog()
    sys.exit(tm.exec_())

