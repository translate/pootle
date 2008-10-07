# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/k-da/Documents/poxole/trunk/pootling/ui/tmSetting.ui'
#
# Created: Mon Jun 25 20:06:00 2007
#      by: PyQt4 UI code generator 4-snapshot-20070212
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_tmsetting(object):
    def setupUi(self, tmsetting):
        tmsetting.setObjectName("tmsetting")
        tmsetting.resize(QtCore.QSize(QtCore.QRect(0,0,468,366).size()).expandedTo(tmsetting.minimumSizeHint()))

        self.gridlayout = QtGui.QGridLayout(tmsetting)
        self.gridlayout.setMargin(9)
        self.gridlayout.setSpacing(6)
        self.gridlayout.setObjectName("gridlayout")

        self.checkBox = QtGui.QCheckBox(tmsetting)
        self.checkBox.setObjectName("checkBox")
        self.gridlayout.addWidget(self.checkBox,5,0,1,2)

        self.listWidget = QtGui.QListWidget(tmsetting)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(7),QtGui.QSizePolicy.Policy(7))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.listWidget.sizePolicy().hasHeightForWidth())
        self.listWidget.setSizePolicy(sizePolicy)
        self.listWidget.setObjectName("listWidget")
        self.gridlayout.addWidget(self.listWidget,1,0,4,2)

        spacerItem = QtGui.QSpacerItem(20,16,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.gridlayout.addItem(spacerItem,4,2,1,1)

        self.btnRemoveAll = QtGui.QPushButton(tmsetting)
        self.btnRemoveAll.setIcon(QtGui.QIcon("../images/eraser.png"))
        self.btnRemoveAll.setIconSize(QtCore.QSize(16,16))
        self.btnRemoveAll.setObjectName("btnRemoveAll")
        self.gridlayout.addWidget(self.btnRemoveAll,3,2,1,1)

        self.btnRemove = QtGui.QPushButton(tmsetting)
        self.btnRemove.setIcon(QtGui.QIcon("../images/removeTM.png"))
        self.btnRemove.setIconSize(QtCore.QSize(16,16))
        self.btnRemove.setObjectName("btnRemove")
        self.gridlayout.addWidget(self.btnRemove,2,2,1,1)

        self.btnAdd = QtGui.QPushButton(tmsetting)
        self.btnAdd.setIcon(QtGui.QIcon("../images/addTM.png"))
        self.btnAdd.setIconSize(QtCore.QSize(16,16))
        self.btnAdd.setObjectName("btnAdd")
        self.gridlayout.addWidget(self.btnAdd,1,2,1,1)

        self.btnCancel = QtGui.QPushButton(tmsetting)
        self.btnCancel.setObjectName("btnCancel")
        self.gridlayout.addWidget(self.btnCancel,8,2,1,1)

        self.btnOk = QtGui.QPushButton(tmsetting)
        self.btnOk.setObjectName("btnOk")
        self.gridlayout.addWidget(self.btnOk,8,1,1,1)

        self.groupBox = QtGui.QGroupBox(tmsetting)
        self.groupBox.setObjectName("groupBox")

        self.gridlayout1 = QtGui.QGridLayout(self.groupBox)
        self.gridlayout1.setMargin(9)
        self.gridlayout1.setSpacing(6)
        self.gridlayout1.setObjectName("gridlayout1")

        self.label_3 = QtGui.QLabel(self.groupBox)
        self.label_3.setObjectName("label_3")
        self.gridlayout1.addWidget(self.label_3,2,0,1,1)

        self.spinMaxLen = QtGui.QSpinBox(self.groupBox)
        self.spinMaxLen.setMaximum(100)
        self.spinMaxLen.setMinimum(1)
        self.spinMaxLen.setProperty("value",QtCore.QVariant(70))
        self.spinMaxLen.setObjectName("spinMaxLen")
        self.gridlayout1.addWidget(self.spinMaxLen,2,1,1,1)

        self.spinSimilarity = QtGui.QSpinBox(self.groupBox)
        self.spinSimilarity.setMaximum(100)
        self.spinSimilarity.setMinimum(75)
        self.spinSimilarity.setSingleStep(1)
        self.spinSimilarity.setProperty("value",QtCore.QVariant(75))
        self.spinSimilarity.setObjectName("spinSimilarity")
        self.gridlayout1.addWidget(self.spinSimilarity,0,1,1,1)

        self.label = QtGui.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.gridlayout1.addWidget(self.label,0,0,1,1)

        self.spinMaxCandidate = QtGui.QSpinBox(self.groupBox)
        self.spinMaxCandidate.setMaximum(10)
        self.spinMaxCandidate.setMinimum(1)
        self.spinMaxCandidate.setProperty("value",QtCore.QVariant(10))
        self.spinMaxCandidate.setObjectName("spinMaxCandidate")
        self.gridlayout1.addWidget(self.spinMaxCandidate,1,1,1,1)

        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.gridlayout1.addWidget(self.label_2,1,0,1,1)
        self.gridlayout.addWidget(self.groupBox,6,0,1,3)

        self.label_4 = QtGui.QLabel(tmsetting)
        self.label_4.setObjectName("label_4")
        self.gridlayout.addWidget(self.label_4,0,0,1,2)

        self.progressBar = QtGui.QProgressBar(tmsetting)
        self.progressBar.setProperty("value",QtCore.QVariant(0))
        self.progressBar.setOrientation(QtCore.Qt.Horizontal)
        self.progressBar.setObjectName("progressBar")
        self.gridlayout.addWidget(self.progressBar,8,0,1,1)

        self.label_6 = QtGui.QLabel(tmsetting)
        self.label_6.setObjectName("label_6")
        self.gridlayout.addWidget(self.label_6,7,0,1,3)

        self.retranslateUi(tmsetting)
        QtCore.QMetaObject.connectSlotsByName(tmsetting)
        tmsetting.setTabOrder(self.listWidget,self.btnAdd)
        tmsetting.setTabOrder(self.btnAdd,self.btnRemove)
        tmsetting.setTabOrder(self.btnRemove,self.btnRemoveAll)
        tmsetting.setTabOrder(self.btnRemoveAll,self.checkBox)
        tmsetting.setTabOrder(self.checkBox,self.spinSimilarity)
        tmsetting.setTabOrder(self.spinSimilarity,self.spinMaxCandidate)
        tmsetting.setTabOrder(self.spinMaxCandidate,self.spinMaxLen)
        tmsetting.setTabOrder(self.spinMaxLen,self.btnOk)
        tmsetting.setTabOrder(self.btnOk,self.btnCancel)

    def retranslateUi(self, tmsetting):
        tmsetting.setWindowTitle(QtGui.QApplication.translate("tmsetting", "Translation Memory and glossary Settings", None, QtGui.QApplication.UnicodeUTF8))
        self.checkBox.setText(QtGui.QApplication.translate("tmsetting", "Dive into Subfolders", None, QtGui.QApplication.UnicodeUTF8))
        self.btnRemoveAll.setToolTip(QtGui.QApplication.translate("tmsetting", "Clear path(s)", None, QtGui.QApplication.UnicodeUTF8))
        self.btnRemoveAll.setText(QtGui.QApplication.translate("tmsetting", " Clea&r", None, QtGui.QApplication.UnicodeUTF8))
        self.btnRemove.setToolTip(QtGui.QApplication.translate("tmsetting", "Delete selected path(s)", None, QtGui.QApplication.UnicodeUTF8))
        self.btnRemove.setText(QtGui.QApplication.translate("tmsetting", " De&lete", None, QtGui.QApplication.UnicodeUTF8))
        self.btnAdd.setToolTip(QtGui.QApplication.translate("tmsetting", "Add file or directory path(s)", None, QtGui.QApplication.UnicodeUTF8))
        self.btnAdd.setText(QtGui.QApplication.translate("tmsetting", " &Add", None, QtGui.QApplication.UnicodeUTF8))
        self.btnCancel.setText(QtGui.QApplication.translate("tmsetting", "&Cancel", None, QtGui.QApplication.UnicodeUTF8))
        self.btnOk.setText(QtGui.QApplication.translate("tmsetting", "&OK", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("tmsetting", "Options", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("tmsetting", "Maximum string length", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("tmsetting", "Minimum similarity", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("tmsetting", "Maximum search result", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("tmsetting", "Locations:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(QtGui.QApplication.translate("tmsetting", "Progress", None, QtGui.QApplication.UnicodeUTF8))



if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    tmsetting = QtGui.QWidget()
    ui = Ui_tmsetting()
    ui.setupUi(tmsetting)
    tmsetting.show()
    sys.exit(app.exec_())
