# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/k-da/Documents/poxole/trunk/pootling/ui/TableGlossary.ui'
#
# Created: Wed Jun  6 11:47:59 2007
#      by: PyQt4 UI code generator 4-snapshot-20070212
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(QtCore.QSize(QtCore.QRect(0,0,229,94).size()).expandedTo(Form.minimumSizeHint()))

        self.gridlayout = QtGui.QGridLayout(Form)
        self.gridlayout.setMargin(0)
        self.gridlayout.setSpacing(0)
        self.gridlayout.setObjectName("gridlayout")

        self.tblGlossary = QtGui.QTableWidget(Form)
        self.tblGlossary.setProperty("showDropIndicator",QtCore.QVariant(False))
        self.tblGlossary.setObjectName("tblGlossary")
        self.gridlayout.addWidget(self.tblGlossary,0,0,1,1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtGui.QApplication.translate("Form", "Glossary", None, QtGui.QApplication.UnicodeUTF8))
        self.tblGlossary.setWhatsThis(QtGui.QApplication.translate("Form", "<h3>Related Words</h3> This table shows all related words highlighted in the source view of the current unit. Its definition was extracted from the Glossary file to hint translators to use the same translation.", None, QtGui.QApplication.UnicodeUTF8))
        self.tblGlossary.setColumnCount(2)
        self.tblGlossary.clear()
        self.tblGlossary.setColumnCount(2)
        self.tblGlossary.setRowCount(0)



if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    Form = QtGui.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())
