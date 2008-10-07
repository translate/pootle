# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/k-da/Documents/poxole/trunk/pootling/ui/CatalogSetting.ui'
#
# Created: Tue Sep 11 10:39:26 2007
#      by: PyQt4 UI code generator 4-snapshot-20070212
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_catPreferences(object):
    def setupUi(self, catPreferences):
        catPreferences.setObjectName("catPreferences")
        catPreferences.resize(QtCore.QSize(QtCore.QRect(0,0,359,250).size()).expandedTo(catPreferences.minimumSizeHint()))

        self.gridlayout = QtGui.QGridLayout(catPreferences)
        self.gridlayout.setMargin(9)
        self.gridlayout.setSpacing(6)
        self.gridlayout.setObjectName("gridlayout")

        self.frame = QtGui.QFrame(catPreferences)
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName("frame")

        self.gridlayout1 = QtGui.QGridLayout(self.frame)
        self.gridlayout1.setMargin(9)
        self.gridlayout1.setSpacing(6)
        self.gridlayout1.setObjectName("gridlayout1")

        spacerItem = QtGui.QSpacerItem(20,40,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.gridlayout1.addItem(spacerItem,3,1,1,1)

        self.chbSVN = QtGui.QCheckBox(self.frame)
        self.chbSVN.setChecked(True)
        self.chbSVN.setObjectName("chbSVN")
        self.gridlayout1.addWidget(self.chbSVN,2,1,1,1)

        self.chbname = QtGui.QCheckBox(self.frame)
        self.chbname.setChecked(True)
        self.chbname.setObjectName("chbname")
        self.gridlayout1.addWidget(self.chbname,0,0,1,1)

        self.chbtranslator = QtGui.QCheckBox(self.frame)
        self.chbtranslator.setChecked(True)
        self.chbtranslator.setObjectName("chbtranslator")
        self.gridlayout1.addWidget(self.chbtranslator,1,2,1,1)

        self.chblastrevision = QtGui.QCheckBox(self.frame)
        self.chblastrevision.setChecked(True)
        self.chblastrevision.setObjectName("chblastrevision")
        self.gridlayout1.addWidget(self.chblastrevision,0,2,1,1)

        self.chbuntranslated = QtGui.QCheckBox(self.frame)
        self.chbuntranslated.setChecked(True)
        self.chbuntranslated.setObjectName("chbuntranslated")
        self.gridlayout1.addWidget(self.chbuntranslated,0,1,1,1)

        self.chbfuzzy = QtGui.QCheckBox(self.frame)
        self.chbfuzzy.setChecked(True)
        self.chbfuzzy.setObjectName("chbfuzzy")
        self.gridlayout1.addWidget(self.chbfuzzy,2,0,1,1)

        self.chbtranslated = QtGui.QCheckBox(self.frame)
        self.chbtranslated.setChecked(True)
        self.chbtranslated.setObjectName("chbtranslated")
        self.gridlayout1.addWidget(self.chbtranslated,1,0,1,1)

        self.chbtotal = QtGui.QCheckBox(self.frame)
        self.chbtotal.setChecked(True)
        self.chbtotal.setObjectName("chbtotal")
        self.gridlayout1.addWidget(self.chbtotal,1,1,1,1)
        self.gridlayout.addWidget(self.frame,1,0,1,2)

        spacerItem1 = QtGui.QSpacerItem(191,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.gridlayout.addItem(spacerItem1,2,0,1,1)

        self.label = QtGui.QLabel(catPreferences)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(5),QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName("label")
        self.gridlayout.addWidget(self.label,0,0,1,2)

        self.btnOk = QtGui.QPushButton(catPreferences)
        self.btnOk.setObjectName("btnOk")
        self.gridlayout.addWidget(self.btnOk,2,1,1,1)

        self.retranslateUi(catPreferences)
        QtCore.QMetaObject.connectSlotsByName(catPreferences)
        catPreferences.setTabOrder(self.chbname,self.chbtranslated)
        catPreferences.setTabOrder(self.chbtranslated,self.chbfuzzy)
        catPreferences.setTabOrder(self.chbfuzzy,self.chbuntranslated)
        catPreferences.setTabOrder(self.chbuntranslated,self.chbtotal)
        catPreferences.setTabOrder(self.chbtotal,self.chbSVN)
        catPreferences.setTabOrder(self.chbSVN,self.chblastrevision)
        catPreferences.setTabOrder(self.chblastrevision,self.chbtranslator)
        catPreferences.setTabOrder(self.chbtranslator,self.btnOk)

    def retranslateUi(self, catPreferences):
        catPreferences.setWindowTitle(QtGui.QApplication.translate("catPreferences", "Catalog Manager Preferences", None, QtGui.QApplication.UnicodeUTF8))
        self.chbSVN.setToolTip(QtGui.QApplication.translate("catPreferences", "CVS/SVN Status", None, QtGui.QApplication.UnicodeUTF8))
        self.chbSVN.setWhatsThis(QtGui.QApplication.translate("catPreferences", "<h3>CVS/SVN Status</h3>Use this to checked/unchecked to display status of file in local or cvs/svn server on the catalog manager.", None, QtGui.QApplication.UnicodeUTF8))
        self.chbSVN.setText(QtGui.QApplication.translate("catPreferences", "CVS/SVN Status", None, QtGui.QApplication.UnicodeUTF8))
        self.chbname.setToolTip(QtGui.QApplication.translate("catPreferences", "Name", None, QtGui.QApplication.UnicodeUTF8))
        self.chbname.setWhatsThis(QtGui.QApplication.translate("catPreferences", "<h3>Name</h3>Use this to checked/unchecked to display file name on the catalog manager.", None, QtGui.QApplication.UnicodeUTF8))
        self.chbname.setText(QtGui.QApplication.translate("catPreferences", "Name", None, QtGui.QApplication.UnicodeUTF8))
        self.chbtranslator.setToolTip(QtGui.QApplication.translate("catPreferences", "Last Translator", None, QtGui.QApplication.UnicodeUTF8))
        self.chbtranslator.setWhatsThis(QtGui.QApplication.translate("catPreferences", "<h3>Last Translator</h3>Use this to checked/unchecked to display last translator\'s name in file on the catalog manager.", None, QtGui.QApplication.UnicodeUTF8))
        self.chbtranslator.setText(QtGui.QApplication.translate("catPreferences", "Last Translator", None, QtGui.QApplication.UnicodeUTF8))
        self.chblastrevision.setToolTip(QtGui.QApplication.translate("catPreferences", "Last Revision", None, QtGui.QApplication.UnicodeUTF8))
        self.chblastrevision.setWhatsThis(QtGui.QApplication.translate("catPreferences", "<h3>Last Revision</h3>Use this to checked/unchecked to display date/time in file was saved by the last translator on the catalog manager.", None, QtGui.QApplication.UnicodeUTF8))
        self.chblastrevision.setText(QtGui.QApplication.translate("catPreferences", "Last Revision", None, QtGui.QApplication.UnicodeUTF8))
        self.chbuntranslated.setToolTip(QtGui.QApplication.translate("catPreferences", "Untranslated", None, QtGui.QApplication.UnicodeUTF8))
        self.chbuntranslated.setWhatsThis(QtGui.QApplication.translate("catPreferences", "<h3>Untranslated</h3>Use this to checked/unchecked to display number of string in file was untranslated on the catalog manager.", None, QtGui.QApplication.UnicodeUTF8))
        self.chbuntranslated.setText(QtGui.QApplication.translate("catPreferences", "Untranslated", None, QtGui.QApplication.UnicodeUTF8))
        self.chbfuzzy.setToolTip(QtGui.QApplication.translate("catPreferences", "Fuzzy", None, QtGui.QApplication.UnicodeUTF8))
        self.chbfuzzy.setWhatsThis(QtGui.QApplication.translate("catPreferences", "<h3>Fuzzy</h3>Use this to checked/unchecked to display fuzzy number in file on the catalog manager.", None, QtGui.QApplication.UnicodeUTF8))
        self.chbfuzzy.setText(QtGui.QApplication.translate("catPreferences", "Fuzzy", None, QtGui.QApplication.UnicodeUTF8))
        self.chbtranslated.setToolTip(QtGui.QApplication.translate("catPreferences", "Translated", None, QtGui.QApplication.UnicodeUTF8))
        self.chbtranslated.setWhatsThis(QtGui.QApplication.translate("catPreferences", "<h3>Translated</h3>Use this to checked/unchecked to display number of string in file was translated on the catalog manager.", None, QtGui.QApplication.UnicodeUTF8))
        self.chbtranslated.setText(QtGui.QApplication.translate("catPreferences", "Translated", None, QtGui.QApplication.UnicodeUTF8))
        self.chbtotal.setToolTip(QtGui.QApplication.translate("catPreferences", "Total", None, QtGui.QApplication.UnicodeUTF8))
        self.chbtotal.setWhatsThis(QtGui.QApplication.translate("catPreferences", "<h3>Total</h3>Use this to checked/unchecked to display total number of strings in file on the catalog manager.", None, QtGui.QApplication.UnicodeUTF8))
        self.chbtotal.setText(QtGui.QApplication.translate("catPreferences", "Total", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("catPreferences", "Show Columns:", None, QtGui.QApplication.UnicodeUTF8))
        self.btnOk.setText(QtGui.QApplication.translate("catPreferences", "&OK", None, QtGui.QApplication.UnicodeUTF8))



if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    catPreferences = QtGui.QWidget()
    ui = Ui_catPreferences()
    ui.setupUi(catPreferences)
    catPreferences.show()
    sys.exit(app.exec_())
