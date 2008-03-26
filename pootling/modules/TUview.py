#!/usr/bin/python
# -*- coding: utf-8 -*-

#Copyright (c) 2006 - 2007 by The WordForge Foundation
#                       www.wordforge.org
#
# This program is free sofware; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your op tion) any later version.
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
from pootling.ui.Ui_TUview import Ui_TUview
from pootling.modules import World
from pootling.modules.highlighter import Highlighter

SHOWTIP = 1
CONTEXTMENU = 2

class TUview(QtGui.QDockWidget):
    """
    Code for TUview.
    
    @signal scrollToRow: emited with value as row start from 0.
    @signal term: emited with word found in self.sourceHighlighter.glossaryWords
    @signal targetChanged: emitted content in textTarget is dirty.
    """
    def __init__(self, parent):
        QtGui.QDockWidget.__init__(self, parent)
        self.setObjectName("detailDock")
        self.setWindowTitle(self.tr("Detail"))
        self.form = QtGui.QWidget(self)
        self.ui = Ui_TUview()
        self.ui.setupUi(self.form)
        self.setWidget(self.form)
        self.setFeatures(QtGui.QDockWidget.DockWidgetClosable)
        self.ui.lblComment.hide()
        self.applySettings()
        self.connect(self.ui.fileScrollBar, QtCore.SIGNAL("valueChanged(int)"), self.emitCurrentIndex)
        
        self.connect(self.ui.tabWidgetSource, QtCore.SIGNAL("currentChanged(int)"), self.sourceIndexChanged)
        self.connect(self.ui.tabWidgetTarget, QtCore.SIGNAL("currentChanged(int)"), self.targetIndexChanged)
        
        # create highlighter
        self.sourceLength = 0
        
        self.sourceHighlighter = Highlighter(self.ui.txtSource)
        self.targetHighlighter = Highlighter(self.ui.txtTarget)
        
        # subclass of event
        self.ui.txtSource.contextMenuEvent = self.customContextMenuEvent
        
        self.ui.txtSource.installEventFilter(self)

        self.contentDirty = False

    def sourceIndexChanged(self, int):
        """
        Slot to receive currentChanged signal when switching source tab.
        
        @param int: the index of the tab, type as int.
        """
        textbox = self.ui.tabWidgetSource.widget(int)
        try:
            source = self.sourceStrings[int]
        except IndexError:
            source = ""
        textbox.setPlainText(source)
    
    def targetIndexChanged(self, int):
        """
        Slot to receive currentChanged signal when switching target tab.
        
        @param int: the index of the tab, type as int.
        """
        textbox = self.ui.tabWidgetTarget.widget(int)
        try:
            target = self.targetStrings[int]
        except IndexError:
            target = ""
        self.emitTargetChanged()
        textbox.setPlainText(target)
        
    def eventFilter(self, obj, event):
        """
        Subclass of eventFilter.
        
        @param obj: an obj whose event will be filtered.
        @param event: type as QEvent.
        """
        if (obj == self.ui.txtSource):
            if (event.type() == QtCore.QEvent.ToolTip):
                """
                Request a tooltip for word in position pos of txtSource.
                """
                self.requestAction = SHOWTIP
                self.globalPos = event.globalPos()
                self.emitTermRequest(event.pos())
                return True
            else:
                return False
        else:
            return self.eventFilter(obj, event)
    
    def customContextMenuEvent(self, e):
        """
        Request a context menu for word in position pos of txtSource.
        
        @param e: type as QContextMenuEvent
        """
        self.requestAction = CONTEXTMENU
        self.copyMenu()
        self.globalPos = e.globalPos()
        self.emitTermRequest(e.pos())
        
    def copyMenu(self):
        """
        Create a copy context menu.
        """
        if (self.requestAction == CONTEXTMENU):
            textCursor = self.ui.txtSource.textCursor()
            selected = textCursor.selectedText()
            if selected:
                menu = QtGui.QMenu()
                menuAction = menu.addAction(unicode(self.tr("copy")))
                menuAction.setData(QtCore.QVariant(selected))
                self.connect(menuAction, QtCore.SIGNAL("triggered()"), self.copyTranslation)
                menu.exec_(QtGui.QCursor.pos())
    
    def popupTerm(self, candidates):
        """
        Popup menu or show tooltip of glossary word's translation.
        
        @param candidates: as list of units.
        """
        if (not candidates):
            return
        
        if (self.requestAction == CONTEXTMENU):
            menu = QtGui.QMenu()
            text = self.ui.txtTarget.toPlainText()
            textCursor = self.ui.txtSource.textCursor()
            selected = textCursor.selectedText()
            if selected:
                self.copyMenu()
                return
                
            for candidate in candidates:
#                if selected and (str(selected).lower() == str(candidate.source).lower()) or not selected:
                srcCopy = unicode(self.tr("Copy \"%s\" to clipboard.")) % unicode(candidate.source)
                menuAction = menu.addAction(srcCopy)
                menuAction.setData(QtCore.QVariant(candidate.source))
                self.connect(menuAction, QtCore.SIGNAL("triggered()"), self.copyTranslation)
            
                strCopy = unicode(self.tr("Copy \"%s\" to clipboard.")) % unicode(candidate.target)
                menuAction = menu.addAction(strCopy)
                menuAction.setData(QtCore.QVariant(candidate.target))
                self.connect(menuAction, QtCore.SIGNAL("triggered()"), self.copyTranslation)
                
                expression = QtCore.QRegExp(candidate.source, QtCore.Qt.CaseInsensitive)
                index = text.indexOf(expression)
                
                strReplaceCursor = unicode(self.tr("Copy \"%s\" to cusor position in target.")) % (unicode(candidate.target))
                menuAction = menu.addAction(strReplaceCursor)
                menuAction.setData(QtCore.QVariant([candidate.target]))
                self.connect(menuAction, QtCore.SIGNAL("triggered()"), self.replaceTranslationInCursor)
                    
                if (index >= 0):
                    length = expression.matchedLength()
                    cText = expression.capturedTexts()[0]
                    strReplace = unicode(self.tr("Replace \"%s\" with \"%s\" in target.")) % (unicode(cText), unicode(candidate.target))
                    menuAction = menu.addAction(strReplace)
                    menuAction.setData(QtCore.QVariant([cText, candidate.target]))
                    self.connect(menuAction, QtCore.SIGNAL("triggered()"), self.replaceTranslation)

            menu.exec_(self.globalPos)
            self.disconnect(menuAction, QtCore.SIGNAL("triggered()"), self.copyTranslation)
        
        elif (self.requestAction == SHOWTIP):
            tips = ""
            for candidate in candidates:
                tips += candidate.target + "\n"
            tips = tips[:-1]
            QtGui.QToolTip.showText(self.globalPos, tips)
    
    def copyTranslation(self):
        """
        Copy self.sender().data() to clipboard.
        """
        # TODO: do not use QLineEdit
        text = self.sender().data().toString()
        lineEdit = QtGui.QLineEdit(text)
        lineEdit.selectAll()
        lineEdit.copy()
    
    def replaceTranslation(self):
        """
        Replace self.sender().data()[0] with self.sender().data()[1]
        in txtTarget.
        """
        source, target = self.sender().data().toStringList()
        if (source.toLower() == target.toLower()):
            return
        text = self.ui.txtTarget.toPlainText()
        expression = QtCore.QRegExp(source, QtCore.Qt.CaseInsensitive)
        index = text.indexOf(expression)
        while (index >= 0):
            length = expression.matchedLength()
            text.replace(index, length, target)
            index = text.indexOf(expression)
        self.setTargetText(text)
        self.ui.txtTarget.setFocus()

    def replaceTranslationInCursor(self, replaceText=""):
        """
        Copy self.sender().data() to cusor position​ in textTarget.
        """
        text = self.ui.txtTarget.toPlainText()
        if (replaceText == ""):
            cText =  self.sender().data().toStringList()[0]
        else:
            cText = replaceText
        cursor = self.ui.txtTarget.textCursor()
        cursor = cursor.position()
        if (len(text) <= 0):
            text = cText
            self.setTargetText(cText)
        elif (cursor == len(text)):
            text = text + cText
            self.setTargetText(text)
        else:
            text = text[:cursor] + cText + text[cursor:]
            self.setTargetText(text)
        self.ui.txtTarget.setFocus()
        cursorPost = len(text[:cursor] + cText)
        cursor = self.ui.txtTarget.textCursor()
        cursor.setPosition(cursorPost)
        self.ui.txtTarget.setTextCursor(cursor)
        
    def emitTermRequest(self, pos):
        """
        Find word in txtSource from position pos, and emit lookupTerm signal.
        """
        text = self.ui.txtSource.toPlainText()
        if (not text):
            return
        glossaryWords = self.sourceHighlighter.glossaryWords
        cursor = self.ui.txtSource.cursorForPosition(pos)
        position = cursor.position()
        # first try wordWithSpace
        withSpace = "\\b(\\w+\\s\\w+)\\b"
        wordWithSpace = QtCore.QRegExp(withSpace)
        index = text.lastIndexOf(wordWithSpace, position)
        length = wordWithSpace.matchedLength()
        termWithSpace = unicode(wordWithSpace.capturedTexts()[0])
        if (termWithSpace in glossaryWords):
            self.emit(QtCore.SIGNAL("lookupTerm"), termWithSpace)
        else:
            withoutSpace = "\\b(\\w+)\\b"
            wordWithoutSpace = QtCore.QRegExp(withoutSpace)
            # then wordWithoutSpace
            index = text.lastIndexOf(wordWithoutSpace, position)
            length = wordWithoutSpace.matchedLength()
            termWithoutSpace = unicode(wordWithoutSpace.capturedTexts()[0])
            if (termWithoutSpace in glossaryWords):
                self.emit(QtCore.SIGNAL("lookupTerm"), termWithoutSpace)
    
    def setPattern(self, patternList):
        """
        call highlighter.setPattern()
        
        @param patternList: a list of pattern 
        """
        self.sourceHighlighter.setPattern(patternList)
    
    def setSearchString(self, searchString, textField, foundPosition):
        """
        call highlighter.setSearchString()
        """
        if (textField == World.source):
            self.sourceHighlighter.setSearchString(searchString, foundPosition)
            self.targetHighlighter.setSearchString("", 0)
        elif (textField == World.target):
            self.targetHighlighter.setSearchString(searchString, foundPosition)
            self.sourceHighlighter.setSearchString("", 0)
    
    def setHighlightGlossary(self, bool):
        """
        call highlighter.setHighlightGlossary()
        """
        self.sourceHighlighter.setHighlightGlossary(bool)
        self.sourceHighlighter.refresh()
        self.emitGlossaryWords()
    
    def closeEvent(self, event):
        """
        set text of action object to 'show Detail' before closing TUview.
        
        @param QCloseEvent Object: received close event when closing widget
        """
        QtGui.QDockWidget.closeEvent(self, event)
        self.toggleViewAction().setChecked(False)
        
    
    def setScrollbarValue(self, value):
        """
        @param value: the new value for the scrollbar.
        """
        if (value < 0):
            value = 0
        self.disconnect(self.ui.fileScrollBar, QtCore.SIGNAL("valueChanged(int)"), self.emitCurrentIndex)
        self.ui.fileScrollBar.setValue(value)
        self.connect(self.ui.fileScrollBar, QtCore.SIGNAL("valueChanged(int)"), self.emitCurrentIndex)
        self.ui.fileScrollBar.setToolTip("%s / %s" % (value + 1,  self.ui.fileScrollBar.maximum() + 1))
    
    def filterChanged(self, filter, lenFilter):
        """
        Adjust the scrollbar maximum according to lenFilter.
        
        @param filter: helper constants for filtering
        @param lenFilter: len of filtered items.
        """
        self.viewSetting(lenFilter)
        self.ui.fileScrollBar.setMaximum(max(lenFilter - 1, 0))
        self.ui.fileScrollBar.setEnabled(bool(lenFilter))
    
    @QtCore.pyqtSignature("int")
    def emitCurrentIndex(self, value):
        """emit "scrollToRow" signal with value as row start from 0.
        @param value: current row."""
        self.emit(QtCore.SIGNAL("scrollToRow"), value)
    
    def updateView(self, unit):
        """
        Update the text in source and target, set the scrollbar position,
        remove a value from scrollbar if the unit is not in filter.
        Then recalculate scrollbar maximum value.
        
        @param unit: unit class.
        """
        if (not unit):
            return
        self.disconnect(self.ui.txtTarget, QtCore.SIGNAL("textChanged()"), self.emitTextChanged)
        self.ui.txtTarget.setReadOnly(False)
        self.ui.txtTarget.setFocus()
        self.emitTargetChanged()
        
        # set comment
        comment = unit.getcontext()
        comment += unit.getnotes("developer")
        if (comment == ""):
            self.ui.lblComment.hide()
        else:
            self.ui.lblComment.show()
            self.ui.lblComment.setText(unicode(comment))
        
        # set source and target, singular or plural.
        isPlural = unit.hasplural() and (self.nplurals > 1)
        self.ui.sourceStacked.setCurrentIndex((self.nplurals and isPlural) or 0)
        self.ui.targetStacked.setCurrentIndex((self.nplurals and isPlural) or 0)
        if (isPlural):
            # plural
            for i in range(self.ui.tabWidgetSource.count()):
                self.ui.tabWidgetSource.removeTab(0)
            for i in range(self.ui.tabWidgetTarget.count()):
                self.ui.tabWidgetTarget.removeTab(0)
            
            self.sourceStrings = unit.source.strings
            for i in range(len(unit.source.strings)):
                textbox = QtGui.QTextEdit()
                textbox.setReadOnly(True)
                textbox.setDocument(self.ui.txtSource.document())
                self.ui.tabWidgetSource.addTab(textbox, "Plural %d" % (i + 1))
                self.ui.tabWidgetSource.setCurrentIndex(i)
            self.ui.tabWidgetSource.setCurrentIndex(0)
            
            self.targetStrings = unit.target.strings
            for i in range(self.nplurals):
                if (len(self.targetStrings) < self.nplurals):
                    self.targetStrings.append("")
                textbox = QtGui.QTextEdit()
                textbox.setDocument(self.ui.txtTarget.document())
                self.ui.tabWidgetTarget.addTab(textbox, "Plural %d" % (i + 1))
                self.ui.tabWidgetTarget.setCurrentIndex(i)
            self.ui.tabWidgetTarget.setCurrentIndex(0)
        else:
            # singular
            self.sourceStrings = []
            self.targetStrings = []
            if (unicode(unit.source) !=  unicode(self.ui.txtSource.toPlainText())):
                self.ui.txtSource.setPlainText(unit.source)
            if (unicode(unit.target) !=  unicode(self.ui.txtTarget.toPlainText())):
                self.ui.txtTarget.setPlainText(unit.target or "")
                self.setCursorToEnd(self.ui.txtTarget)
        
        # set the scrollbar position
        self.setScrollbarValue(unit.x_editor_row)
        self.connect(self.ui.txtTarget, QtCore.SIGNAL("textChanged()"), self.emitTextChanged)
        
        self.currentUnit = unit
        self.emitGlossaryWords()
        self.emitTargetChanged()
    
    def emitGlossaryWords(self):
        """
        emit term signal with word found in self.sourceHighlighter.glossaryWords
        """
        glossaryWords = self.sourceHighlighter.glossaryWords
        for word in glossaryWords:
            self.emit(QtCore.SIGNAL("term"), word)
    
    def emitTextChanged(self):
        """
        @emit textchanged signal for widget that need to update text while typing.
        """
        if (self.ui.txtTarget.document().isModified()):
            text = unicode(self.ui.txtTarget.toPlainText())
            self.emit(QtCore.SIGNAL("textChanged"), text)
            self.contentDirty = True
    
    def emitTargetChanged(self):
        """
        @emit targetChanged signal if content is dirty 
        with target and currentUnit.
        """
        if (self.contentDirty) and (hasattr(self, "currentUnit")):
            target = self.targetStrings or unicode(self.ui.txtTarget.toPlainText())
            self.emit(QtCore.SIGNAL("targetChanged"), target, self.currentUnit)
        self.contentDirty = False
    
    def source2target(self):
        """
        Copy the text from source to target.
        """
        self.setTargetText(self.ui.txtSource.toPlainText())
        self.ui.txtTarget.setFocus()
        if (World.settings.value("cursorHome", QtCore.QVariant(True)).toBool()):
            self.setCursorToHome(self.ui.txtTarget)
        else:
            self.setCursorToEnd(self.ui.txtTarget)
        
    def translation2target(self, translation):
        """
        Copy the translation from TM to target.
        """
        self.setTargetText(translation)
        self.ui.txtTarget.setFocus()
        self.setCursorToEnd(self.ui.txtTarget)
    
    def replaceText(self, textField, position, length, replacedText):
        """
        replace the string (at position and length) with replacedText in txtTarget.
        
        @param textField: source or target text box.
        @param position: old string's start point.
        @param length: old string's length.
        @param replacedText: string to replace.
        """
        if (textField != World.target):
            return
        text = self.ui.txtTarget.toPlainText()
        text.replace(position, length, replacedText);
        self.ui.txtTarget.setPlainText(text)
    
    def applySettings(self):
        """
        Get settings from World and apply such as font, color, number of
        plural.
        """
        sourceColor = World.settings.value("tuSourceColor")
        if (sourceColor.isValid()):
            colorObj = QtGui.QColor(sourceColor.toString())
            palette = QtGui.QPalette(self.ui.txtSource.palette())
            palette.setColor(QtGui.QPalette.Active,QtGui.QPalette.ColorRole(QtGui.QPalette.Text), colorObj)
            palette.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.ColorRole(QtGui.QPalette.Text), colorObj)
            self.ui.txtSource.setPalette(palette)
        
        targetColor = World.settings.value("tuTargetColor")
        if (targetColor.isValid()):
            colorObj = QtGui.QColor(targetColor.toString())
            palette = QtGui.QPalette(self.ui.txtTarget.palette())
            palette.setColor(QtGui.QPalette.Active,QtGui.QPalette.ColorRole(QtGui.QPalette.Text), colorObj)
            palette.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.ColorRole(QtGui.QPalette.Text), colorObj)
            self.ui.txtTarget.setPalette(palette)
    
        fontObj = QtGui.QFont()
        sourcefont = World.settings.value("tuSourceFont")
        if (sourcefont.isValid() and fontObj.fromString(sourcefont.toString())):
            self.ui.txtSource.setFont(fontObj)
            self.ui.txtSource.setTabStopWidth(QtGui.QFontMetrics(fontObj).width("m"*8))
    
        targetfont = World.settings.value("tuTargetFont")
        if (targetfont.isValid() and fontObj.fromString(targetfont.toString())):
            self.ui.txtTarget.setFont(fontObj)
            self.ui.txtTarget.setTabStopWidth(QtGui.QFontMetrics(fontObj).width("m"*8))
        
        self.nplurals = World.settings.value("nPlural").toInt()[0]
        
    def viewSetting(self, arg = None):
        """
        Set the view to Detail view: scrollbar, 
        
        @param arg: type as list
        """
        
        if (type(arg) is list):
            lenFilter = len(arg)
            self.ui.fileScrollBar.setMaximum(max(lenFilter - 1, 0))
            self.ui.fileScrollBar.setEnabled(bool(lenFilter))
        # value: a bool value just to set the widget visible or not.
        # value = True means there is at leaset a unit.
        value = (arg and True or False)

        if (value == False):
            self.ui.lblComment.clear()
            self.ui.txtSource.clear()
            self.ui.txtTarget.clear()
        self.ui.lblComment.setVisible(value)
        self.ui.sourceStacked.setEnabled(value)
        self.ui.targetStacked.setEnabled(value)
        self.contentDirty = False
        
    def setCursorToHome(self, obj):
        """
        move the obj cursor to the beginning of the first line.
        
        @param obj: QTextEdit object.
        """
        cursor = obj.textCursor()
        cursor.setPosition(0)
        obj.setTextCursor(cursor)
        
    def setCursorToEnd(self, obj):
        """
        move the obj cursor to the end of text.
        
        @param obj: QTextEdit object.
        """
        cursor = obj.textCursor()
        cursor.setPosition(len(obj.toPlainText()))
        obj.setTextCursor(cursor)
    
    def setTargetText(self, text):
        """
        Set text of txtTarget while keep undo history.
        
        @param text: text for txtTarget.
        """
        self.ui.txtTarget.selectAll()
        self.ui.txtTarget.insertPlainText(text)

    
if __name__ == "__main__":
    import sys, os
    # set the path for QT in order to find the icons
    QtCore.QDir.setCurrent(os.path.join(sys.path[0], "..", "ui"))
    app = QtGui.QApplication(sys.argv)
    Form = TUview(None)
    Form.show()
    sys.exit(app.exec_())
