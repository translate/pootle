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
# This module is working on Preferences


from PyQt4 import QtCore, QtGui
from pootling.ui.Ui_Preference import Ui_frmPreference
from translate.lang import common
import pootling.modules.World as World
import translate.lang.data as data

class Preference(QtGui.QDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.ui = None

    def initUI(self):
        """ get values and display them """
        self.overviewFont = self.getFont(self.widget[0])
        self.setCaption(self.ui.lblOverView, self.overviewFont)
        self.tuSourceFont = self.getFont(self.widget[1])
        self.setCaption(self.ui.lblSource, self.tuSourceFont)
        self.tuTargetFont = self.getFont(self.widget[2])
        self.setCaption(self.ui.lblTarget, self.tuTargetFont )
        self.commentFont = self.getFont(self.widget[3])
        self.setCaption(self.ui.lblComment, self.commentFont)
        self.overviewHeaderFont = self.getFont(self.widget[4])
        self.setCaption(self.ui.lblOverViewHeader, self.overviewHeaderFont)
        self.TMFont = self.getFont(self.widget[5])
        self.setCaption(self.ui.lblTM, self.TMFont)
        self.glossaryFont = self.getFont(self.widget[6])
        self.setCaption(self.ui.lblGlossary, self.glossaryFont)
        
        
        self.overviewColorObj = self.getColor(self.widget[0])
        self.setTextColor(self.ui.lblOverView, self.overviewColorObj)
        self.tuSourceColorObj = self.getColor(self.widget[1])
        self.setTextColor(self.ui.lblSource, self.tuSourceColorObj)
        self.tuTargetColorObj = self.getColor(self.widget[2])
        self.setTextColor(self.ui.lblTarget, self.tuTargetColorObj)
        self.commentColorObj = self.getColor(self.widget[3])
        self.setTextColor(self.ui.lblComment, self.commentColorObj)
        self.TMColorObj = self.getColor(self.widget[5])
        self.setTextColor(self.ui.lblTM, self.TMColorObj)
        self.glossaryColorObj = self.getColor(self.widget[6])
        self.setTextColor(self.ui.lblGlossary, self.glossaryColorObj)
        
        self.ui.UserName.setText(World.settings.value("UserName").toString())
        self.ui.EmailAddress.setText(World.settings.value("EmailAddress").toString())
        self.ui.lineFullLang.setText(World.settings.value("FullLanguage").toString())
        self.ui.cbxLanguageCode.setEditText(World.settings.value("Code").toString())
        self.ui.SupportTeam.setText(World.settings.value("SupportTeam").toString())
        self.ui.spinBox.setValue(World.settings.value("nPlural").toInt()[0])
        self.ui.lineEqaution.setText(World.settings.value("equation").toString())
        checkState = World.settings.value("headerAuto", QtCore.QVariant(True))
        if (checkState.toBool()):
            self.ui.chkHeaderAuto.setCheckState(QtCore.Qt.Checked)
        else:
            self.ui.chkHeaderAuto.setCheckState(QtCore.Qt.Unchecked)
        
        checkCurHome = World.settings.value("cursorHome", QtCore.QVariant(True))
        if (checkCurHome.toBool()):
            self.ui.chkCursorHome.setCheckState(QtCore.Qt.Checked)
        else:
            self.ui.chkCursorHome.setCheckState(QtCore.Qt.Unchecked)
            
        # TODO: set checkstateOptions of TM preference here when applicaiton is running
        TMpreference = World.settings.value("TMpreference").toInt()[0]
        self.ui.chbAutoTranslate.setChecked(TMpreference & 1 and True or False)
        self.ui.chbIgnoreFuzzy.setChecked(TMpreference & 2 and True or False)
        self.ui.chbAddTraslation.setChecked(TMpreference & 4 and True or False)
        
        GlossaryPreference = World.settings.value("GlossaryPreference").toInt()[0]
        self.ui.chbAutoIdentTerm.setChecked(GlossaryPreference & 1 and True or False)
        self.ui.chbChangeTerm.setChecked(GlossaryPreference & 2 and True or False)
        self.ui.chbMatchTerm.setChecked(GlossaryPreference & 4 and True or False)
        self.ui.chbDetectTerm.setChecked(GlossaryPreference & 8 and True or False)
        self.ui.chbAddNewTerm.setChecked(GlossaryPreference & 16 and True or False)
        self.ui.chbSuggestTranslation.setChecked(GlossaryPreference & 32 and True or False)
        
        self.connect(self.ui.okButton, QtCore.SIGNAL("clicked()"), self.accept)
        self.connect(self.ui.cancelButton, QtCore.SIGNAL("clicked()"), self.reject)
        
        #tempory hide some features that will be included in the next version.
        #Glossary
        self.ui.chbChangeTerm.hide()
        self.ui.chbMatchTerm.hide()
        self.ui.chbAddNewTerm.hide()
        self.ui.chbSuggestTranslation.hide()
        self.ui.chbDetectTerm.hide()
        #TM
        self.ui.chbEditTraslation.hide()
        self.ui.chbAddTraslation.hide()
        
    def accepted(self):
        """ slot ok pressed """
        self.rememberFont(self.widget[0], self.overviewFont)
        self.rememberFont(self.widget[1], self.tuSourceFont)
        self.rememberFont(self.widget[2], self.tuTargetFont)
        self.rememberFont(self.widget[3], self.commentFont)
        self.rememberFont(self.widget[4], self.overviewHeaderFont)
        self.rememberFont(self.widget[5], self.TMFont)
        self.rememberFont(self.widget[6], self.glossaryFont)

        self.rememberColor(self.widget[0], self.overviewColorObj)
        self.rememberColor(self.widget[1], self.tuSourceColorObj)
        self.rememberColor(self.widget[2], self.tuTargetColorObj)
        self.rememberColor(self.widget[3], self.commentColorObj)
        self.rememberColor(self.widget[5], self.TMColorObj)
        self.rememberColor(self.widget[6], self.glossaryColorObj)

        World.settings.setValue("UserName", QtCore.QVariant(self.ui.UserName.text()))
        World.settings.setValue("EmailAddress", QtCore.QVariant(self.ui.EmailAddress.text()))
        World.settings.setValue("FullLanguage", QtCore.QVariant(self.ui.lineFullLang.text()))
        World.settings.setValue("Code", QtCore.QVariant(self.ui.cbxLanguageCode.currentText()))
        World.settings.setValue("SupportTeam", QtCore.QVariant(self.ui.SupportTeam.text()))
        World.settings.setValue("nPlural", QtCore.QVariant(self.ui.spinBox.value()))
        World.settings.setValue("equation", QtCore.QVariant(self.ui.lineEqaution.text()))
        World.settings.setValue("headerAuto", QtCore.QVariant(self.ui.chkHeaderAuto.checkState() == QtCore.Qt.Checked))
        World.settings.setValue("cursorHome", QtCore.QVariant(self.ui.chkCursorHome.checkState() == QtCore.Qt.Checked))
        TMpreference = self.setTMOptions()
        World.settings.setValue("TMpreference", QtCore.QVariant(TMpreference))
        GlossaryPreference = self.setGlossaryOptions()
        World.settings.setValue("GlossaryPreference", QtCore.QVariant(GlossaryPreference))
        self.emit(QtCore.SIGNAL("settingsChanged"))

    def rememberFont(self, obj, fontObj):
        """ remember Font in Qsettings
        @param obj: input as string
        @param fontObj: stored font"""
        World.settings.setValue(str(obj + "Font"), QtCore.QVariant(fontObj.toString()))

    def rememberColor(self, obj, colorObj):
        """ remember Color in Qsettings
        @param obj: input as string
        @param colorObj: stored color"""
        World.settings.setValue(str(obj + "Color"), QtCore.QVariant(colorObj.name()))

    def fontOverview(self):
        """ slot to open font selection dialog """
        self.overviewFont = self.setFont(self.widget[0])
        self.setCaption(self.ui.lblOverView, self.overviewFont)
        
    def fontSource(self):
        """ slot to open font selection dialog """
        self.tuSourceFont = self.setFont(self.widget[1])
        self.setCaption(self.ui.lblSource, self.tuSourceFont)
        
    def fontTarget(self):
        """ slot to open font selection dialog """
        self.tuTargetFont = self.setFont(self.widget[2])
        self.setCaption(self.ui.lblTarget, self.tuTargetFont)

    def fontComment(self):
        """ slot to open font selection dialog """
        self.commentFont = self.setFont(self.widget[3])
        self.setCaption(self.ui.lblComment, self.commentFont)
        
    def fontOverviewHeader(self):
        """ slot to open font selection dialog """
        self.overviewHeaderFont = self.setFont(self.widget[4])
        self.setCaption(self.ui.lblOverViewHeader, self.overviewHeaderFont)
        
    def fontTM(self):
        """ slot to open font selection dialog """
        self.TMFont = self.setFont(self.widget[5])
        self.setCaption(self.ui.lblTM, self.TMFont)
    
    def fontGlossary(self):
        """ slot to open font selection dialog """
        self.glossaryFont = self.setFont(self.widget[6])
        self.setCaption(self.ui.lblGlossary, self.glossaryFont)

    def colorOverview(self):
        """ slot to open color selection dialog """
        self.overviewColorObj = self.setColor(self.widget[0])
        self.setTextColor(self.ui.lblOverView, self.overviewColorObj)

    def colorSource(self):
        """ slot to open color selection dialog """
        self.tuSourceColorObj = self.setColor(self.widget[1])
        self.setTextColor(self.ui.lblSource, self.tuSourceColorObj)

    def colorTarget(self):
        """ slot to open color selection dialog """
        self.tuTargetColorObj = self.setColor(self.widget[2])
        self.setTextColor(self.ui.lblTarget, self.tuTargetColorObj)

    def colorComment(self):
        """ slot to open font selection dialog """
        self.commentColorObj = self.setColor(self.widget[3])
        self.setTextColor(self.ui.lblComment, self.commentColorObj)
        
    def colorTM(self):
        """ slot to open font selection dialog """
        self.TMColorObj = self.setColor(self.widget[5])
        self.setTextColor(self.ui.lblTM, self.TMColorObj)
    
    def colorGlossary(self):
        """ slot to open font selection dialog """
        self.glossaryColorObj = self.setColor(self.widget[6])
        self.setTextColor(self.ui.lblGlossary, self.glossaryColorObj)

    def getFont(self, obj):
        """@return obj: font object created from settings
        @param obj: widget whose font is gotten from"""
        font = World.settings.value(str(obj + "Font"), QtCore.QVariant(self.defaultFont.toString()))
        if (font.isValid()):
            fontObj = QtGui.QFont()
            if (fontObj.fromString(font.toString())):
                return fontObj
        return self.defaultFont

    def getColor(self, obj):
        """@return obj: color object created from settings
        @param obj: widget whose color is gotten from"""
        color = World.settings.value(str(obj + "Color"), QtCore.QVariant(self.defaultColor.name()))
        colorObj = QtGui.QColor(color.toString())
        return colorObj

    def defaultFonts(self):
        """slot Set default fonts"""
        self.setCaption(self.ui.lblOverView, self.defaultFont)
        self.overviewFont = self.defaultFont
        self.setCaption(self.ui.lblOverViewHeader, self.defaultFont)
        self.overviewHeaderFont = self.defaultFont
        self.setCaption(self.ui.lblSource, self.defaultFont)
        self.tuSourceFont = self.defaultFont
        self.setCaption(self.ui.lblTarget, self.defaultFont)
        self.tuTargetFont = self.defaultFont
        self.setCaption(self.ui.lblComment, self.defaultFont)
        self.commentFont = self.defaultFont
        self.setCaption(self.ui.lblTM, self.defaultFont)
        self.TMFont = self.defaultFont
        self.setCaption(self.ui.lblGlossary, self.defaultFont)
        self.glossaryFont = self.defaultFont

    def AdjustAllFonts(self):
        """ slot to open font selection dialog """
        self.adjustAllFonts = self.setFont(self.widget[1])
        self.overviewHeaderFont = self.adjustAllFonts
        self.setCaption(self.ui.lblOverViewHeader, self.overviewHeaderFont)
        self.overviewFont = self.adjustAllFonts
        self.setCaption(self.ui.lblOverView, self.overviewFont)
        self.tuSourceFont = self.adjustAllFonts
        self.setCaption(self.ui.lblSource, self.tuSourceFont)
        self.tuTargetFont = self.adjustAllFonts
        self.setCaption(self.ui.lblTarget, self.tuTargetFont)
        self.commentFont = self.adjustAllFonts
        self.setCaption(self.ui.lblComment, self.commentFont)
        self.TMFont = self.adjustAllFonts
        self.setCaption(self.ui.lblTM, self.TMFont)
        self.glossaryFont = self.adjustAllFonts
        self.setCaption(self.ui.lblGlossary, self.glossaryFont)

    def defaultColors(self):
        """slot Set default colors"""
        self.setTextColor(self.ui.lblOverView, self.defaultColor)
        self.overviewColorObj = self.defaultColor
        self.setTextColor(self.ui.lblSource, self.defaultColor)
        self.tuSourceColorObj = self.defaultColor
        self.setTextColor(self.ui.lblTarget, self.defaultColor)
        self.tuTargetColorObj = self.defaultColor
        self.setTextColor(self.ui.lblComment, self.defaultColor)
        self.commentColorObj = self.defaultColor
        self.setTextColor(self.ui.lblTM, self.defaultColor)
        self.TMColorObj = self.defaultColor
        self.setTextColor(self.ui.lblGlossary, self.defaultColor)
        self.glossaryColorObj = self.defaultColor

    def setCaption(self, lbl, fontObj):
        """ create the text from the font object and set the widget lable
        @param lbl: label widget for setting Font information to
        @param fontObj:  font whose information is set to label widget"""
        newText = fontObj.family() +",  "+ str(fontObj.pointSize())
        if (fontObj.bold()):
            newText.append(", " + self.tr("bold"))
        if (fontObj.italic()):
            newText.append(", " + self.tr("italic"))
        if (fontObj.underline()):
            newText.append(", " + self.tr("underline"))
        lbl.setText(newText)
        
    def setTextColor(self, lbl, colorObj):
        """ set color to the text of lable widget
        @param lbl: label widget for setting color to
        @param colorObj: Color to set to label widget"""
        palette = QtGui.QPalette(lbl.palette())
        palette.setColor(QtGui.QPalette.Active,QtGui.QPalette.ColorRole(QtGui.QPalette.WindowText), colorObj)
        palette.setColor(QtGui.QPalette.Inactive,QtGui.QPalette.ColorRole(QtGui.QPalette.WindowText), colorObj)
        lbl.setPalette(palette)

    def setFont(self, obj):
        """ open font dialog 
        @return selected new font object or the old one if cancel was pressed 
        @param obj: widget whose font is gotten from"""
        oldFont = self.getFont(obj)
        newFont, okPressed = QtGui.QFontDialog.getFont(oldFont)
        if (okPressed):
            return newFont
        return oldFont

    def setColor(self, obj):
        """ open color dialog 
        @return selected new color object or the old one if cancel was pressed
        @param obj: widget whose color is gotten from"""
        oldColor = self.getColor(obj)
        newColor = QtGui.QColorDialog.getColor(QtCore.Qt.white)
        if (newColor.isValid()):
            return newColor
        return oldColor
       
    def showDialog(self):
        """ make the dialog visible """
        # lazy init 
        if (not self.ui):
            self.setWindowTitle(self.tr("Preferences"))
            self.setModal(True)
            self.defaultFont = QtGui.QFont("Serif", 10)
            self.defaultColor = QtGui.QColor(QtCore.Qt.black)
            self.ui = Ui_frmPreference()
            self.ui.setupUi(self)
            self.ui.listWidget.addItem(QtGui.QListWidgetItem(QtGui.QIcon("../images/identity.png"), self.tr("Personalize")))
            self.ui.listWidget.addItem(QtGui.QListWidgetItem(QtGui.QIcon("../images/colorize.png"), self.tr("Font & Color")))
            self.ui.listWidget.addItem(QtGui.QListWidgetItem(QtGui.QIcon("../images/memory.png"), self.tr("TM-Glossary")))
            self.ui.listWidget.addItem(QtGui.QListWidgetItem(QtGui.QIcon("../images/save.png"), self.tr("      Save    ")))
            self.ui.listWidget.addItem(QtGui.QListWidgetItem(QtGui.QIcon("../images/editor.png"), self.tr("      Editor    ")))
            self.ui.listWidget.setViewMode(QtGui.QListView.IconMode)
            self.ui.listWidget.setCurrentRow(0)
            self.ui.listWidget.setResizeMode(QtGui.QListView.Fixed)
            #This setDragDropMode is mentioned in Qt4.2 only
#            self.ui.listWidget.setDragDropMode(QtGui.QAbstractItemView.NoDragDrop)
            self.connect(self.ui.listWidget, QtCore.SIGNAL("currentRowChanged(int)"), self.changedPaged)
            
            # TM page signals
            self.connect(self.ui.chbAutoTranslate, QtCore.SIGNAL("stateChanged(int)"), self.setTMOptions)
            self.connect(self.ui.chbIgnoreFuzzy, QtCore.SIGNAL("stateChanged(int)"), self.setTMOptions)
            self.connect(self.ui.chbAddTraslation, QtCore.SIGNAL("stateChanged(int)"), self.setTMOptions)
            
            # Glossary page signals
            self.connect(self.ui.chbAutoIdentTerm, QtCore.SIGNAL("stateChanged(int)"), self.setGlossaryOptions)
            self.connect(self.ui.chbChangeTerm, QtCore.SIGNAL("stateChanged(int)"), self.setGlossaryOptions)
            self.connect(self.ui.chbMatchTerm, QtCore.SIGNAL("stateChanged(int)"), self.setGlossaryOptions)
            self.connect(self.ui.chbDetectTerm, QtCore.SIGNAL("stateChanged(int)"), self.setGlossaryOptions)
            self.connect(self.ui.chbAddNewTerm, QtCore.SIGNAL("stateChanged(int)"), self.setGlossaryOptions)
            self.connect(self.ui.chbSuggestTranslation, QtCore.SIGNAL("stateChanged(int)"), self.setGlossaryOptions)
            
            # connect signals
            self.connect(self.ui.chkHeaderAuto, QtCore.SIGNAL("stateChanged(int)"), self.ui.chkHeaderAuto.checkState) 
            self.connect(self.ui.chkCursorHome, QtCore.SIGNAL("stateChanged(int)"), self.ui.chkCursorHome.checkState) 
            self.connect(self.ui.bntFontOverview, QtCore.SIGNAL("clicked()"), self.fontOverview) 
            self.connect(self.ui.bntFontOverviewHeader, QtCore.SIGNAL("clicked()"), self.fontOverviewHeader)
            self.connect(self.ui.bntFontSource, QtCore.SIGNAL("clicked()"), self.fontSource) 
            self.connect(self.ui.bntFontTarget, QtCore.SIGNAL("clicked()"), self.fontTarget)
            self.connect(self.ui.bntFontComment, QtCore.SIGNAL("clicked()"), self.fontComment) 
            self.connect(self.ui.bntFontTM, QtCore.SIGNAL("clicked()"), self.fontTM) 
            self.connect(self.ui.bntFontGlossary, QtCore.SIGNAL("clicked()"), self.fontGlossary) 
            self.connect(self.ui.bntDefaultsFont, QtCore.SIGNAL("clicked()"), self.defaultFonts)
            # set adjust all fonts for all widget
            self.connect(self.ui.bntAdjustAllFont, QtCore.SIGNAL("clicked()"), self.AdjustAllFonts)
            
            # for color
            self.connect(self.ui.btnColorComment, QtCore.SIGNAL("clicked()"), self.colorComment) 
            self.connect(self.ui.btnColorSource, QtCore.SIGNAL("clicked()"), self.colorSource) 
            self.connect(self.ui.btnColorTarget, QtCore.SIGNAL("clicked()"), self.colorTarget) 
            self.connect(self.ui.btnColorOverview, QtCore.SIGNAL("clicked()"), self.colorOverview) 
            self.connect(self.ui.btnColorTM, QtCore.SIGNAL("clicked()"), self.colorTM) 
            self.connect(self.ui.btnColorGlossary, QtCore.SIGNAL("clicked()"), self.colorGlossary) 
            self.connect(self.ui.bntDefaultsColor, QtCore.SIGNAL("clicked()"), self.defaultColors)
            
            #for language
            self.connect(self.ui.cbxLanguageCode, QtCore.SIGNAL("currentIndexChanged(const QString &)"), self.setLanguageIndex)
            self.connect(self.ui.cbxLanguageCode, QtCore.SIGNAL("currentIndexChanged(const QString &)"), self.setNPlural)
            
            self.connect(self.ui.okButton, QtCore.SIGNAL("clicked()"), self.accepted)
            
            self.widget = ["overview","tuSource","tuTarget","comment", "overviewHeader", "TM", "Glossary"]
            
            code =[]
            language = []
            for langCode, langInfo in data.languages.iteritems():
                code.append(langCode)
                language.append(langInfo[0])
                
            code.sort()
            self.ui.cbxLanguageCode.addItems(code)
    
        self.initUI()
        self.show()
        self.ui.listWidget.setFocus()
  
    def setLanguageIndex(self, langCode):
        """Set language name in line edit widget corresponding to langCode.
        @param langCode: a language code for finding language name as Qstring type. """
        language = common.Common(str(langCode))
        self.ui.lineFullLang.setText(language.fullname)
    
    def setNPlural(self, langCode):
        """Set nplurals for specific language.
        @param langCode: as Qstring type. """
        language = common.Common(str(langCode))
        self.ui.spinBox.setValue(language.nplurals)
        self.ui.lineEqaution.setText(language.pluralequation)
    
    def changedPaged(self):
        '''show a page of stackedWidget according to selected item in listwidget.
        '''
        self.ui.stackedWidget.setCurrentIndex(self.ui.listWidget.currentRow())
    
    def setTMOptions(self):
        TMpreference = 0
        if (self.ui.chbAutoTranslate.isChecked()):
            TMpreference +=1
        if (self.ui.chbIgnoreFuzzy.isChecked()):
            TMpreference +=2
        if (self.ui.chbAddTraslation.isChecked()):
            TMpreference +=4
        return TMpreference
#        self.emit(QtCore.SIGNAL("TMpreference"), TMpreference)
#        World.settings.setValue("TMpreference", QtCore.QVariant(TMpreference))
    
    def setGlossaryOptions(self):
        GlossaryPreference = 0
        if (self.ui.chbAutoIdentTerm.isChecked()):
            GlossaryPreference +=1
        if (self.ui.chbChangeTerm.isChecked()):
            GlossaryPreference +=2
        if (self.ui.chbMatchTerm.isChecked()):
            GlossaryPreference +=4
        if (self.ui.chbDetectTerm.isChecked()):
            GlossaryPreference +=8
        if (self.ui.chbAddNewTerm.isChecked()):
            GlossaryPreference +=16
        if (self.ui.chbSuggestTranslation.isChecked()):
            GlossaryPreference +=32
        return GlossaryPreference
        
if __name__ == "__main__":
    import sys, os
    # set the path for QT in order to find the icons
    QtCore.QDir.setCurrent(os.path.join(sys.path[0], "..", "ui"))
    app = QtGui.QApplication(sys.argv)
    user = Preference(None)
    user.showDialog()
    sys.exit(app.exec_())
