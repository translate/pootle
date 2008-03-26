#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2006 - 2007 by The WordForge Foundation
# www.wordforge.org
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
# This module is working on Catalog Manager of translation files

from PyQt4 import QtCore, QtGui
from pootling.ui.Ui_Catalog import Ui_Catalog
from pootling.modules.CatalogSetting import CatalogSetting
from pootling.modules import tmSetting
from pootling.modules.AboutEditor import AboutEditor
from translate.storage import factory
import pootling.modules.World as World
from pootling.modules.FindInCatalog import FindInCatalog
from pootling.modules.NewProject import newProject
from pootling.ui.Ui_tmSetting import Ui_tmsetting
from pootling import __version__
import os, sys

class Catalog(QtGui.QMainWindow):
    """
    The Catalog Manager which holds the toolviews.
    """
    def __init__(self, parent = None):
        QtGui.QMainWindow.__init__(self, parent)
        self.ui = None
    
    def lazyInit(self):
        """
        Initialize only at time of calling Catalog.
        """
        if (self.ui):
            return
        self.ui = Ui_Catalog()
        self.ui.setupUi(self)
        self.resize(720,400)
        self.autoRefresh = True
        self.updateRecentProject()
        self.setWindowTitle(self.tr("%s Catalog Manager" % (World.settingApp)))
        self.ui.toolBar.toggleViewAction()
        self.ui.actionBuildTM.setEnabled(False)
        self.ui.toolBar.setWindowTitle("ToolBar View")
        self.ui.toolBar.setStatusTip("Toggle toolbar view")
        
        self.folderIcon = QtGui.QIcon("../images/open.png")
        self.iconFile = QtGui.QIcon("../images/iconfile.png")
        # set up table appearance and behavior
        self.headerLabels = [self.tr("Name"),
                            self.tr("Untranslated"),
                            self.tr("Fuzzy"),
                            self.tr("Translated"),
                            self.tr("Total"),
                            self.tr("CVS/SVN Status"),
                            self.tr("Last Revision"),
                            self.tr("Last Translator")]
        self.ui.treeCatalog.setColumnCount(len(self.headerLabels))
        self.ui.treeCatalog.setHeaderLabels(self.headerLabels)
        self.ui.treeCatalog.setSortingEnabled(True)
        self.ui.treeCatalog.sortItems(0, QtCore.Qt.AscendingOrder)
        self.ui.treeCatalog.hideColumn(5)
        self.ui.treeCatalog.header().setResizeMode(QtGui.QHeaderView.Interactive)

        # Quit action
        self.connect(self.ui.actionQuit, QtCore.SIGNAL("triggered()"), QtCore.SLOT("close()"))
        
        # Reload action
        self.connect(self.ui.actionReload, QtCore.SIGNAL("triggered()"), self.refresh)
        
        # Stop action
        self.connect(self.ui.actionStop, QtCore.SIGNAL("triggered()"), self.stopUpdate)
        
        # Statistic action
        self.connect(self.ui.actionStatistics, QtCore.SIGNAL("triggered()"), self.showStatistic)
        
        # a new project of Catalog Manager
        self.Project = newProject(self)
        self.connect(self.ui.actionNew, QtCore.SIGNAL("triggered()"), self.showNew)
        self.connect(self.ui.actionOpen, QtCore.SIGNAL("triggered()"), self.openProject)
        self.connect(self.ui.actionSave, QtCore.SIGNAL("triggered()"), self.Project.saveProject)
        self.connect(self.ui.actionSaveAs, QtCore.SIGNAL("triggered()"), self.Project.saveProject)
        self.connect(self.ui.actionClose, QtCore.SIGNAL("triggered()"), self.closeProject)
        self.connect(self.ui.actionProperties, QtCore.SIGNAL("triggered()"), self.showProperties)
        self.connect(self.Project, QtCore.SIGNAL("updateCatalog"), self.updateCatalog)
        self.connect(self.Project, QtCore.SIGNAL("hasModified"), self.setModified)
        
        # catalog setting's checkboxes action.
        self.catSetting = CatalogSetting(self)
        self.connect(self.ui.actionPreferences, QtCore.SIGNAL("triggered()"), self.catSetting.show)
        self.connect(self.ui.actionBuildTM, QtCore.SIGNAL("triggered()"), self.emitBuildTM)
        self.connect(self.catSetting.ui.chbname, QtCore.SIGNAL("stateChanged(int)"), self.toggleHeaderItem)
        self.connect(self.catSetting.ui.chbfuzzy, QtCore.SIGNAL("stateChanged(int)"), self.toggleHeaderItem)
        self.connect(self.catSetting.ui.chblastrevision, QtCore.SIGNAL("stateChanged(int)"), self.toggleHeaderItem)
        self.connect(self.catSetting.ui.chbtranslator, QtCore.SIGNAL("stateChanged(int)"), self.toggleHeaderItem)
        self.connect(self.catSetting.ui.chbuntranslated, QtCore.SIGNAL("stateChanged(int)"), self.toggleHeaderItem)
        self.connect(self.catSetting.ui.chbtotal, QtCore.SIGNAL("stateChanged(int)"), self.toggleHeaderItem)
        self.connect(self.catSetting.ui.chbSVN, QtCore.SIGNAL("stateChanged(int)"), self.toggleHeaderItem)
        self.connect(self.catSetting.ui.chbtranslated, QtCore.SIGNAL("stateChanged(int)"), self.toggleHeaderItem)
        
        # Create Find String in Catalog
        self.findBar = FindInCatalog(self)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.findBar)

        self.connect(self.ui.actionFind_in_Files, QtCore.SIGNAL("triggered()"), self.findBar.showFind)
        # emit findfiles signal from FindInCatalog file
        self.connect(self.findBar, QtCore.SIGNAL("findNext"), self.findNext)
        self.connect(self.findBar, QtCore.SIGNAL("returnSignal"), self._setFocusOnCatalog)

        # progress bar
        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setEnabled(True)
        self.progressBar.setProperty("value", QtCore.QVariant(0))
        self.progressBar.setOrientation(QtCore.Qt.Horizontal)
        self.progressBar.setObjectName("progressBar")
        self.progressBar.setVisible(False)
        self.ui.statusbar.addPermanentWidget(self.progressBar)

        # Help menu of aboutQt
        self.ui.menuHelp.addSeparator()
        action = QtGui.QWhatsThis.createAction(self)
        self.ui.menuHelp.addAction(action)
        self.aboutDialog = AboutEditor(self)
        self.connect(self.ui.actionAbout, QtCore.SIGNAL("triggered()"), self.aboutDialog.showDialog)
        self.connect(self.ui.actionAboutQt, QtCore.SIGNAL("triggered()"), QtGui.qApp, QtCore.SLOT("aboutQt()"))
        
        self.connect(self.ui.treeCatalog, QtCore.SIGNAL("itemDoubleClicked(QTreeWidgetItem *, int)"), self.emitOpenFile)
        self.connect(self.ui.treeCatalog.model(), QtCore.SIGNAL("layoutChanged()"), self.sort)
        self.connect(self.ui.treeCatalog, QtCore.SIGNAL("currentItemChanged(QTreeWidgetItem *, QTreeWidgetItem *)"), self.itemChanged)
        self.setupCheckbox()
                
        # timer..
        self.timer = QtCore.QTimer()
        self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.updateStatistic)
        self.lastFoundNumber = 0
        
        # context menu of items
        self.menu = QtGui.QMenu()
        actionOpen = self.menu.addAction(QtGui.QIcon("../images/open.png"), self.tr("Open"))
        actionFind = self.menu.addAction(QtGui.QIcon("../images/find.png"), self.tr("Find"))
        actionShowStat = self.menu.addAction(QtGui.QIcon("../images/statistic.png"), self.tr("Show statistic"))
        if (self.autoRefresh):
            actionOpen.setEnabled(False)
            actionFind.setEnabled(False)
            actionShowStat.setEnabled(False)

        self.connect(actionOpen, QtCore.SIGNAL("triggered()"), self.emitOpenFile)
        self.connect(actionFind, QtCore.SIGNAL("triggered()"), self.findBar.showFind)
        self.connect(actionShowStat, QtCore.SIGNAL("triggered()"), self.showStatistic)
        
        # install custom menu event for treeCatalog
        self.ui.treeCatalog.contextMenuEvent = self.customContextMenuEvent
        
        self.reachedEnd = False
        self.currentFileOpen = None
        self.searchString = None
        # bool indicates progress bar need update as TM progresses.
        self.allowUpdate = False
        self.catalogModified = False
        
        self.notFoundString = None
    
    def itemChanged(self, curItem, preItem):
        """
        slot item changed, use to reset self.reachedEnd, self.currentFileOpen
        to mark the start of search circle.
        
        @param curItem: QTreeWidgetItem
        @param preItem: QTreeWidgetItem
        These two params are not used at the moment.
        """
        
        self.reachedEnd = False
        self.currentFileOpen = None
    
    def setSearchStatus(self, message):
        """
        Set search status so that we can determine the search is end at operator.
        
        @param message: a string tells about the status of search process.
        """
        if (message == "reachedEnd"):
            self.reachedEnd = True
    
    def findNext(self, searchString, searchOptions):
        """
        The search here is only determine if search string exist in filename,
        then it connects to search function in operator.
        
        @param searchString: text to search for; type string.
        @param searchOptions: source and/or target; type as integer defined in world.
        """
        if (not searchString):
            return
        
        # if it starts with last-not-found string, do not search.
        if (self.notFoundString) and (searchString[:len(self.notFoundString)] == self.notFoundString):
            self.findBar.setColorStatus("notFound")
            self.ui.statusbar.showMessage(self.tr("Search was not found."), 3000)
            return
        
        if (not self.reachedEnd) and (self.currentFileOpen) and (searchString == self.searchString):
            self.emit(QtCore.SIGNAL("searchNext"))
            return
        
        currentItem = self.ui.treeCatalog.currentItem()
        resumePoint = self.fileItems.index(currentItem)
        for item in self.fileItems[resumePoint:] + self.fileItems[:resumePoint]:
            filename = self.getFilename(item)
            if (filename == self.currentFileOpen) and (self.reachedEnd):
                continue
            # first find if it is in the file or not.
            store = factory.getobject(filename)
            if (not hasattr(store, "units")):
                continue
            found = -1
            for unit in store.units:
                searchableText = ""
                if (searchOptions & World.source):
                    searchableText += unit.source or ""
                if (searchOptions & World.target):
                    searchableText += unicode(unit.target)
                index = searchableText.lower().find(searchString.lower())
                if (index > -1):
                    found = index
                    break
            if (found >= 0):
                self.notFoundString = None
                self.currentFileOpen = filename
                self.searchString = searchString
                self.ui.treeCatalog.setCurrentItem(item)
                self.emit(QtCore.SIGNAL("openFile"), filename)
                filter = []
                if (searchOptions & World.source):
                    filter.append(World.source)
                if (searchOptions & World.target):
                    filter.append(World.target)
                self.emit(QtCore.SIGNAL("initSearch"), searchString, filter, False)
                self.emit(QtCore.SIGNAL("searchNext"))
                break
            self.reachedEnd = False
        else:
            self.notFoundString = searchString
            self.currentFileOpen = None
            self.searchString = None
            self.findBar.setColorStatus("notFound")
            self.ui.statusbar.showMessage(self.tr("Search was not found."), 3000)
    
    def _getStringFromUnit(self, unit, fields):
        """
        Return QString of unit's field; source, target.
        
        @param unit: class unit.
        @param fields: members of class unit such as source or target.
        """
        unitString = ""
        if (fields & World.source):
            unitString += unit.source
        if (fields & World.target):
            unitString += unit.target
        return unitString

    def showStatistic(self):
        """
        Show statistic message in a dialog.
        """
        item = self.ui.treeCatalog.currentItem()
        if (not item):
            return
        
        filename = self.getFilename(item)
        
        title = unicode(os.path.basename(filename))
        
        self.numOfFiles = 0
        stats = self.getStatsFromItem(item)
        translated = stats["translated"]
        fuzzy = stats["fuzzy"]
        untranslated = stats["untranslated"]
        total = float(translated + fuzzy + untranslated)
        
        if (total > 0):
            perTranslated = str((translated/total) * 100)
            perTranslated = perTranslated[0:perTranslated.find(".")+3] + "%"
            perFuzzy = str((fuzzy/total) * 100)
            perFuzzy = perFuzzy[0:perFuzzy.find(".")+3] + "%"
            perUntranslated = str((untranslated/total) * 100)
            perUntranslated = perUntranslated[0:perUntranslated.find(".")+3] + "%"
        else:
            perTranslated = "0%"
            perFuzzy = "0%"
            perUntranslated = "0%"

        from pootling.modules.StatisticsDialog import StatisticDialog
        self.statisticsDialog = StatisticDialog(self)

        self.lblStatistic = self.statisticsDialog.ui.lblStatistic
        self.lblStatistic.setText(title)

        self.lblNumberofFiles = self.statisticsDialog.ui.lblNumberofFiles
        self.lblNumberofFiles.setText(str(self.numOfFiles))
  
        self.lblTranslated = self.statisticsDialog.ui.lblTranslated
        self.lblTranslated.setText(str(translated))
      
        self.lblTransPercent = self.statisticsDialog.ui.lblTransPercent
        self.lblTransPercent.setText(perTranslated)

        self.lblFuzzy = self.statisticsDialog.ui.lblFuzzy
        self.lblFuzzy.setText(str(fuzzy))

        self.lblFuzzyPercent = self.statisticsDialog.ui.lblFuzzyPercent
        self.lblFuzzyPercent.setText(perFuzzy)

        self.lblUntranslated = self.statisticsDialog.ui.lblUntranslated
        self.lblUntranslated.setText(str(untranslated)) 

        self.lblUntranPercent = self.statisticsDialog.ui.lblUntranPercent
        self.lblUntranPercent.setText(perUntranslated) 

        self.lblTotal = self.statisticsDialog.ui.lblTotal
        self.lblTotal.setText(str(int(total)))

        self.statisticsDialog.show()

    def toggleHeaderItem(self):
        """
        Show or hide the header label of catalog main window.
        """
        if (isinstance(self.sender(), QtGui.QCheckBox)):
            text = self.sender().text()
            if text in self.headerLabels:
                checked = self.sender().isChecked()
                if (checked):
                    self.ui.treeCatalog.showColumn(self.headerLabels.index(text))
                    self.ui.treeCatalog.hideColumn(5)
                else:
                    self.ui.treeCatalog.hideColumn(self.headerLabels.index(text))
                    self.ui.treeCatalog.hideColumn(5)
                World.settings.setValue("Catalog." + text, QtCore.QVariant(checked))

    def updateProgress(self, value):
        """
        Set the value for the progress bar.
        self.allowUpdate is a condition whether to update or not, use to protect
        other class call.
        
        @param value: value to set, type as int.
        """
        if (not hasattr(self, "allowUpdate")) or (not self.allowUpdate):
           return
        if (not self.progressBar.isVisible()):
            self.progressBar.setVisible(True)
        elif (value == 100):
            self.allowUpdate = False
            self.progressBar.setVisible(False)
        self.progressBar.setValue(value)
        
    def showDialog(self):
        """
        Display the Catalog main window with configured information.
        """
        self.lazyInit()
        self.show()
        
        if (self.ui.treeCatalog.topLevelItemCount() == 0):
            # first look if there's current project previously opened.
            currentProject = World.settings.value("CurrentProject").toString()
            if (currentProject):
                self.openProject(currentProject)
    
    def updateCatalog(self, cats, includeSub, name):
        """
        Read data from "cats" and display statistic of files in tree view.
        
        @param cats: a list of file or folder paths
        @param includeSub: a boolean variable. If true, dive into sub folder.
        """
        if (cats):
            self.ui.actionSaveAs.setEnabled(True)
            self.ui.actionReload.setEnabled(True)
            self.ui.actionStop.setEnabled(True)
            self.ui.actionFind_in_Files.setEnabled(True)
            self.ui.actionStatistics.setEnabled(True)
            self.ui.actionProperties.setEnabled(True)
            self.ui.actionBuildTM.setEnabled(True)
            self.ui.actionClose.setEnabled(True)
            
        else:
            self.ui.actionSaveAs.setEnabled(False)
            self.ui.actionReload.setEnabled(False)
            self.ui.actionStop.setEnabled(False)
            self.ui.actionFind_in_Files.setEnabled(False)
            self.ui.actionStatistics.setEnabled(False)
            self.ui.actionProperties.setEnabled(False)
            self.ui.actionBuildTM.setEnabled(False)
            self.ui.actionClose.setEnabled(False)
            self.progressBar.setVisible(False)
            self.ui.treeCatalog.clear()
            return
        
        if (not self.isVisible()):
            self.showDialog()
        
        title = unicode(self.tr("%s - %s  Catalog Manager")) % (unicode(name), World.settingApp)
        self.setWindowTitle(str(title))
        
        self.ui.treeCatalog.clear()
        for catalogFile in cats:
            catalogFile = unicode(catalogFile)
            self.addCatalogFile(catalogFile, includeSub, None)
        
        self.sort()
        self.ui.treeCatalog.resizeColumnToContents(0)
        self.allowUpdate = True
##        self._setFocusOnCatalog()
        
        self.ui.treeCatalog.setFocus()
        self.itemNumber = 0
        self.timer.start(10)
    
    def keyReleaseEvent(self, event):
        """
        A subclass for keyReleaseEvent.
        """
        # press Enter key to open the file.
        if (event.key() == 16777220) and (self.ui.treeCatalog.currentItem()):
            self.emitOpenFile()

    def _setFocusOnCatalog(self):
        """
        Set focus on the first item in Catalog treeview.
        """
        if (self.fileItems):
            item = self.fileItems[0]
            self.ui.treeCatalog.setCurrentItem(item)
            self.ui.treeCatalog.setFocus()
    
    def addCatalogFile(self, path, includeSub, item):
        """
        add path to catalog tree view if it's file, if it's directory then
        dive into it and add files.
        
        @param path: file or directory path to set to the catalog tree view.
        @param includeSub: If it is True, dive into subfolder
        @param item: childItem in the folder
        """
        if (os.path.isfile(path)):
            existedItem = self.getExistedItem(os.path.dirname(path))
            if (existedItem):
                item = existedItem
            elif (item == None):
                item = QtGui.QTreeWidgetItem(item)
                self.ui.treeCatalog.addTopLevelItem(item)
                self.ui.treeCatalog.expandItem(item)
                item.setText(0, os.path.dirname(path))

            # if file is already existed in the item's child... skip.
            if (path.endswith(".po") or path.endswith(".pot") or path.endswith(".xlf") or path.endswith(".xliff")) and (not self.ifFileExisted(path, item)):
                childItem = QtGui.QTreeWidgetItem(item)
                childItem.setText(0, os.path.basename(path))
                childItem.setIcon(0, self.iconFile)
            # check extension of file if not have .po or .pot or xlf and xliff files. hide folder
#            if (item.childCount() == 0):
#                item.parent().takeChild(0)

        if (os.path.isdir(path)) and (not path.endswith(".svn")):
            existedItem = self.getExistedItem(path)
            if (existedItem):
                # it's already existed, so use the existed one
                childItem = existedItem
            else:
                # it does not exist in tree yet, create new one
                if (item == None):
                    childItem = QtGui.QTreeWidgetItem(item)
                    self.ui.treeCatalog.addTopLevelItem(childItem)
                    self.ui.treeCatalog.expandItem(childItem)
                    childItem.setText(0, path)
                # it's existed in tree but it is the sub directory
                elif hasattr(item, "parent"):
##                    childItem = QtGui.QTreeWidgetItem()
##                    item.insertChild(0, childItem)
                    childItem = QtGui.QTreeWidgetItem(item)
                    childItem.setText(0, os.path.basename(path))
                childItem.setIcon(0, self.folderIcon)

#            if (item.childCount() == 0):
#                item.setHidden(True)

            for root, dirs, files in os.walk(path):
                for file in files:
                    path = os.path.join(root + os.path.sep + file)
                    self.addCatalogFile(path, includeSub, childItem)
                # whether dive into subfolder
                if (includeSub):
                    for folder in dirs:
                        path = os.path.join(root + os.path.sep + folder)
                        self.addCatalogFile(path, includeSub, childItem)
                break
            
        self.ui.treeCatalog.expandItem(item)
    
    def updateFileStatus(self, filename):
        """
        Update status of a file.
        
        @param filename: the file whose status will be updated.
        """
        if (not self.isVisible()):
            return
        for item in self.fileItems:
            if filename == self.getFilename(item):
                statusDic = self.getStats(filename)
                item.setText(1, (str(statusDic["numUntranslated"])).rjust(4))
                item.setText(2, (str(statusDic["numFuzzy"])).rjust(4))
                item.setText(3, (str(statusDic["numTranslated"])).rjust(4))
                item.setText(4, (str(statusDic["numTotal"])).rjust(4))
                item.setText(5, statusDic["subVersionState"])
                item.setText(6, statusDic["revisionDate"])
                item.setText(7, statusDic["lastTranslator"])
                break

    def getExistedItem(self, path):
        """
        Check if the path is duplicated. If it is duplicated, returns
        the item, otherwise returns False.
        
        @param path: file or directory path getting from Catalog
                            Location list to check if it is duplicated.
        """
        for i in range(self.ui.treeCatalog.topLevelItemCount()):
            item = self.ui.treeCatalog.topLevelItem(i)
            if (hasattr(item, "text")) and (item.text(0) == path):
                return item
        return False
    
    def ifFileExisted(self, path, item):
        """
        Get existed item in the view. If the item existed, it returns
        the item, otherwise returns False.
        
        @param path: file or directory path to get if it is existed.
        @param item: QTreeWidgetItem
        """
        if (not hasattr(item, "childCount")):
            return False
        for i in range(item.childCount()):
            it = item.child(i)
            if (hasattr(it, "text")) and (it.text(0) == os.path.basename(path)):
                return it
        return False
    
    def getStats(self, filename):
        """
        return a dictionary which consists of basename, translatedCount, fuzzyCount,
        untranslatedCount, totalCount, subVersionState, revisionDate, lastTranslator from the filename.
        return False when error.
        
        @param filename: path and file name whose status is returned.
        """
        if (not os.path.isfile(filename)):
            return False
        
        try:
            store = factory.getobject(filename)
        except:
            return False
        
        basename = os.path.basename(filename)
        numTranslated = store.translated_unitcount()
        numFuzzy = store.fuzzy_unitcount()
        numUntranslated = store.untranslated_unitcount()
    
        numTotal = numTranslated + numUntranslated + numFuzzy
        subVersionState = ""
        
        revisionDate = ""
        lastTranslator = ""
        if hasattr(store, "parseheader"):
            headerDic = store.parseheader()
            try:
                revisionDate = str(headerDic["PO-Revision-Date"])
            except:
                pass
            try:
                lastTranslator = str(headerDic["Last-Translator"])
            except:
                pass
        
        return {"basename":basename, "numUntranslated":numUntranslated, "numFuzzy":numFuzzy, 
                "numTranslated":numTranslated ,"numTotal":numTotal, 
                "subVersionState":subVersionState, "revisionDate":revisionDate, 
                "lastTranslator":lastTranslator}

    def getStatsFromItem(self, item):
        """
        get number of untranslated, fuzzy, and translated units from item.
        
        @param item: treewidget item which has at least those four fields.
        @return dictionary of stats.
        """
        try:
            translated = int(item.text(1))
            fuzzy = int(item.text(2))
            untranslated = int(item.text(3))
            self.numOfFiles += 1
        except:
            translated = 0
            fuzzy = 0
            untranslated = 0
        
        for i in range(item.childCount()):
            child = item.child(i)
            stats = self.getStatsFromItem(child)
            translated += stats["translated"]
            fuzzy += stats["fuzzy"]
            untranslated += stats["untranslated"]
        
        
        return {"untranslated":untranslated, "fuzzy":fuzzy, "translated": translated}
    
    def setupCheckbox(self):
        """
        Set checked or unchecked for the header label of Catalog main window.
        """
        
        value = World.settings.value("Catalog.Name")
        if (value.isValid()):
            if not (value.toBool()):
                checkState = QtCore.Qt.Unchecked
            else:
                checkState = QtCore.Qt.Checked
        else:
            # on fresh start of program, if the value is not in setting yet
            # make it True by default.
            checkState = QtCore.Qt.Checked
        self.catSetting.ui.chbname.setCheckState(checkState)
        
        value = World.settings.value("Catalog.Translated")
        if (value.isValid()):
            if not (value.toBool()):
                checkState = QtCore.Qt.Unchecked
            else:
                checkState = QtCore.Qt.Checked
        else:
            checkState = QtCore.Qt.Checked
        self.catSetting.ui.chbtranslated.setCheckState(checkState)
        
        value = World.settings.value("Catalog.Fuzzy")
        if (value.isValid()):
            if not (value.toBool()):
                checkState = QtCore.Qt.Unchecked
            else:
                checkState = QtCore.Qt.Checked
        else:
            checkState = QtCore.Qt.Checked
        self.catSetting.ui.chbfuzzy.setCheckState(checkState)
        
        value = World.settings.value("Catalog.Untranslated")
        if (value.isValid()):
            if not (value.toBool()):
                checkState = QtCore.Qt.Unchecked
            else:
                checkState = QtCore.Qt.Checked
        else:
            checkState = QtCore.Qt.Checked
        self.catSetting.ui.chbuntranslated.setCheckState(checkState)
        
        value = World.settings.value("Catalog.Total")
        if (value.isValid()):
            if not (value.toBool()):
                checkState = QtCore.Qt.Unchecked
            else:
                checkState = QtCore.Qt.Checked
        else:
            checkState = QtCore.Qt.Checked
        self.catSetting.ui.chbtotal.setCheckState(checkState)
        
        value = World.settings.value("Catalog.CVS/SVN Status")
        if (value.isValid()):
            if not (value.toBool()):
                checkState = QtCore.Qt.Unchecked
            else:
                checkState = QtCore.Qt.Checked
        else:
            checkState = QtCore.Qt.Checked
        self.catSetting.ui.chbSVN.setCheckState(checkState)
        self.catSetting.ui.chbSVN.setVisible(False)
        
        value = World.settings.value("Catalog.Last Revision")
        if (value.isValid()):
            if not (value.toBool()):
                checkState = QtCore.Qt.Unchecked
            else:
                checkState = QtCore.Qt.Checked
        else:
            checkState = QtCore.Qt.Checked
        self.catSetting.ui.chblastrevision.setCheckState(checkState)
        
        value = World.settings.value("Catalog.Last Translator")
        if (value.isValid()):
            if not (value.toBool()):
                checkState = QtCore.Qt.Unchecked
            else:
                checkState = QtCore.Qt.Checked
        else:
            checkState = QtCore.Qt.Checked
        self.catSetting.ui.chbtranslator.setCheckState(checkState)
        
    def emitOpenFile(self, item=None, col=None):
        """
        Send "openFile" signal with filename.
        
        @param item: type as treewidget item 
        @param col: type as int. 
        """
        if (not item):
            try:
                item = self.ui.treeCatalog.selectedItems()[0]
            except:
                return
        
        filename = self.getFilename(item)

        if (os.path.isfile(filename)): 
            self.emit(QtCore.SIGNAL("openFile"), filename)
        
    def getFilename(self, item):
        """
        return filename join from item.text(0) to its parent.
        
        @ param item: type as treewidget item. column must be 0 because
                                the filename is in the first col.
        """
        if (not hasattr(item, "text")):
            return None
        filename = unicode(item.text(0))
        if (item.parent()):
            filename = os.path.join(self.getFilename(item.parent()) + os.path.sep + filename)
        return filename
    
    def refresh(self):
        """
        Slot to refresh Catalog information.
        """
        self.stopUpdate()
        
        for item in self.fileItems:
            item.setText(1, "")
            item.setText(2, "")
            item.setText(3, "")
            item.setText(4, "")
            item.setText(5, "")
            item.setText(6, "")
            item.setText(7, "")
        
        self.itemNumber = 0
        self.timer.start(10)
    
    def emitBuildTM(self):
        """
        Emit "buildTM" signal with catalog paths.
        """
        catPaths = []
        for i in range(self.ui.treeCatalog.topLevelItemCount()):
            topItem = self.ui.treeCatalog.topLevelItem(i)
            catPath = self.getFilename(topItem)
            catPaths.append(catPath)
        self.allowUpdate = True
        self.emit(QtCore.SIGNAL("buildTM"), catPaths)
    
    def updateStatistic(self):
        """
        Update statistic information once adding file to the Catalog tree.
        """
        if (len(self.fileItems) <= 0):
            self.timer.stop()
            self.itemNumber = 0
            return

        self.timer.stop()
        
        item = self.fileItems[self.itemNumber]
        path = self.getFilename(item)
        childStats = self.getStats(path)
  
        if (childStats):
            item.setText(1, (str(childStats["numUntranslated"])).rjust(4))
            item.setText(2, (str(childStats["numFuzzy"])).rjust(4))
            item.setText(3, (str(childStats["numTranslated"])).rjust(4))
            item.setText(4, (str(childStats["numTotal"])).rjust(4))
            item.setText(5, childStats["subVersionState"])
            item.setText(6, childStats["revisionDate"])
            item.setText(7, childStats["lastTranslator"])

        self.itemNumber += 1
        
        perc = int((float(self.itemNumber) / len(self.fileItems)) * 100)
        self.updateProgress(perc)
        
        # start getting statistic
        self.timer.start(10)
        if (self.itemNumber == len(self.fileItems)):
            self.timer.stop()
            self.itemNumber = 0
    
    def stopUpdate(self):
        """
        Stop loading the file(s) into Catalog treeview.
        """
        self.timer.stop()
        self.updateProgress(100)

    def updateRecentProject(self):
        """
        Open openRecentProject list in World, and update it in recent open menu.
        Put current project on top of list.
        """
        
        projectList = World.settings.value("recentProjectList").toStringList()
        projectFilename = World.settings.value("CurrentProject").toString()
        
        if (projectFilename):
            # remove from list if it's already existed.
            projectFilenameIndex = projectList.indexOf(projectFilename)
            if (projectFilenameIndex >= 0):
                projectList.removeAt(projectFilenameIndex)
            # then add current project at top
            projectList.prepend(projectFilename)
        
        # remove older recent files when reached max count.
        while (projectList.count() > World.MaxRecentFiles + 1):
            projectList.removeAt(World.MaxRecentFiles + 1)
        World.settings.setValue("recentProjectList", QtCore.QVariant(projectList))
        
        i = 0
        self.ui.menuOpenRecentProject.clear()
        for project in projectList:
            i += 1
            recentAction = QtGui.QAction(self)
            recentAction.setText(self.tr("&" + str(i) + ": ") + project)
            recentAction.setData(QtCore.QVariant(project))
            self.ui.menuOpenRecentProject.addAction(recentAction)
            self.connect(recentAction, QtCore.SIGNAL("triggered()"), self.openRecentProject)
        
        self.ui.menuOpenRecentProject.addSeparator()
        clearAction = QtGui.QAction(self.tr("&Clear"), self)
        self.ui.menuOpenRecentProject.addAction(clearAction)
        self.connect(clearAction, QtCore.SIGNAL("triggered()"), self.clearRecentProject)
        
        if (projectList):
            self.ui.menuOpenRecentProject.setEnabled(True)
        else:
            self.ui.menuOpenRecentProject.setEnabled(False)
        
    def clearRecentProject(self):
        """
        Slot to clear all path in open recent project list.
        """
        self.ui.menuOpenRecentProject.clear()
        self.ui.menuOpenRecentProject.setEnabled(False)
        World.settings.remove("recentProjectList")

    def openRecentProject(self):
        """
        Get the file from the open recent list and call openProject().
        """
        action = self.sender()
        filename = action.data().toString()
        
        # A dialog ask to remove death file name.
        if (not(os.path.isfile(filename))):
            titled = unicode(self.tr("%s was not found.\nDo you want to remove it from list?")) % (unicode(filename))
            ret = QtGui.QMessageBox.critical(self, self.tr("Error"), 
                titled,
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.Default, 
                QtGui.QMessageBox.No | QtGui.QMessageBox.Escape) 
            if (ret == QtGui.QMessageBox.Yes):
                projectList = World.settings.value("recentProjectList").toStringList()
                filenameIndex = projectList.indexOf(filename)
                if (filenameIndex >= 0):
                    projectList.removeAt(filenameIndex)
                World.settings.setValue("recentProjectList", QtCore.QVariant(projectList))
                self.updateRecentProject()
            return
        
        self.openProject(filename)
    
    def customContextMenuEvent(self, e):
        """
        A subclass for customContextMenu event.
        """
        self.menu.exec_(e.globalPos())
    
    def sort(self):
        """
        Re-arrange the fileItems to suit the sorting order.
        """
        self.fileItems = []
        for i in range(self.ui.treeCatalog.topLevelItemCount()):
            item = self.ui.treeCatalog.topLevelItem(i)
            self.fileItems += self.getItems(item)
##            
##        for i in range(self.ui.treeCatalog.topLevelItemCount()):
##            item = self.ui.treeCatalog.topLevelItem(i)
##            self.sortItemsByType(item, i)
    
    def getItems(self, items):
        """
        Return a list of item in items.
        
        @param items: type as treewidget item.
        """
        item = [items]
        # children
        for i in range(items.childCount()):
            item += self.getItems(items.child(i))
        return item

##    def sortItemsByType(self, items, index):
##        """
##        type items: QTreeWidgetItem.
##        """
##        if (not items):
##            return
##        
##        for i in range(items.childCount()):
##            item = items.child(i)
##            self.sortItemsByType(item, i)
##        
##        name = self.getFilename(items)
##        if os.path.isdir(name):
##            parent = items.parent()
##            if (parent):
##                print "will take", items, "at", index
##                print "will add", items, "at 0"
####                parent.takeChild(index)
####                parent.insertChild(0, items)
##    

    def setModified(self, bool):
        """
        Mark modified state of catalog.
        """
        self.catalogModified = bool
        self.ui.actionSave.setEnabled(bool)
    
    def showNew(self):
        """
        Slot to call Project.showNew()
        """
        self.lazyInit()
        self.Project.showNew()
        
    def showProperties(self):
        """
        Slot to call Project.showProperties()
        """
        self.lazyInit()
        self.Project.showProperties()
    
    def openProject(self, filename = None):
        """
        Slot to call Project.openProject().
        """
        self.emit(QtCore.SIGNAL("projectOpened"), True)
        self.lazyInit()
        self.Project.openProject(filename)
        self.updateRecentProject()
    
    def closeProject(self):
        """
        Stop update to avoid crash and call Project.closeProject().
        """
        self.emit(QtCore.SIGNAL("projectOpened"), False)
        self.stopUpdate()
        self.Project.closeProject()
    
    def saveBeforeLose(self):
        """
        Look if the contents has been modified and ask to save.
        
        @return bool: indicates the function has accept or reject.
        """
        if (self.catalogModified):
            ret = QtGui.QMessageBox.question(self, self.tr("Catalog Modified"),
                self.tr("The catalog has been modified.\n"
                        "Do you want to save changes?"),
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.Default,
                QtGui.QMessageBox.No,
                QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Escape)
            
            if (ret == QtGui.QMessageBox.Yes):
                self.Project.saveProject()
            elif (ret == QtGui.QMessageBox.Cancel):
                return False
        return True
        
    def closeEvent(self, event):
        """
        Action before close catalog dialog.
        @param even: QCloseEvent Object
        
        @signal updateCatalog: emitted when self.projectPath is modified.
        """
        QtGui.QMainWindow.closeEvent(self, event)
        if (self.saveBeforeLose()):
            event.accept()
        else:
            event.ignore()
    
def main():
    # set the path for QT in order to find the icons
    if __name__ == "__main__":
        QtCore.QDir.setCurrent(os.path.join(sys.path[0], "../ui"))
        app = QtGui.QApplication(sys.argv)
        catalog = Catalog()
        catalog.showDialog()
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()
