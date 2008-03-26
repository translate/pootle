# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/ks/programming/wordforge/trunk/pootling/ui/Find.ui'
#
# Created: Tue Feb 20 14:12:15 2007
#      by: PyQt4 UI code generator 4-snapshot-20070212
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_frmFind(object):
    def setupUi(self, frmFind):
        frmFind.setObjectName("frmFind")
        frmFind.setEnabled(True)
        frmFind.resize(QtCore.QSize(QtCore.QRect(0,0,695,78).size()).expandedTo(frmFind.minimumSizeHint()))

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(7),QtGui.QSizePolicy.Policy(7))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(frmFind.sizePolicy().hasHeightForWidth())
        frmFind.setSizePolicy(sizePolicy)
        frmFind.setAutoFillBackground(True)

        self.gridlayout = QtGui.QGridLayout(frmFind)
        self.gridlayout.setMargin(9)
        self.gridlayout.setSpacing(6)
        self.gridlayout.setObjectName("gridlayout")

        self.matchcase = QtGui.QCheckBox(frmFind)
        self.matchcase.setObjectName("matchcase")
        self.gridlayout.addWidget(self.matchcase,0,2,1,1)

        self.groupBox = QtGui.QGroupBox(frmFind)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(5),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setObjectName("groupBox")

        self.hboxlayout = QtGui.QHBoxLayout(self.groupBox)
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(11)
        self.hboxlayout.setObjectName("hboxlayout")

        self.insource = QtGui.QCheckBox(self.groupBox)
        self.insource.setCheckable(True)
        self.insource.setTristate(False)
        self.insource.setObjectName("insource")
        self.hboxlayout.addWidget(self.insource)

        self.intarget = QtGui.QCheckBox(self.groupBox)
        self.intarget.setObjectName("intarget")
        self.hboxlayout.addWidget(self.intarget)

        self.incomment = QtGui.QCheckBox(self.groupBox)
        self.incomment.setChecked(False)
        self.incomment.setObjectName("incomment")
        self.hboxlayout.addWidget(self.incomment)
        self.gridlayout.addWidget(self.groupBox,0,1,1,1)

        self.gridlayout1 = QtGui.QGridLayout()
        self.gridlayout1.setMargin(0)
        self.gridlayout1.setSpacing(6)
        self.gridlayout1.setObjectName("gridlayout1")

        self.lineEdit_2 = QtGui.QLineEdit(frmFind)
        self.lineEdit_2.setEnabled(False)
        self.lineEdit_2.setMinimumSize(QtCore.QSize(0,26))
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.gridlayout1.addWidget(self.lineEdit_2,1,1,1,1)

        self.lblReplace = QtGui.QLabel(frmFind)
        self.lblReplace.setSizeIncrement(QtCore.QSize(0,0))
        self.lblReplace.setObjectName("lblReplace")
        self.gridlayout1.addWidget(self.lblReplace,1,0,1,1)

        self.findNext = QtGui.QPushButton(frmFind)
        self.findNext.setEnabled(False)
        self.findNext.setIcon(QtGui.QIcon("../images/next.png"))
        self.findNext.setAutoDefault(True)
        self.findNext.setDefault(True)
        self.findNext.setFlat(False)
        self.findNext.setObjectName("findNext")
        self.gridlayout1.addWidget(self.findNext,0,2,1,1)

        self.lblFind = QtGui.QLabel(frmFind)
        self.lblFind.setSizeIncrement(QtCore.QSize(0,0))
        self.lblFind.setObjectName("lblFind")
        self.gridlayout1.addWidget(self.lblFind,0,0,1,1)

        self.lineEdit = QtGui.QLineEdit(frmFind)
        self.lineEdit.setEnabled(False)
        self.lineEdit.setMinimumSize(QtCore.QSize(0,26))
        self.lineEdit.setObjectName("lineEdit")
        self.gridlayout1.addWidget(self.lineEdit,0,1,1,1)

        self.findPrevious = QtGui.QPushButton(frmFind)
        self.findPrevious.setEnabled(False)
        self.findPrevious.setIcon(QtGui.QIcon("../images/previous.png"))
        self.findPrevious.setAutoDefault(True)
        self.findPrevious.setDefault(True)
        self.findPrevious.setFlat(False)
        self.findPrevious.setObjectName("findPrevious")
        self.gridlayout1.addWidget(self.findPrevious,0,3,1,1)

        self.replace = QtGui.QPushButton(frmFind)
        self.replace.setEnabled(False)
        self.replace.setIcon(QtGui.QIcon("../images/replace.png"))
        self.replace.setAutoDefault(True)
        self.replace.setDefault(True)
        self.replace.setFlat(False)
        self.replace.setObjectName("replace")
        self.gridlayout1.addWidget(self.replace,1,2,1,1)

        self.replaceAll = QtGui.QPushButton(frmFind)
        self.replaceAll.setEnabled(False)
        self.replaceAll.setIcon(QtGui.QIcon("../images/replaceAll.png"))
        self.replaceAll.setAutoDefault(True)
        self.replaceAll.setDefault(True)
        self.replaceAll.setFlat(False)
        self.replaceAll.setObjectName("replaceAll")
        self.gridlayout1.addWidget(self.replaceAll,1,3,1,1)
        self.gridlayout.addLayout(self.gridlayout1,0,0,1,1)

        self.retranslateUi(frmFind)
        QtCore.QMetaObject.connectSlotsByName(frmFind)
        frmFind.setTabOrder(self.lineEdit,self.findNext)
        frmFind.setTabOrder(self.findNext,self.findPrevious)
        frmFind.setTabOrder(self.findPrevious,self.lineEdit_2)
        frmFind.setTabOrder(self.lineEdit_2,self.replace)
        frmFind.setTabOrder(self.replace,self.replaceAll)

    def retranslateUi(self, frmFind):
        frmFind.setWindowTitle(QtGui.QApplication.translate("frmFind", "Find & Replace", None, QtGui.QApplication.UnicodeUTF8))
        self.matchcase.setText(QtGui.QApplication.translate("frmFind", "&Match case", None, QtGui.QApplication.UnicodeUTF8))
        self.insource.setText(QtGui.QApplication.translate("frmFind", "S&ource", None, QtGui.QApplication.UnicodeUTF8))
        self.intarget.setText(QtGui.QApplication.translate("frmFind", "T&arget", None, QtGui.QApplication.UnicodeUTF8))
        self.incomment.setText(QtGui.QApplication.translate("frmFind", "&Comment", None, QtGui.QApplication.UnicodeUTF8))
        self.lblReplace.setText(QtGui.QApplication.translate("frmFind", "Replace", None, QtGui.QApplication.UnicodeUTF8))
        self.findNext.setText(QtGui.QApplication.translate("frmFind", " &Next", None, QtGui.QApplication.UnicodeUTF8))
        self.lblFind.setText(QtGui.QApplication.translate("frmFind", "Search", None, QtGui.QApplication.UnicodeUTF8))
        self.findPrevious.setText(QtGui.QApplication.translate("frmFind", "  &Previous  ", None, QtGui.QApplication.UnicodeUTF8))
        self.replace.setText(QtGui.QApplication.translate("frmFind", " &Replace", None, QtGui.QApplication.UnicodeUTF8))
        self.replaceAll.setText(QtGui.QApplication.translate("frmFind", " Replace &All", None, QtGui.QApplication.UnicodeUTF8))



if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    frmFind = QtGui.QWidget()
    ui = Ui_frmFind()
    ui.setupUi(frmFind)
    frmFind.show()
    sys.exit(app.exec_())
