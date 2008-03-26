# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/k-da/Documents/poxole/trunk/pootling/ui/TUview.ui'
#
# Created: Mon Jul 30 09:12:20 2007
#      by: PyQt4 UI code generator 4-snapshot-20070212
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_TUview(object):
    def setupUi(self, TUview):
        TUview.setObjectName("TUview")
        TUview.setEnabled(True)
        TUview.resize(QtCore.QSize(QtCore.QRect(0,0,427,292).size()).expandedTo(TUview.minimumSizeHint()))

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(13),QtGui.QSizePolicy.Policy(13))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(TUview.sizePolicy().hasHeightForWidth())
        TUview.setSizePolicy(sizePolicy)
        TUview.setMaximumSize(QtCore.QSize(16777187,16777215))
        TUview.setFocusPolicy(QtCore.Qt.NoFocus)
        TUview.setAutoFillBackground(True)

        self.gridlayout = QtGui.QGridLayout(TUview)
        self.gridlayout.setMargin(0)
        self.gridlayout.setSpacing(0)
        self.gridlayout.setObjectName("gridlayout")

        self.splitter = QtGui.QSplitter(TUview)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName("splitter")

        self.sourceStacked = QtGui.QStackedWidget(self.splitter)
        self.sourceStacked.setObjectName("sourceStacked")

        self.page1 = QtGui.QWidget()
        self.page1.setObjectName("page1")

        self.gridlayout1 = QtGui.QGridLayout(self.page1)
        self.gridlayout1.setMargin(0)
        self.gridlayout1.setSpacing(0)
        self.gridlayout1.setObjectName("gridlayout1")

        self.txtSource = QtGui.QTextEdit(self.page1)
        self.txtSource.setTabChangesFocus(True)
        self.txtSource.setUndoRedoEnabled(False)
        self.txtSource.setReadOnly(True)
        self.txtSource.setTabStopWidth(79)
        self.txtSource.setObjectName("txtSource")
        self.gridlayout1.addWidget(self.txtSource,0,0,1,1)
        self.sourceStacked.addWidget(self.page1)

        self.page2 = QtGui.QWidget()
        self.page2.setObjectName("page2")

        self.gridlayout2 = QtGui.QGridLayout(self.page2)
        self.gridlayout2.setMargin(0)
        self.gridlayout2.setSpacing(0)
        self.gridlayout2.setObjectName("gridlayout2")

        self.tabWidgetSource = QtGui.QTabWidget(self.page2)
        self.tabWidgetSource.setObjectName("tabWidgetSource")

        self.tabSource1 = QtGui.QWidget()
        self.tabSource1.setObjectName("tabSource1")

        self.gridlayout3 = QtGui.QGridLayout(self.tabSource1)
        self.gridlayout3.setMargin(0)
        self.gridlayout3.setSpacing(0)
        self.gridlayout3.setObjectName("gridlayout3")

        self.txtPluralSource1 = QtGui.QTextEdit(self.tabSource1)
        self.txtPluralSource1.setObjectName("txtPluralSource1")
        self.gridlayout3.addWidget(self.txtPluralSource1,0,0,1,1)
        self.tabWidgetSource.addTab(self.tabSource1,"")
        self.gridlayout2.addWidget(self.tabWidgetSource,0,0,1,1)
        self.sourceStacked.addWidget(self.page2)

        self.lblComment = QtGui.QLabel(self.splitter)

        palette = QtGui.QPalette()

        brush = QtGui.QBrush(QtGui.QColor(255,10,26))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active,QtGui.QPalette.WindowText,brush)

        brush = QtGui.QBrush(QtGui.QColor(221,223,228))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active,QtGui.QPalette.Button,brush)

        brush = QtGui.QBrush(QtGui.QColor(255,255,255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active,QtGui.QPalette.Light,brush)

        brush = QtGui.QBrush(QtGui.QColor(255,255,255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active,QtGui.QPalette.Midlight,brush)

        brush = QtGui.QBrush(QtGui.QColor(85,85,85))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active,QtGui.QPalette.Dark,brush)

        brush = QtGui.QBrush(QtGui.QColor(199,199,199))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active,QtGui.QPalette.Mid,brush)

        brush = QtGui.QBrush(QtGui.QColor(0,0,0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active,QtGui.QPalette.Text,brush)

        brush = QtGui.QBrush(QtGui.QColor(255,255,255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active,QtGui.QPalette.BrightText,brush)

        brush = QtGui.QBrush(QtGui.QColor(0,0,0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active,QtGui.QPalette.ButtonText,brush)

        brush = QtGui.QBrush(QtGui.QColor(255,255,255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active,QtGui.QPalette.Base,brush)

        brush = QtGui.QBrush(QtGui.QColor(239,239,239))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active,QtGui.QPalette.Window,brush)

        brush = QtGui.QBrush(QtGui.QColor(0,0,0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active,QtGui.QPalette.Shadow,brush)

        brush = QtGui.QBrush(QtGui.QColor(103,141,178))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active,QtGui.QPalette.Highlight,brush)

        brush = QtGui.QBrush(QtGui.QColor(255,255,255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active,QtGui.QPalette.HighlightedText,brush)

        brush = QtGui.QBrush(QtGui.QColor(0,0,238))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active,QtGui.QPalette.Link,brush)

        brush = QtGui.QBrush(QtGui.QColor(82,24,139))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active,QtGui.QPalette.LinkVisited,brush)

        brush = QtGui.QBrush(QtGui.QColor(232,232,232))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active,QtGui.QPalette.AlternateBase,brush)

        brush = QtGui.QBrush(QtGui.QColor(255,10,26))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive,QtGui.QPalette.WindowText,brush)

        brush = QtGui.QBrush(QtGui.QColor(221,223,228))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive,QtGui.QPalette.Button,brush)

        brush = QtGui.QBrush(QtGui.QColor(255,255,255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive,QtGui.QPalette.Light,brush)

        brush = QtGui.QBrush(QtGui.QColor(255,255,255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive,QtGui.QPalette.Midlight,brush)

        brush = QtGui.QBrush(QtGui.QColor(85,85,85))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive,QtGui.QPalette.Dark,brush)

        brush = QtGui.QBrush(QtGui.QColor(199,199,199))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive,QtGui.QPalette.Mid,brush)

        brush = QtGui.QBrush(QtGui.QColor(0,0,0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive,QtGui.QPalette.Text,brush)

        brush = QtGui.QBrush(QtGui.QColor(255,255,255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive,QtGui.QPalette.BrightText,brush)

        brush = QtGui.QBrush(QtGui.QColor(0,0,0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive,QtGui.QPalette.ButtonText,brush)

        brush = QtGui.QBrush(QtGui.QColor(255,255,255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive,QtGui.QPalette.Base,brush)

        brush = QtGui.QBrush(QtGui.QColor(239,239,239))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive,QtGui.QPalette.Window,brush)

        brush = QtGui.QBrush(QtGui.QColor(0,0,0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive,QtGui.QPalette.Shadow,brush)

        brush = QtGui.QBrush(QtGui.QColor(103,141,178))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive,QtGui.QPalette.Highlight,brush)

        brush = QtGui.QBrush(QtGui.QColor(255,255,255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive,QtGui.QPalette.HighlightedText,brush)

        brush = QtGui.QBrush(QtGui.QColor(0,0,238))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive,QtGui.QPalette.Link,brush)

        brush = QtGui.QBrush(QtGui.QColor(82,24,139))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive,QtGui.QPalette.LinkVisited,brush)

        brush = QtGui.QBrush(QtGui.QColor(232,232,232))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive,QtGui.QPalette.AlternateBase,brush)

        brush = QtGui.QBrush(QtGui.QColor(128,128,128))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled,QtGui.QPalette.WindowText,brush)

        brush = QtGui.QBrush(QtGui.QColor(221,223,228))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled,QtGui.QPalette.Button,brush)

        brush = QtGui.QBrush(QtGui.QColor(255,255,255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled,QtGui.QPalette.Light,brush)

        brush = QtGui.QBrush(QtGui.QColor(255,255,255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled,QtGui.QPalette.Midlight,brush)

        brush = QtGui.QBrush(QtGui.QColor(85,85,85))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled,QtGui.QPalette.Dark,brush)

        brush = QtGui.QBrush(QtGui.QColor(199,199,199))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled,QtGui.QPalette.Mid,brush)

        brush = QtGui.QBrush(QtGui.QColor(199,199,199))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled,QtGui.QPalette.Text,brush)

        brush = QtGui.QBrush(QtGui.QColor(255,255,255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled,QtGui.QPalette.BrightText,brush)

        brush = QtGui.QBrush(QtGui.QColor(128,128,128))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled,QtGui.QPalette.ButtonText,brush)

        brush = QtGui.QBrush(QtGui.QColor(239,239,239))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled,QtGui.QPalette.Base,brush)

        brush = QtGui.QBrush(QtGui.QColor(239,239,239))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled,QtGui.QPalette.Window,brush)

        brush = QtGui.QBrush(QtGui.QColor(0,0,0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled,QtGui.QPalette.Shadow,brush)

        brush = QtGui.QBrush(QtGui.QColor(86,117,148))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled,QtGui.QPalette.Highlight,brush)

        brush = QtGui.QBrush(QtGui.QColor(255,255,255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled,QtGui.QPalette.HighlightedText,brush)

        brush = QtGui.QBrush(QtGui.QColor(0,0,238))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled,QtGui.QPalette.Link,brush)

        brush = QtGui.QBrush(QtGui.QColor(82,24,139))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled,QtGui.QPalette.LinkVisited,brush)

        brush = QtGui.QBrush(QtGui.QColor(232,232,232))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled,QtGui.QPalette.AlternateBase,brush)
        self.lblComment.setPalette(palette)
        self.lblComment.setObjectName("lblComment")

        self.targetStacked = QtGui.QStackedWidget(self.splitter)
        self.targetStacked.setObjectName("targetStacked")

        self.page3 = QtGui.QWidget()
        self.page3.setObjectName("page3")

        self.gridlayout4 = QtGui.QGridLayout(self.page3)
        self.gridlayout4.setMargin(0)
        self.gridlayout4.setSpacing(0)
        self.gridlayout4.setObjectName("gridlayout4")

        self.txtTarget = QtGui.QTextEdit(self.page3)
        self.txtTarget.setTabChangesFocus(False)
        self.txtTarget.setUndoRedoEnabled(False)
        self.txtTarget.setReadOnly(True)
        self.txtTarget.setTabStopWidth(79)
        self.txtTarget.setObjectName("txtTarget")
        self.gridlayout4.addWidget(self.txtTarget,0,0,1,1)
        self.targetStacked.addWidget(self.page3)

        self.page4 = QtGui.QWidget()
        self.page4.setObjectName("page4")

        self.gridlayout5 = QtGui.QGridLayout(self.page4)
        self.gridlayout5.setMargin(0)
        self.gridlayout5.setSpacing(0)
        self.gridlayout5.setObjectName("gridlayout5")

        self.tabWidgetTarget = QtGui.QTabWidget(self.page4)
        self.tabWidgetTarget.setObjectName("tabWidgetTarget")

        self.tabTarget1 = QtGui.QWidget()
        self.tabTarget1.setObjectName("tabTarget1")

        self.gridlayout6 = QtGui.QGridLayout(self.tabTarget1)
        self.gridlayout6.setMargin(0)
        self.gridlayout6.setSpacing(0)
        self.gridlayout6.setObjectName("gridlayout6")

        self.txtPluralTarget1 = QtGui.QTextEdit(self.tabTarget1)
        self.txtPluralTarget1.setObjectName("txtPluralTarget1")
        self.gridlayout6.addWidget(self.txtPluralTarget1,0,0,1,1)
        self.tabWidgetTarget.addTab(self.tabTarget1,"")
        self.gridlayout5.addWidget(self.tabWidgetTarget,0,0,1,1)
        self.targetStacked.addWidget(self.page4)
        self.gridlayout.addWidget(self.splitter,0,0,1,1)

        self.fileScrollBar = QtGui.QScrollBar(TUview)
        self.fileScrollBar.setEnabled(False)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(0),QtGui.QSizePolicy.Policy(7))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.fileScrollBar.sizePolicy().hasHeightForWidth())
        self.fileScrollBar.setSizePolicy(sizePolicy)
        self.fileScrollBar.setMaximum(0)
        self.fileScrollBar.setTracking(False)
        self.fileScrollBar.setOrientation(QtCore.Qt.Vertical)
        self.fileScrollBar.setObjectName("fileScrollBar")
        self.gridlayout.addWidget(self.fileScrollBar,0,2,1,1)

        spacerItem = QtGui.QSpacerItem(16,588,QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Minimum)
        self.gridlayout.addItem(spacerItem,0,1,1,1)

        self.retranslateUi(TUview)
        self.sourceStacked.setCurrentIndex(0)
        self.tabWidgetSource.setCurrentIndex(0)
        self.targetStacked.setCurrentIndex(0)
        self.tabWidgetTarget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(TUview)

    def retranslateUi(self, TUview):
        TUview.setWindowTitle(QtGui.QApplication.translate("TUview", "Detail", None, QtGui.QApplication.UnicodeUTF8))
        TUview.setWhatsThis(QtGui.QApplication.translate("TUview", "<h3>Source and Target View</h3>It contains source of unit in the upper text box, and target of unit in the below text box. If unit is plural, it will display multi of tabs.", None, QtGui.QApplication.UnicodeUTF8))
        self.txtSource.setToolTip(QtGui.QApplication.translate("TUview", "Original Source String", None, QtGui.QApplication.UnicodeUTF8))
        self.txtSource.setWhatsThis(QtGui.QApplication.translate("TUview", "<h3>Original Source String</h3>This part of the window shows you the original string of the currently displayed entry. <br>You can not edit this string.", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidgetSource.setTabText(self.tabWidgetSource.indexOf(self.tabSource1), QtGui.QApplication.translate("TUview", "Plural 1", None, QtGui.QApplication.UnicodeUTF8))
        self.lblComment.setToolTip(QtGui.QApplication.translate("TUview", "Important Comment", None, QtGui.QApplication.UnicodeUTF8))
        self.lblComment.setStatusTip(QtGui.QApplication.translate("TUview", "Important Comment", None, QtGui.QApplication.UnicodeUTF8))
        self.lblComment.setWhatsThis(QtGui.QApplication.translate("TUview", "<h3>Important Comment</h3>Hints from the developer to the translator are displayed in this area. This area will be hidden if there is no hint. ", None, QtGui.QApplication.UnicodeUTF8))
        self.txtTarget.setToolTip(QtGui.QApplication.translate("TUview", "Translated String", None, QtGui.QApplication.UnicodeUTF8))
        self.txtTarget.setWhatsThis(QtGui.QApplication.translate("TUview", "<h3>Translated String</h3>This editor displays and lets you edit the translation of the currently displayed string.", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidgetTarget.setTabText(self.tabWidgetTarget.indexOf(self.tabTarget1), QtGui.QApplication.translate("TUview", "Plural 1", None, QtGui.QApplication.UnicodeUTF8))
        self.fileScrollBar.setToolTip(QtGui.QApplication.translate("TUview", "Navigate in your file", None, QtGui.QApplication.UnicodeUTF8))
        self.fileScrollBar.setStatusTip(QtGui.QApplication.translate("TUview", "Navigation Scrollbar", None, QtGui.QApplication.UnicodeUTF8))
        self.fileScrollBar.setWhatsThis(QtGui.QApplication.translate("TUview", "<h3>Navigation Scrollbar</h3>It allows you do navigate in the current file. If you filter your strings you get only the filtered list. <br>It also gives you visual feedback about the postion of the current entry. The Tooltip also shows you the current number and the total numbers of strings.", None, QtGui.QApplication.UnicodeUTF8))



if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    TUview = QtGui.QWidget()
    ui = Ui_TUview()
    ui.setupUi(TUview)
    TUview.show()
    sys.exit(app.exec_())
