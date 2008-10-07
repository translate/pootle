# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/k-da/Documents/poxole/trunk/pootling/ui/TableTM.ui'
#
# Created: Tue Jun 19 11:50:43 2007
#      by: PyQt4 UI code generator 4-snapshot-20070212
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(QtCore.QSize(QtCore.QRect(0,0,227,100).size()).expandedTo(Form.minimumSizeHint()))

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(13),QtGui.QSizePolicy.Policy(13))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        Form.setMinimumSize(QtCore.QSize(100,50))

        self.gridlayout = QtGui.QGridLayout(Form)
        self.gridlayout.setMargin(0)
        self.gridlayout.setSpacing(0)
        self.gridlayout.setObjectName("gridlayout")

        self.tblTM = QtGui.QTableWidget(Form)
        self.tblTM.setDragEnabled(True)
        self.tblTM.setObjectName("tblTM")
        self.gridlayout.addWidget(self.tblTM,0,0,1,1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtGui.QApplication.translate("Form", "Lookup", None, QtGui.QApplication.UnicodeUTF8))
        self.tblTM.setWhatsThis(QtGui.QApplication.translate("Form", "<h3>Search Results</h3>This table shows the results of searching in translation memory. Similarity tells you about the seach score. 100% means the source is identical in TM. At the buttom is displayed the location, translator, and translated date of each candidate, row. This table is automatically hiden if the option \" Automatically lookup translation in TM\" under Settings/Preference/TM-Glossary is unchecked.", None, QtGui.QApplication.UnicodeUTF8))
        self.tblTM.setRowCount(0)
        self.tblTM.setColumnCount(2)
        self.tblTM.clear()
        self.tblTM.setColumnCount(2)
        self.tblTM.setRowCount(0)



if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    Form = QtGui.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())
