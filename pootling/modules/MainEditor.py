#!/usr/bin/python
# -*- coding: utf-8 -*-
#Copyright (c) 2006 - 2007 by The WordForge Foundation
#                       www.wordforge.org
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2.1
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
# This module is working on the main windows of Editor

import os
import sys
from PyQt4 import QtCore, QtGui
from pootling.ui.Ui_MainEditor import Ui_MainWindow
from pootling.modules.TUview import TUview
from pootling.modules.Overview import OverviewDock
from pootling.modules.Comment import CommentDock
from pootling.modules.Header import Header
from pootling.modules.Operator import Operator
from pootling.modules.FileAction import FileAction
from pootling.modules.Find import Find
from pootling.modules.Catalog import Catalog
from pootling.modules.NewProject import newProject
from pootling.modules.Preference import Preference
from pootling.modules.AboutEditor import AboutEditor
import pootling.modules.World as World
from pootling.modules import tmSetting
from pootling.modules import tableTM
from pootling.modules import TableGlossary
from pootling import __version__

class MainWindow(QtGui.QMainWindow):
    """
    The main window which holds the toolviews.
    """

    def __init__(self, parent = None):
        QtGui.QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.recentaction = []
        self.bookmarkaction = []
        self.setWindowTitle(World.settingApp + ' ' + __version__.ver)
        self.maxBookmark = 10
        self.delimiter = " : "
        self.createBookmarkAction()
        self.clearBookmarks()
        imagesdir = "../images"
        self.ui.actionAuto_translate.setEnabled(False)
        app = QtGui.QApplication.instance()
        self.connect(app, QtCore.SIGNAL("focusChanged(QWidget *,QWidget *)"), self.focusChanged)
        
        # get the last geometry
        geometry = World.settings.value("lastGeometry")
        if (geometry.isValid()):
            self.setGeometry(geometry.toRect())

        sepAction = self.ui.menuWindow.actions()[0]
        #plug in overview widget
        self.dockOverview = OverviewDock(self)
        self.addDockWidget(QtCore.Qt.TopDockWidgetArea, self.dockOverview)
        action = self.dockOverview.toggleViewAction()
        action.setText("&Overview")
        action.setStatusTip("Toggle the Overview window")
        action.setWhatsThis("<h3>Toggle the Overview window</h3>If the Overview window is hidden then display it. If it is displayed then close it.")
        self.ui.menuWindow.insertAction(sepAction, action)
        
        #plug in TUview widget
        self.dockTUview = TUview(self)
        self.setCentralWidget(self.dockTUview)
        action = self.dockTUview.toggleViewAction()
        action.setText("&Detail")
        action.setStatusTip("Toggle the Detail window")
        action.setWhatsThis("<h3>Toggle the Detail window</h3>If the Detail window is hidden then display it. If it is displayed then close it.")
        self.ui.menuWindow.insertAction(sepAction, action)
        
        #Plug in glossary widget
        self.tableGlossary = TableGlossary.TableGlossary(self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.tableGlossary)
        action = self.tableGlossary.toggleViewAction()
        action.setText("Glossary Lookup")
        action.setStatusTip("Toggle the Glossary Lookup window")
        action.setWhatsThis("<h3>Toggle the Glossary Lookup window</h3>If the Glossary Lookup window is hidden then display it. If it is displayed then close it.")
        self.ui.menuWindow.insertAction(sepAction, action)
        
        #plug in comment widget
        self.dockComment = CommentDock(self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dockComment)
        action = self.dockComment.toggleViewAction()
        action.setText("&Comment")
        action.setStatusTip("Toggle the Comment window")
        action.setWhatsThis("<h3>Toggle the Comment window</h3>If the Comment window is hidden then display it. If it is displayed then close it.")
        self.ui.menuWindow.insertAction(sepAction, action)
       
        #add widgets to statusbar
        self.statusfuzzy = QtGui.QLabel()
        pixmap = QtGui.QPixmap(os.path.join(imagesdir, "fuzzy.png"))
        self.statusfuzzy.setPixmap(pixmap.scaled(16, 16, QtCore.Qt.KeepAspectRatio))
        self.statusfuzzy.setToolTip("Current unit is fuzzy")
        
        self.statuslabel = QtGui.QLabel()
        self.statuslabel.setFrameStyle(QtGui.QFrame.NoFrame)
        self.statuslabel.setMargin(1)
        self.ui.statusbar.addWidget(self.statuslabel)
        self.ui.statusbar.setWhatsThis("<h3>Status Bar</h3>Shows the progress of the translation in the file and messages about the current state of the application.")

        #add action from each toolbar toggleviewaction to toolbars submenu of view menu
        self.ui.menuToolbars.addAction(self.ui.toolFile.toggleViewAction())
        self.ui.menuToolbars.addAction(self.ui.toolEdit.toggleViewAction())
        self.ui.menuToolbars.addAction(self.ui.toolNavigation.toggleViewAction())
        self.ui.menuToolbars.addAction(self.ui.toolFilter.toggleViewAction())

        #create operator
        self.operator = Operator()
        
        # action Tool menu of Catalog Manager
        self.Catalog = Catalog(self)
        self.connect(self.ui.actionCatalogManager, QtCore.SIGNAL("triggered()"), self.Catalog.showDialog)
        self.connect(self.Catalog, QtCore.SIGNAL("initSearch"), self.operator.initSearch)
        self.connect(self.Catalog, QtCore.SIGNAL("searchNext"), self.operator.searchNext)
        
        # TM table
        self.table = tableTM.tableTM(self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.table)
        action = self.table.toggleViewAction()
        action.setText("TM &Lookup")
        action.setStatusTip("Toggle the TM Lookup window")
        action.setWhatsThis("<h3>Toggle the TM Lookup window</h3>If the TM Lookup window is hidden then display it. If it is displayed then close it.")
        self.ui.menuWindow.insertAction(sepAction, action)
        
        self.connect(self.operator, QtCore.SIGNAL("requestTargetChanged"), self.dockTUview.emitTargetChanged)
        
        # translation memory
        self.connect(self.dockOverview, QtCore.SIGNAL("requestUnit"), self.operator.emitRequestUnit)
        self.connect(self.operator, QtCore.SIGNAL("tmRequest"), self.dockOverview.popupTranslation)
        self.connect(self.operator, QtCore.SIGNAL("tmCandidates"), self.table.fillTable)
        self.connect(self.table, QtCore.SIGNAL("translation2target"), self.dockTUview.translation2target)
        self.connect(self.table, QtCore.SIGNAL("visible"), self.operator.setTmLookup)
        
        # glossary
        self.connect(self.dockTUview, QtCore.SIGNAL("lookupTerm"), self.operator.emitTermRequest)
        self.connect(self.operator, QtCore.SIGNAL("termRequest"), self.dockTUview.popupTerm)
        self.connect(self.operator, QtCore.SIGNAL("termCandidates"), self.tableGlossary.fillTable)
        self.connect(self.tableGlossary, QtCore.SIGNAL("closed"), self.toggleTUviewTermSig)
        self.connect(self.tableGlossary, QtCore.SIGNAL("shown"), self.toggleTUviewTermSig)
        self.connect(self.operator, QtCore.SIGNAL("currentUnit"), self.tableGlossary.newUnit)
        
        #Help menu of aboutQt
        self.ui.menuHelp.addSeparator()
        action = QtGui.QWhatsThis.createAction(self)
        action.setText(self.tr("&What's This?"))
        action.setStatusTip("Context sensitive help")
        action.setWhatsThis("<h3>Display context sensitive help</h3>In what's This? mode, the mouse cursor shows an arrow with a question mark, and you can click on the interface elements to get a short description of what they do and how to use them in a dialog, the feature can be accessed using the context help button in the titlebar.")
        self.ui.menuHelp.addAction(action)
        self.aboutDialog = AboutEditor(self)
        self.connect(self.ui.actionAbout, QtCore.SIGNAL("triggered()"), self.aboutDialog.showDialog)
        self.connect(self.ui.actionAboutQT, QtCore.SIGNAL("triggered()"), QtGui.qApp, QtCore.SLOT("aboutQt()"))
        
        # create file action object and file action menu related signals
        self.fileaction = FileAction(self)
        self.connect(self.ui.actionOpen, QtCore.SIGNAL("triggered()"), self.fileaction.openFile)
        self.connect(self.ui.action_Close, QtCore.SIGNAL("triggered()"), self.closeFile)
        self.connect(self.ui.actionSave, QtCore.SIGNAL("triggered()"), self.saveFile)
        self.connect(self.ui.actionSaveas, QtCore.SIGNAL("triggered()"), self.fileaction.saveAs)
        self.connect(self.ui.actionExit, QtCore.SIGNAL("triggered()"), QtCore.SLOT("close()"))
        self.createRecentAction()
        
        # create Find widget and connect signals related to it
        self.findBar = Find(self)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.findBar)
        self.connect(self.ui.actionFind, QtCore.SIGNAL("triggered()"), self.findBar.showFind)
        self.connect(self.ui.actionFindNext, QtCore.SIGNAL("triggered()"), self.searchNext)
        self.connect(self.ui.actionFindPrevious, QtCore.SIGNAL("triggered()"), self.searchPrevious)
        self.connect(self.ui.actionReplace, QtCore.SIGNAL("triggered()"), self.findBar.showReplace)
        self.connect(self.findBar, QtCore.SIGNAL("initSearch"), self.operator.initSearch)
        self.connect(self.findBar, QtCore.SIGNAL("searchNext"), self.searchNext)
        self.connect(self.findBar, QtCore.SIGNAL("searchPrevious"), self.searchPrevious)
        self.connect(self.table, QtCore.SIGNAL("findUnit"), self.operator.slotFindUnit)
        self.connect(self.operator, QtCore.SIGNAL("searchStatus"), self.findBar.setColorStatus)
        self.connect(self.operator, QtCore.SIGNAL("searchStatus"), self.displayTempMessage)
        
        self.connect(self.findBar, QtCore.SIGNAL("replace"), self.operator.replace)
        self.connect(self.findBar, QtCore.SIGNAL("replaceAll"), self.operator.replaceAll)
        
        self.connect(self.operator, QtCore.SIGNAL("glossaryPattern"), self.dockTUview.setPattern)
        self.connect(self.operator, QtCore.SIGNAL("highlightGlossary"), self.dockTUview.setHighlightGlossary)
        self.connect(self.operator, QtCore.SIGNAL("searchResult"), self.dockTUview.setSearchString)
        self.connect(self.operator, QtCore.SIGNAL("searchResult"), self.dockComment.setSearchString)
        self.connect(self.operator, QtCore.SIGNAL("searchStatus"), self.Catalog.setSearchStatus)
        # "replaceText" sends text field, start, length, and text to replace.
        self.connect(self.operator, QtCore.SIGNAL("replaceText"), self.dockTUview.replaceText)
        self.connect(self.operator, QtCore.SIGNAL("replaceText"), self.dockComment.replaceText)
       
        # Goto menu action
        self.ui.actionGoTo.setIcon(QtGui.QIcon(os.path.join(imagesdir, "goto.png")))
        self.connect(self.ui.actionGoTo, QtCore.SIGNAL("triggered()"), self.showGoto)
        
        # Bookmarks menu action
        self.connect(self.ui.actionAddBookmarks, QtCore.SIGNAL("triggered()"), self.setBookmarks)
        self.connect(self.ui.actionClearBookmarks, QtCore.SIGNAL("triggered()"), self.clearBookmarks)

        self.connect(self.ui.actionNewPro, QtCore.SIGNAL("triggered()"), self.Catalog.showNew)
        self.connect(self.ui.actionOpenPro, QtCore.SIGNAL("triggered()"), self.Catalog.openProject)
        self.connect(self.ui.actionProperties, QtCore.SIGNAL("triggered()"), self.Catalog.showProperties)
        self.connect(self.Catalog, QtCore.SIGNAL("projectOpened"), self.ui.actionProperties.setEnabled)
        
        # action Preferences menu 
        self.preference = Preference(self)
        self.connect(self.ui.actionPreferences, QtCore.SIGNAL("triggered()"), self.preference.showDialog)
        self.connect(self.preference, QtCore.SIGNAL("settingsChanged"), self.dockComment.applySettings)
        self.connect(self.preference, QtCore.SIGNAL("settingsChanged"), self.dockOverview.applySettings)
        self.connect(self.preference, QtCore.SIGNAL("settingsChanged"), self.dockTUview.applySettings)
        self.connect(self.preference, QtCore.SIGNAL("settingsChanged"), self.operator.applySettings)
        self.connect(self.preference, QtCore.SIGNAL("settingsChanged"), self.table.applySettings)
        self.connect(self.preference, QtCore.SIGNAL("settingsChanged"), self.tableGlossary.applySettings)

        # action lookup text and auto translation from TM
        self.connect(self.ui.actionAuto_translate, QtCore.SIGNAL("triggered()"), self.operator.autoTranslate)
        
        # action setting Path of TM
        self.tmsetting = tmSetting.tmSetting(self)
        self.connect(self.ui.actionBuild_TM, QtCore.SIGNAL("triggered()"), self.tmsetting.showDialog)
        self.connect(self.tmsetting, QtCore.SIGNAL("matcher"), self.operator.setMatcher)
        
        # action setting path of glossary
        self.glossary = tmSetting.glossarySetting(self)
        self.connect(self.ui.actionGlossary, QtCore.SIGNAL("triggered()"), self.glossary.showDialog)
        self.connect(self.glossary, QtCore.SIGNAL("matcher"), self.operator.setMatcher)
        
        # Edit Header
        self.headerDialog = Header(self, self.operator)
        self.connect(self.ui.actionEdit_Header, QtCore.SIGNAL("triggered()"), self.headerDialog.showDialog)
        self.connect(self.headerDialog, QtCore.SIGNAL("showPreference()"), self.preference.showDialog)

        # Other actions
        self.connect(self.ui.actionFirst, QtCore.SIGNAL("triggered()"), self.dockOverview.scrollFirst)
        self.connect(self.ui.actionPrevious, QtCore.SIGNAL("triggered()"), self.dockOverview.scrollPrevious)
        self.connect(self.ui.actionNext, QtCore.SIGNAL("triggered()"), self.dockOverview.scrollNext)
        self.connect(self.ui.actionLast, QtCore.SIGNAL("triggered()"), self.dockOverview.scrollLast)
        self.connect(self.ui.actionCopySource2Target, QtCore.SIGNAL("triggered()"), self.dockTUview.source2target)
        self.connect(self.ui.actionCopySearchResult2Target, QtCore.SIGNAL("triggered()"), self.table.emitTarget)

        # action filter menu
        self.connect(self.ui.actionFilterFuzzy, QtCore.SIGNAL("toggled(bool)"), self.operator.filterFuzzy)
        self.connect(self.ui.actionFilterTranslated, QtCore.SIGNAL("toggled(bool)"), self.operator.filterTranslated)
        self.connect(self.ui.actionFilterUntranslated, QtCore.SIGNAL("toggled(bool)"), self.operator.filterUntranslated)
        self.connect(self.ui.actionToggleFuzzy, QtCore.SIGNAL("triggered()"), self.operator.toggleFuzzy)
        self.connect(self.ui.actionClear_Fuzzies, QtCore.SIGNAL("triggered()"), self.operator.clearFuzzies)
    
        # "currentUnit" sends currentUnit, currentIndex
        self.connect(self.operator, QtCore.SIGNAL("currentUnit"), self.dockOverview.updateView)
        self.connect(self.operator, QtCore.SIGNAL("currentUnit"), self.dockTUview.updateView)
        self.connect(self.operator, QtCore.SIGNAL("currentUnit"), self.dockComment.updateView)

        self.connect(self.operator, QtCore.SIGNAL("currentUnit"), self.addFuzzyIcon)
        self.connect(self.dockOverview, QtCore.SIGNAL("filteredIndex"), self.operator.setUnitFromPosition)
        self.connect(self.dockTUview, QtCore.SIGNAL("scrollToRow"), self.dockOverview.scrollToRow)
        
        self.connect(self.dockOverview, QtCore.SIGNAL("targetChanged"), self.operator.setTarget)
        self.connect(self.dockTUview, QtCore.SIGNAL("targetChanged"), self.operator.setTarget)
        self.connect(self.dockTUview, QtCore.SIGNAL("textChanged"), self.dockOverview.updateText)
        self.connect(self.dockComment, QtCore.SIGNAL("textChanged"), self.dockOverview.markComment)
        self.connect(self.dockComment, QtCore.SIGNAL("commentChanged"), self.operator.setComment)
        self.connect(self.fileaction, QtCore.SIGNAL("fileToSave"), self.operator.saveStoreToFile)
        self.connect(self.dockTUview, QtCore.SIGNAL("textChanged"), self.operator.contentChanged)
        self.connect(self.dockComment, QtCore.SIGNAL("textChanged"), self.operator.contentChanged)
        self.connect(self.operator, QtCore.SIGNAL("enableSave"), self.setSaveEnabled)
        
        # get "returnFilename" signal from operator of saveStoreToFile function
        self.connect(self.operator, QtCore.SIGNAL("returnFilename"), self.updateStatistic)

        self.connect(self.fileaction, QtCore.SIGNAL("fileToSave"), self.setTitle)
        self.connect(self.dockOverview, QtCore.SIGNAL("toggleFirstLastUnit"), self.toggleFirstLastUnit)

        self.connect(self.operator, QtCore.SIGNAL("newUnits"), self.dockOverview.slotNewUnits)
        self.connect(self.operator, QtCore.SIGNAL("newUnits"), self.dockTUview.viewSetting)
        self.connect(self.operator, QtCore.SIGNAL("newUnits"), self.dockComment.viewSetting)
        # "filterChanged" sends filter and number of filtered items.
        self.connect(self.operator, QtCore.SIGNAL("filterChanged"), self.dockOverview.filterChanged)
        self.connect(self.operator, QtCore.SIGNAL("filterChanged"), self.dockTUview.filterChanged)

        # set file status information to text label of status bar.
        self.connect(self.operator, QtCore.SIGNAL("currentStatus"), self.setStatus)
        self.connect(self.fileaction, QtCore.SIGNAL("fileToOpen"), self.openFile)

        # progress bar
        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setEnabled(True)
        self.progressBar.setProperty("value",QtCore.QVariant(0))
        self.progressBar.setOrientation(QtCore.Qt.Horizontal)
        self.progressBar.setObjectName("progressBar")
        self.progressBar.setVisible(False)
        self.ui.statusbar.addPermanentWidget(self.progressBar)
        self.connect(self.dockOverview, QtCore.SIGNAL("progressBarValue"), self.updateProgress)
        self.connect(self.operator, QtCore.SIGNAL("progressBarValue"), self.updateProgress)

        # get the last state of mainwindows's toolbars and dockwidgets
        state = World.settings.value("MainWindowState")
        # check if the last state is valid it will restore
        if (state.isValid()):
            self.restoreState(state.toByteArray(), 1)
        
        tuViewHidden = World.settings.value("TuViewHidden", QtCore.QVariant(False))
        self.dockTUview.setHidden(tuViewHidden.toBool())
        self.findBar.setHidden(True)
        
        self.connect(self.Catalog, QtCore.SIGNAL("openFile"), self.openFile)
        self.connect(self.Catalog, QtCore.SIGNAL("buildTM"), self.tmsetting.buildMatcher)
        self.connect(self.tmsetting, QtCore.SIGNAL("buildPercentage"), self.Catalog.updateProgress)
        
        self.connect(self.table, QtCore.SIGNAL("openFile"), self.openFile)
        self.connect(self.table, QtCore.SIGNAL("goto"), self.dockOverview.gotoRow)
        
        self.operator.applySettings()
        catalogProject = World.settings.value("CurrentProject").toString()
        self.ui.actionProperties.setEnabled(bool(catalogProject))
        
    
    def updateProgress(self, value):
        if (not self.progressBar.isVisible()):
            self.progressBar.setVisible(True)
        elif (value == 100):
            self.progressBar.setVisible(False)
        self.progressBar.setValue(value)
    
    def enableCopyCut(self, bool):
        self.ui.actionCopy.setEnabled(bool)
        self.ui.actionCut.setEnabled(bool)

    def enableUndo(self, bool):
        self.ui.actionUndo.setEnabled(bool)

    def enableRedo(self, bool):
        self.ui.actionRedo.setEnabled(bool)

    def showGoto(self):
        value, ok = QtGui.QInputDialog.getInteger(self, self.tr("Goto"), self.tr("String Number:"), 1, 1, self.operator.status.numTotal)
        if ok:
            self.dockOverview.gotoRow(value)

    def setBookmarks(self):
        unit = self.operator.getCurrentUnit()
        id = self.dockOverview.getCurrentIndex()

        reducedSource = str(id) + self.delimiter + unit.source[:15] + "..."
        bookmark = World.settings.value("bookmarkList").toStringList()
        bookmark.removeAll(reducedSource)
        bookmark.prepend(reducedSource)
        bookmark.sort()
        while bookmark.count() > self.maxBookmark:
            bookmark.removeAt(bookmark.count() - 1)
        World.settings.setValue("bookmarkList", QtCore.QVariant(bookmark))
        self.updateBookmarkAction()

    def createBookmarkAction(self):
        for i in range(self.maxBookmark):
            self.bookmarkaction.append(QtGui.QAction(self))
            self.bookmarkaction[i].setVisible(False)
            self.connect(self.bookmarkaction[i], QtCore.SIGNAL("triggered()"), self.startBookmarkAction)
            self.ui.menuBookmark.addAction(self.bookmarkaction[i])
        self.updateBookmarkAction()
    
    def startBookmarkAction(self):
        action = self.sender()
        if action:
            index = str(action.data().toString()).split(self.delimiter)
            self.dockOverview.gotoRow(int(index[0]))
    
    def updateBookmarkAction(self):
        """
        Update bookmark action
        """
        bookmark = World.settings.value("bookmarkList").toStringList()
        numBookmark = min(bookmark.count(), self.maxBookmark)
        for i in range(numBookmark):
            self.bookmarkaction[i].setText(bookmark[i])
            self.bookmarkaction[i].setData(QtCore.QVariant(bookmark[i]))
            self.bookmarkaction[i].setVisible(True)

        for j in range(numBookmark, self.maxBookmark):
            self.bookmarkaction[j].setVisible(False)

    def clearBookmarks(self):
        files = World.settings.value("bookmarkList").toStringList()
        numClear = min(files.count(), self.maxBookmark)
        for i in range(numClear):
            self.bookmarkaction[i].setVisible(False)
        World.settings.remove("bookmarkList")
    
    def prependOpenRecent(self, fileName):
        """
        Append the recentely opened file to the open recent list.
        @param fileName string, the filename to append to Open Recent.
        """
        files = World.settings.value("recentFileList").toStringList()
        files.removeAll(fileName)
        files.prepend(fileName)
        while files.count() > World.MaxRecentFiles:
            files.removeAt(files.count() - 1)
        if (files.count() > 0):
            self.ui.menuOpen_Recent.setEnabled(True)
        World.settings.setValue("recentFileList", QtCore.QVariant(files))
        self.updateRecentAction()
        
    def startRecentAction(self):
        action = self.sender()
        if action:
            # TODO: remove filename from recent file if it doesn't exist.
            filename = unicode(action.data().toString())
            self.openFile(filename)
    
    def clearRecentAction(self):
        self.ui.menuOpen_Recent.clear()
        self.ui.menuOpen_Recent.setEnabled(False)
        World.settings.remove("recentFileList")
        # remove menu Open_Recent action, and add Open action to toolbar
        self.addOpenToBar()
    
    def createRecentAction(self):
        for i in range(World.MaxRecentFiles):
            self.recentaction.append(QtGui.QAction(self))
            self.recentaction[i].setVisible(False)
            self.connect(self.recentaction[i], QtCore.SIGNAL("triggered()"), self.startRecentAction)
            self.ui.menuOpen_Recent.addAction(self.recentaction[i])
        self.ui.menuOpen_Recent.addSeparator()
        self.clearAction = QtGui.QAction("&Clear", self)
        self.connect(self.clearAction, QtCore.SIGNAL("triggered()"), self.clearRecentAction)
        self.ui.menuOpen_Recent.addAction(self.clearAction)
        self.ui.menuOpen_Recent.setEnabled(False)
        self.updateRecentAction()

    def updateRecentAction(self):
        """
        Update recent actions of Open Recent Files with names of recentely opened files
        """
        if (not len(self.ui.menuOpen_Recent.actions())):
            self.createRecentAction()
        files = World.settings.value("recentFileList").toStringList()
        if (files.count() > 0):
            self.ui.menuOpen_Recent.setEnabled(True)
        numRecentFiles = min(files.count(), World.MaxRecentFiles)
        for i in range(numRecentFiles):
            self.recentaction[i].setText(self.tr("&" + str(i+1) + ": ") + files[i])
            self.recentaction[i].setData(QtCore.QVariant(files[i]))
            self.recentaction[i].setVisible(True)

        for j in range(numRecentFiles, World.MaxRecentFiles):
            self.recentaction[j].setVisible(False)
        # remove Open action from toolbar, and add menu Open_Recent action to toolbar
        self.addOpenToBar()

    def closeEvent(self, event):
        """
        @param QCloseEvent Object: received close event when closing mainwindows
        """
        self.dockTUview.emitTargetChanged()
        self.dockComment.emitCommentChanged()
        QtGui.QMainWindow.closeEvent(self, event)
        if (self.operator.isModified()):
            if (self.fileaction.clearedModified(self)):
                self.operator.setModified(False)
                event.accept()
            else:
                event.ignore()
        # remember last geometry
        World.settings.setValue("lastGeometry", QtCore.QVariant(self.geometry()))
        
        # remember last state
        state = self.saveState(1)
        World.settings.setValue("MainWindowState", QtCore.QVariant(state))
        World.settings.setValue("TuViewHidden", QtCore.QVariant(self.dockTUview.isHidden()))
        
    def setTitle(self, filename):
        """
        set the title of program.
        @param filename: a filename with full path, type as string.
        """
        if (filename):
            self.setWindowTitle("%s - %s" % (filename, World.settingApp))
            self.prependOpenRecent(filename)
        else:
            self.setWindowTitle(World.settingApp)
    
    def toggleFirstLastUnit(self, atFirst, atLast):
        """set enable/disable first, previous, next, and last unit buttons
        @param atFirst: bool indicates that the unit is at first place
        @param atLast: bool indicates that the unit is at last place
        """
        self.ui.actionFirst.setDisabled(atFirst)
        self.ui.actionPrevious.setDisabled(atFirst)
        self.ui.actionNext.setDisabled(atLast)
        self.ui.actionLast.setDisabled(atLast)
    
    def searchNext(self):
        """Find Next from submenu """
        self.operator.searchNext()
        self.findBar.ui.lineEdit.setFocus()
##        self.findBar.ui.findPrevious.setEnabled(True)
##        self.ui.actionFindPrevious.setEnabled(True)
    
    def searchPrevious(self):
        """Find Previous from submenu."""
        self.operator.searchPrevious()
        self.findBar.ui.lineEdit.setFocus()
##        self.findBar.ui.findNext.setEnabled(True)
##        self.ui.actionFindNext.setEnabled(True)
        
##    def findStatus(self, text):
##        """
##        Disable Find Next or Previous Button if the search reach the end of file.
##        @param text: a string to decide which button should be diabled.
##        """
####        self.Catalog.setReachedEnd()
##        if (text == "Next"):
##            self.findBar.ui.findNext.setDisabled(True)
##            self.ui.actionFindNext.setDisabled(True)
##        elif (text == "Previous"):
##            self.findBar.ui.findPrevious.setDisabled(True)
##            self.ui.actionFindPrevious.setDisabled(True)
        
    def focusChanged(self, oldWidget, newWidget):
        if (oldWidget):
            self.disconnect(oldWidget, QtCore.SIGNAL("copyAvailable(bool)"), self.enableCopyCut)
            self.disconnect(oldWidget, QtCore.SIGNAL("undoAvailable(bool)"), self.enableUndo)
            self.disconnect(oldWidget, QtCore.SIGNAL("redoAvailable(bool)"), self.enableRedo)
            # cut, copy and paste in oldWidget
            if (callable(getattr(oldWidget, "cut", None))):
                self.disconnect(self.ui.actionCut, QtCore.SIGNAL("triggered()"), oldWidget, QtCore.SLOT("cut()"))

            if (callable(getattr(oldWidget, "copy", None))):
                self.disconnect(self.ui.actionCopy, QtCore.SIGNAL("triggered()"), oldWidget, QtCore.SLOT("copy()"))

            if (callable(getattr(oldWidget, "paste", None))):
                self.disconnect(self.ui.actionPaste, QtCore.SIGNAL("triggered()"), oldWidget, QtCore.SLOT("paste()"))
            # undo, redo and selectAll in oldWidget
            if (callable(getattr(oldWidget, "document", None))):
                self.disconnect(self.ui.actionUndo, QtCore.SIGNAL("triggered()"), oldWidget.document(), QtCore.SLOT("undo()"))
                self.disconnect(self.ui.actionRedo, QtCore.SIGNAL("triggered()"), oldWidget.document(), QtCore.SLOT("redo()"))

        if (newWidget):
            self.connect(newWidget, QtCore.SIGNAL("copyAvailable(bool)"), self.enableCopyCut)
            self.connect(newWidget, QtCore.SIGNAL("undoAvailable(bool)"), self.enableUndo)
            self.connect(newWidget, QtCore.SIGNAL("redoAvailable(bool)"), self.enableRedo)
            # cut, copy and paste in newWidget
            if (callable(getattr(newWidget, "cut", None))):
                self.connect(self.ui.actionCut, QtCore.SIGNAL("triggered()"), newWidget, QtCore.SLOT("cut()"))

            if (callable(getattr(newWidget, "copy", None))):
                self.connect(self.ui.actionCopy, QtCore.SIGNAL("triggered()"), newWidget, QtCore.SLOT("copy()"))

            if (callable(getattr(newWidget, "paste", None))):
                self.connect(self.ui.actionPaste, QtCore.SIGNAL("triggered()"), newWidget, QtCore.SLOT("paste()"))
                if (callable(getattr(newWidget, "isReadOnly", None))):
                    self.ui.actionPaste.setEnabled(not newWidget.isReadOnly())
                else:
                    self.ui.actionPaste.setEnabled(True)
            else:
                self.ui.actionPaste.setEnabled(False)

            if (callable(getattr(newWidget, "textCursor", None))):
                hasSelection = newWidget.textCursor().hasSelection()
                self.enableCopyCut(hasSelection)
            else:
                self.enableCopyCut(False)

            #it will not work for QLineEdits
            if (callable(getattr(newWidget, "document", None))):
                undoAvailable = newWidget.document().isUndoAvailable()
                redoAvailable = newWidget.document().isRedoAvailable()
                self.enableUndo(undoAvailable)
                self.enableRedo(redoAvailable)
                self.connect(self.ui.actionUndo, QtCore.SIGNAL("triggered()"), newWidget.document(), QtCore.SLOT("undo()"))
                self.connect(self.ui.actionRedo, QtCore.SIGNAL("triggered()"), newWidget.document(), QtCore.SLOT("redo()"))
            else:
                self.enableUndo(False)
                self.enableRedo(False)
    
    def addFuzzyIcon(self, unit):
        self.ui.statusbar.removeWidget(self.statusfuzzy)
        if hasattr(unit, "x_editor_state"):
            if (unit.x_editor_state & World.fuzzy):
                self.statusfuzzy.setVisible(True)
                self.ui.statusbar.addWidget(self.statusfuzzy)
    
    def openFile(self, filename):
        """
        Open filename and prepend it in recent list.
        @param filename: file to open.
        """
        closed = self.closeFile()
        if (closed):
            if (self.operator.getUnits(filename)):
                self.fileaction.setFileProperty(filename)
                self.setStatusForFile(filename)
                self.prependOpenRecent(filename)
                self.clearBookmarks()
        self.show()
    
    def closeFile(self, force = False):
        """
        Return True when successfully close file, else return False.
        @param force: bool whether to check if content is modified.
        """
        self.dockTUview.emitTargetChanged()
        self.dockComment.emitCommentChanged()
        
        if (force) or (not self.operator.isModified()):
            self.setStatusForFile(None)
            self.operator.closeFile()
            self.statuslabel.setText("")
            self.ui.actionSave.setEnabled(False)
            self.ui.actionAuto_translate.setEnabled(False)
            self.operator.setModified(False)
        elif (self.operator.isModified()):
            if self.fileaction.clearedModified(self):
                self.closeFile(True)
            else:
                return False
        return True
    
    def setStatusForFile(self, filename):
        """
        Enable/disable buttons according to availability of filename.
        @param filename: filename to set title and determine enable/disable.
        """
        self.ui.actionSave.setEnabled(False)
        
        value = bool(filename)
        self.setTitle(filename)
        self.ui.action_Close.setEnabled(value)
        self.ui.actionSaveas.setEnabled(value)
        self.ui.actionPaste.setEnabled(value)
        self.ui.actionFindNext.setEnabled(value)
        self.ui.actionFindPrevious.setEnabled(value)
        self.ui.actionFind.setEnabled(value)
        self.ui.actionReplace.setEnabled(value)
        self.ui.actionCopySource2Target.setEnabled(value)
        self.ui.actionEdit_Header.setEnabled(value)
        self.ui.actionGoTo.setEnabled(value)
        self.ui.actionAddBookmarks.setEnabled(value)
        self.ui.actionToggleFuzzy.setEnabled(value)
        self.ui.actionClear_Fuzzies.setEnabled(value)
        self.ui.actionFilterFuzzy.setEnabled(value)
        self.ui.actionFilterTranslated.setEnabled(value)
        self.ui.actionFilterUntranslated.setEnabled(value)
        
        # disconnect and reconnect fuzzy, translated, and untranslated button actions.
        self.disconnect(self.ui.actionFilterFuzzy, QtCore.SIGNAL("toggled(bool)"), self.operator.filterFuzzy)
        self.disconnect(self.ui.actionFilterTranslated, QtCore.SIGNAL("toggled(bool)"), self.operator.filterTranslated)
        self.disconnect(self.ui.actionFilterUntranslated, QtCore.SIGNAL("toggled(bool)"), self.operator.filterUntranslated)
        self.ui.actionFilterFuzzy.setChecked(True)
        self.ui.actionFilterTranslated.setChecked(True)
        self.ui.actionFilterUntranslated.setChecked(True)
        self.connect(self.ui.actionFilterFuzzy, QtCore.SIGNAL("toggled(bool)"), self.operator.filterFuzzy)
        self.connect(self.ui.actionFilterTranslated, QtCore.SIGNAL("toggled(bool)"), self.operator.filterTranslated)
        self.connect(self.ui.actionFilterUntranslated, QtCore.SIGNAL("toggled(bool)"), self.operator.filterUntranslated)
        
        #TODO: it is enable unless Automatically lookup translation in TM is checked.
        self.ui.actionCopySearchResult2Target.setEnabled(value)
        self.findBar.toggleViewAction().setVisible(value)
        self.ui.actionAuto_translate.setEnabled(True)
        self.table.ui.tblTM.clear()
        self.table.ui.tblTM.setRowCount(0)
        self.table.ui.tblTM.setEnabled(value)
        self.tableGlossary.ui.tblGlossary.setEnabled(value)
    
    def addOpenToBar(self):
        '''add Open action or menu Open_Recent action to toolbar
        
        '''
        if (hasattr(self, "actionOpen")):
            self.ui.toolFile.removeAction(self.actionOpen)
        if not self.ui.menuOpen_Recent.isEnabled():
            self.actionOpen = self.ui.actionOpen
        else:
            self.actionOpen = self.ui.menuOpen_Recent.menuAction()
            self.disconnect(self.actionOpen, QtCore.SIGNAL("triggered()"), self.fileaction.openFile)
            self.connect(self.actionOpen, QtCore.SIGNAL("triggered()"), self.fileaction.openFile)
        self.actionOpen.setToolTip(self.tr("Open"))
        self.actionOpen.setWhatsThis("<h3>Open a file</h3>You will be asked for the name of a file to be opened and open recent file in an editor window.") 
        self.ui.toolFile.insertAction(self.ui.actionSave, self.actionOpen)
        
    def toggleTUviewTermSig(self):
            """Toggle TUview term signal."""
            if self.tableGlossary.toggleViewAction().isChecked():
                self.connect(self.dockTUview, QtCore.SIGNAL("term"), self.operator.emitGlossaryCandidates)
                self.dockTUview.emitGlossaryWords()
            else:
                self.disconnect(self.dockTUview, QtCore.SIGNAL("term"), self.operator.emitGlossaryCandidates)
    
    def setSaveEnabled(self):
        """
        Set save button enabled immediatly as text, fuzzy status has changed.
        """
        if (not self.ui.actionSave.isEnabled()):
            self.ui.actionSave.setEnabled(True)
    
    def saveFile(self):
        """
        Call fileaction.save() and set save button disable.
        """
        self.fileaction.save()
        self.ui.actionSave.setEnabled(False)
    
    def updateStatistic(self, filename):
        """
        Call Operator.saveStoreToFile() to return signal of filename
        """
        self.Catalog.updateFileStatus(filename)

    def setStatus(self, statusList):
        """
        Set status that contain current, total, untranslated, translated to the current file.
        """
        numUntran = statusList[0]
        numFuzzy = statusList[1]
        numTran = statusList[2]
        current = statusList[3]
        numTotal = numUntran + numFuzzy + numTran
        
        statusString = "Current: " + str(current) +"/" + str(numTotal) + "  |  " + \
                "Untranslated: " + str(numUntran) + "  |  " + \
                "Fuzzy: " +  str(numFuzzy) + "  |  " + \
                "Translated: " +  str(numTran)
                
        self.statuslabel.setText(statusString)
    
    def displayTempMessage(self, message):
        """
        display a quick message for 5 seconds in status bar.
        """
        if (message == "reachedEnd"):
            self.message = self.tr("Search has reached the end.")
            self.ui.statusbar.showMessage(self.message, 3000)
        elif (message == "notFound"):
            self.message = self.tr("Search was not found.")
            self.ui.statusbar.showMessage(self.message, 3000)
        elif (message == "found"):
            if (hasattr(self, "message")) and (self.message != ""):
                self.ui.statusbar.showMessage("", 0000)
            self.message = ""

def main(inputFile = None):
    # set the path for QT in order to find the icons
    if __name__ == "__main__":
        QtCore.QDir.setCurrent(os.path.join(sys.path[0], "../ui"))
    else:
#        try:
#            QtCore.QDir.setCurrent(os.path.join(sys.path[0], "../images"))
#        except Exception, e:
        import distutils.sysconfig
        packagesdir = distutils.sysconfig.get_python_lib(prefix = "/usr/local")
        QtCore.QDir.setCurrent(os.path.join(packagesdir, "pootling", "ui"))
            
    app = QtGui.QApplication(sys.argv)
    editor = MainWindow()
    editor.show()
    
    if (inputFile):
        if os.path.exists(inputFile):
            editor.openFile(inputFile)
        else:
            msg = editor.tr("%1 file name doesn't exist").arg(inputFile)
            QtGui.QMessageBox.warning(editor, editor.tr("File not found") , msg)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
