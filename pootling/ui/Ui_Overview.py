# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/k-da/Documents/poxole/trunk/pootling/ui/Overview.ui'
#
# Created: Thu Apr 26 16:43:12 2007
#      by: PyQt4 UI code generator 4-snapshot-20070212
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(QtCore.QSize(QtCore.QRect(0,0,350,254).size()).expandedTo(Form.minimumSizeHint()))

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(3),QtGui.QSizePolicy.Policy(3))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        Form.setMinimumSize(QtCore.QSize(350,75))
        Form.setFocusPolicy(QtCore.Qt.NoFocus)

        self.gridlayout = QtGui.QGridLayout(Form)
        self.gridlayout.setMargin(0)
        self.gridlayout.setSpacing(1)
        self.gridlayout.setObjectName("gridlayout")

        self.tableOverview = QtGui.QTableWidget(Form)
        self.tableOverview.setEnabled(False)
        self.tableOverview.setMinimumSize(QtCore.QSize(0,0))
        self.tableOverview.setTabKeyNavigation(True)
        self.tableOverview.setAlternatingRowColors(True)
        self.tableOverview.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.tableOverview.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tableOverview.setShowGrid(False)
        self.tableOverview.setSortingEnabled(True)
        self.tableOverview.setObjectName("tableOverview")
        self.gridlayout.addWidget(self.tableOverview,0,0,1,1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtGui.QApplication.translate("Form", "Overview", None, QtGui.QApplication.UnicodeUTF8))
        self.tableOverview.setWhatsThis(QtGui.QApplication.translate("Form", "<h3>Overview</h3>This table shows original messages, translations, and status of each messages in current file.", None, QtGui.QApplication.UnicodeUTF8))
        self.tableOverview.setRowCount(0)
        self.tableOverview.clear()
        self.tableOverview.setColumnCount(0)
        self.tableOverview.setRowCount(0)



if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    Form = QtGui.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())
