# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'unknown'
#
# Created: Tue Jun 12 10:22:09 2007
#      by: PyQt4 UI code generator 4.0
#
# WARNING! All changes made in this file will be lost!

import sys
from PyQt4 import QtCore, QtGui

class Ui_frmFind(object):
    def setupUi(self, frmFind):
        frmFind.setObjectName("frmFind")
        frmFind.setEnabled(True)
        frmFind.resize(QtCore.QSize(QtCore.QRect(0,0,695,26).size()).expandedTo(frmFind.minimumSizeHint()))

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(1),QtGui.QSizePolicy.Policy(1))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(frmFind.sizePolicy().hasHeightForWidth())
        frmFind.setSizePolicy(sizePolicy)
        frmFind.setAutoFillBackground(True)

        self.gridlayout = QtGui.QGridLayout(frmFind)
        self.gridlayout.setMargin(0)
        self.gridlayout.setSpacing(6)
        self.gridlayout.setObjectName("gridlayout")

        self.lineEdit = QtGui.QLineEdit(frmFind)
        self.lineEdit.setEnabled(True)
        self.lineEdit.setMinimumSize(QtCore.QSize(0,26))
        self.lineEdit.setObjectName("lineEdit")
        self.gridlayout.addWidget(self.lineEdit,0,1,1,1)

        self.find = QtGui.QPushButton(frmFind)
        self.find.setEnabled(True)
        self.find.setIcon(QtGui.QIcon("../images/find.png"))
        self.find.setAutoDefault(True)
        self.find.setDefault(True)
        self.find.setFlat(False)
        self.find.setObjectName("find")
        self.gridlayout.addWidget(self.find,0,2,1,1)

        self.lblFind = QtGui.QLabel(frmFind)
        self.lblFind.setSizeIncrement(QtCore.QSize(0,0))
        self.lblFind.setObjectName("lblFind")
        self.gridlayout.addWidget(self.lblFind,0,0,1,1)

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

        self.chbsource = QtGui.QCheckBox(self.groupBox)
        self.chbsource.setChecked(True)
        self.chbsource.setObjectName("chbsource")
        self.hboxlayout.addWidget(self.chbsource)

        self.chbtarget = QtGui.QCheckBox(self.groupBox)
        self.chbtarget.setChecked(True)
        self.chbtarget.setObjectName("chbtarget")
        self.hboxlayout.addWidget(self.chbtarget)
        self.gridlayout.addWidget(self.groupBox,0,4,1,1)

        self.retranslateUi(frmFind)
        QtCore.QMetaObject.connectSlotsByName(frmFind)
        frmFind.setTabOrder(self.lineEdit,self.find)

    def tr(self, string):
        return QtGui.QApplication.translate("frmFind", string, None, QtGui.QApplication.UnicodeUTF8)

    def retranslateUi(self, frmFind):
        frmFind.setWindowTitle(self.tr("Find"))
        self.find.setText(self.tr(" &Find"))
        self.lblFind.setText(self.tr("Find String in Files:"))
        self.chbsource.setText(self.tr("S&ource"))
        self.chbtarget.setText(self.tr("T&arget"))


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    frmFind = QtGui.QWidget()
    ui = Ui_frmFind()
    ui.setupUi(frmFind)
    frmFind.show()
    sys.exit(app.exec_())
