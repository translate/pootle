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

from pootling.modules import World
from PyQt4 import QtCore, QtGui

class Highlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, parent):
        QtGui.QSyntaxHighlighter.__init__(self, parent)
        self.parent = parent
        
        # var format
        self.varFormat = QtGui.QTextCharFormat()
        self.varFormat.setForeground(QtCore.Qt.blue)
        # variables: e.g. &python; %s %1 AppName
        self.vars = "&\\w+;|%\\w+|[A-Z][a-z]+[A-Z][a-z](\\w)+"
        self.varExpression = QtCore.QRegExp(self.vars)
        # tag format
        self.tagFormat = QtGui.QTextCharFormat()
        self.tagFormat.setForeground(QtCore.Qt.darkMagenta)
        # tags: e.g. <b> </ui>
        self.tags = "<\\w+>|</\\w+>"
        self.tagExpression = QtCore.QRegExp(self.tags)
        
        # glossary format
        self.glsFormat = QtGui.QTextCharFormat()
        self.glsFormat.setFontWeight(QtGui.QFont.Bold)
        self.glsFormat.setForeground(QtCore.Qt.darkGreen)
##        self.glsFormat.setUnderlineStyle(QtGui.QTextCharFormat.DotLine)
        self.glsFormat.setFontUnderline(True)
        self.glsFormat.setUnderlineColor(QtCore.Qt.darkGreen)
        self.highlightGlossary = False
        self.glsExpression = None
        self.glossaryWords = []
        
        # search format
        self.searchFormat = QtGui.QTextCharFormat()
        self.searchFormat.setFontWeight(QtGui.QFont.Bold)
        self.searchFormat.setForeground(QtCore.Qt.white)
        self.searchFormat.setBackground(QtCore.Qt.darkMagenta)
        
        self.searchString = None
    
    def highlightBlock(self, text):
        """
        highlight the text according to the self.expression
        @ param text: a document text.
        """
        
        # clear glossaryWords not by rehighlight block.
        if (self.previousBlockState() == -1):
            self.glossaryWords = []
            self.blockWordCount = 0
        self.setCurrentBlockState(0)
        
        if (self.highlightGlossary) and (self.glsExpression):
            glsIndex = text.indexOf(self.glsExpression)
        else:
            glsIndex = -1
        while (glsIndex >= 0):
            # highlight glossary
            if (self.highlightGlossary) and (self.glsExpression):
                length = self.glsExpression.matchedLength()
                self.setFormat(glsIndex, length, self.glsFormat)
                self.glossaryWords.append(unicode(self.glsExpression.capturedTexts()[0]))
                glsIndex = text.indexOf(self.glsExpression, glsIndex + length)
        
        # highlight arguments, variable
        varIndex = text.indexOf(self.varExpression)
        tagIndex = text.indexOf(self.tagExpression)
        while (tagIndex >= 0) or (varIndex >= 0):
            # highlight tag and variable
            length = self.tagExpression.matchedLength()
            self.setFormat(tagIndex, length, self.tagFormat)
            tagIndex = text.indexOf(self.tagExpression, tagIndex + length)
            length = self.varExpression.matchedLength()
            self.setFormat(varIndex, length, self.varFormat)
            varIndex = text.indexOf(self.varExpression, varIndex + length)
        
        # highlight search
        if (self.searchString):
            index = self.foundPosition - self.blockWordCount
            self.setFormat(index, len(self.searchString), self.searchFormat)
            cursor = self.parent.textCursor()
            cursor.setPosition(self.blockWordCount + index)
            self.parent.setTextCursor(cursor)
            captured = unicode(text[index:index + len(self.searchString)])
            if (captured.lower() == self.searchString.lower()):
                self.searchString = None
        
        self.blockWordCount += len(text) + 1
    
    def refresh(self):
        """
        mark contents dirty, to make it rehighlight.
        """
        self.parent.document().markContentsDirty(0, len(self.parent.document().toPlainText()))
    
    def setPattern(self, patternList):
        """
        build self.glsExpression base on given pattern.
        @param patternList: list of string.
        """
        pattern = "\\b(" + "|".join(p for p in patternList) + ")\\b"
        self.glsExpression = QtCore.QRegExp(pattern)
        self.glsExpression.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
    
    def setSearchString(self, searchString, foundPosition):
        """
        set searchString and make document() dirty then it will
        re highlightBlock().
        @param searchString: string to be searched for
        @param foundPosition: Position of found string in the document
        """
        self.searchString = searchString
        self.foundPosition = foundPosition
        self.refresh()
        
    def setHighlightGlossary(self, bool):
        self.highlightGlossary = bool
    
