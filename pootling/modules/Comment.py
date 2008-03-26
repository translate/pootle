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
# This module is working on any comments of current TU.

from PyQt4 import QtCore, QtGui
from pootling.ui.Ui_Comment import Ui_frmComment
import pootling.modules.World as World
from translate.storage import po
from translate.storage import xliff
from pootling.modules.highlighter import Highlighter

class CommentDock(QtGui.QDockWidget):
    """
    Code for Comment View
    
    @signal commentChanged(): emitted when Comment view's document is modified.
    @signal copyAvailable(bool): emitted when text is selected or de-selected in the Comment view.
    @signal textChanged(): emitted everytime Comment view's document is modified.
    """
    
    def __init__(self, parent):
        QtGui.QDockWidget.__init__(self, parent)
        self.setObjectName("commentDock")
        self.setWindowTitle(self.tr("Comment"))
        self.form = QtGui.QWidget(self)
        self.ui = Ui_frmComment()
        self.ui.setupUi(self.form)
        self.setWidget(self.form)
        self.ui.txtLocationComment.hide()
        # create highlighter
        self.highlighter = Highlighter(self.ui.txtTranslatorComment)
        self.applySettings()
        
##        self.ui.txtTranslatorComment.focusOutEvent = self.customFocusOutEvent
##        
##    def customFocusOutEvent(self, e):
##        """
##        subclass of focusOutEvent of txtTranslatorComment
##        """
##        self.emitCommentChanged()
##        return QtGui.QTextEdit.focusOutEvent(self.ui.txtTranslatorComment, e)
    
    def closeEvent(self, event):
        """
        set text of action object to 'show Comment' before closing Comment View
        @param QCloseEvent Object: received close event when closing widget
        """
        QtGui.QDockWidget.closeEvent(self, event)
        self.toggleViewAction().setChecked(False)
    
    def updateView(self, unit):
        """
        Update the comments view
        @param unit: class unit.
        """
        self.viewSetting(unit)
        if (not unit):
            return
        
        self.disconnect(self.ui.txtTranslatorComment, QtCore.SIGNAL("textChanged()"), self.textChanged)
        
        self.emitCommentChanged()
        translatorComment = ""
        locationComment = ""
        translatorComment = unit.getnotes("translator")
        locationComments = unit.getlocations()
        locationComment = "\n".join([location for location in locationComments])
        if (locationComment == ""):
            self.ui.txtLocationComment.hide()
        else:
            self.ui.txtLocationComment.show()
            self.ui.txtLocationComment.setPlainText(locationComment)
        if (unicode(self.ui.txtTranslatorComment.toPlainText()) != unicode(translatorComment)):
            self.ui.txtTranslatorComment.setPlainText(translatorComment)
        
        #move the cursor to the end of sentence.
        cursor = self.ui.txtTranslatorComment.textCursor()
        cursor.setPosition(len(translatorComment or ""))
        self.ui.txtTranslatorComment.setTextCursor(cursor)
        self.currentUnit = unit
        
        self.connect(self.ui.txtTranslatorComment, QtCore.SIGNAL("textChanged()"), self.textChanged)
    
    def textChanged(self):
        """
        @emit textchanged signal for widget that need to update text while typing.
        """
        if (self.ui.txtTranslatorComment.document().isUndoAvailable()):
            text = unicode(self.ui.txtTranslatorComment.toPlainText())
            self.emit(QtCore.SIGNAL("textChanged"), text)
            self.contentDirty = True
    
    def emitCommentChanged(self):
        """
        @emit targetChanged signal if content is dirty.
        """
        if (hasattr(self, "contentDirty") and self.contentDirty) and (hasattr(self, "currentUnit")):
            comment = unicode(self.ui.txtTranslatorComment.toPlainText())
            self.emit(QtCore.SIGNAL("commentChanged"), comment, self.currentUnit)
        self.contentDirty = False
    
    def setSearchString(self, searchString, textField, foundPosition):
        """
        call highlighter.setSearchString()
        @param searchString: string to be searched for
        @param textField: where to search for the searchString, i.e. source, target or comment text box.
        """
        if (textField == World.comment):
            self.highlighter.setSearchString(searchString, foundPosition)
    
    def applySettings(self):
        """ set color and font to txtTranslatorComment"""
        commentColor = World.settings.value("commentColor")
        if (commentColor.isValid()):
            colorObj = QtGui.QColor(commentColor.toString())
            palette = QtGui.QPalette(self.ui.txtTranslatorComment.palette())
            palette.setColor(QtGui.QPalette.Active,QtGui.QPalette.ColorRole(QtGui.QPalette.Text), colorObj)
            palette.setColor(QtGui.QPalette.Inactive,QtGui.QPalette.ColorRole(QtGui.QPalette.Text), colorObj)
            if (self.ui.txtTranslatorComment.isEnabled()):
                self.ui.txtTranslatorComment.setPalette(palette)
            else:
                # we need to enable the widget otherwise it will not use the new palette
                self.ui.txtTranslatorComment.setEnabled(True)
                self.ui.txtTranslatorComment.setPalette(palette)
                self.ui.txtTranslatorComment.setEnabled(False)

        font = World.settings.value("commentFont")
        if (font.isValid()):
            fontObj = QtGui.QFont()
            if (fontObj.fromString(font.toString())):
                self.ui.txtTranslatorComment.setFont(fontObj)
                
    def replaceText(self, textField, position, length, replacedText):
        """replace the string (at position and length) with replacedText in txtTranslatorComment.
        @param textField: where to search for the text, i.e. source, target or comment text box.
        @param position: old string's start point.
        @param length: old string's length.
        @param replacedText: string to replace."""
        if (textField != World.comment):
            return
        text = self.ui.txtTranslatorComment.toPlainText()
        text.replace(position, length, replacedText)
        self.ui.txtTranslatorComment.setPlainText(text)
        self.ui.txtTranslatorComment.document().setModified()
        self.emitCommentChanged()
    
    def viewSetting(self, unit):
        """Set the view status of txtLocationComment and txtLocationComment.
        @param unit: if not unit, hide location comment textbox and clear the translator comment box.
        """
        bool = (unit and True or False)
        self.ui.txtTranslatorComment.setEnabled(bool)
        if (bool == False):
            self.ui.txtLocationComment.hide()
            self.ui.txtTranslatorComment.clear()
            return

if __name__ == "__main__":
    import sys, os
    # set the path for QT in order to find the icons
    QtCore.QDir.setCurrent(os.path.join(sys.path[0], "..", "ui"))
    app = QtGui.QApplication(sys.argv)
    comment = CommentDock(None)
    comment.show()
    sys.exit(app.exec_())
