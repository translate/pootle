# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/ratha/sourceforge.net/translate/trunk/pootling/ui/StatisticsDialog.ui'
#
# Created: Thu Aug 30 16:48:52 2007
#      by: PyQt4 UI code generator 4.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_StatisticsDialog(object):
    def setupUi(self, StatisticsDialog):
        StatisticsDialog.setObjectName("StatisticsDialog")
        StatisticsDialog.resize(QtCore.QSize(QtCore.QRect(0,0,298,275).size()).expandedTo(StatisticsDialog.minimumSizeHint()))

        self.gridlayout = QtGui.QGridLayout(StatisticsDialog)
        self.gridlayout.setMargin(9)
        self.gridlayout.setSpacing(6)
        self.gridlayout.setObjectName("gridlayout")

        self.frame = QtGui.QFrame(StatisticsDialog)
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName("frame")

        self.gridlayout1 = QtGui.QGridLayout(self.frame)
        self.gridlayout1.setMargin(9)
        self.gridlayout1.setSpacing(6)
        self.gridlayout1.setObjectName("gridlayout1")

        self.lblTransPercent = QtGui.QLabel(self.frame)
        self.lblTransPercent.setFrameShape(QtGui.QFrame.NoFrame)
        self.lblTransPercent.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.lblTransPercent.setObjectName("lblTransPercent")
        self.gridlayout1.addWidget(self.lblTransPercent,3,3,1,1)

        self.lblUntranPercent = QtGui.QLabel(self.frame)
        self.lblUntranPercent.setFrameShape(QtGui.QFrame.NoFrame)
        self.lblUntranPercent.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.lblUntranPercent.setObjectName("lblUntranPercent")
        self.gridlayout1.addWidget(self.lblUntranPercent,5,3,1,1)

        self.label_4 = QtGui.QLabel(self.frame)

        font = QtGui.QFont()
        font.setPointSize(9)
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.gridlayout1.addWidget(self.label_4,3,0,1,2)

        self.label_2 = QtGui.QLabel(self.frame)

        font = QtGui.QFont()
        font.setPointSize(9)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.gridlayout1.addWidget(self.label_2,5,0,1,1)

        self.label = QtGui.QLabel(self.frame)

        font = QtGui.QFont()
        font.setPointSize(9)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.gridlayout1.addWidget(self.label,2,0,1,2)

        self.lblTotalPercent = QtGui.QLabel(self.frame)
        self.lblTotalPercent.setFrameShape(QtGui.QFrame.NoFrame)
        self.lblTotalPercent.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.lblTotalPercent.setObjectName("lblTotalPercent")
        self.gridlayout1.addWidget(self.lblTotalPercent,6,3,1,1)

        spacerItem = QtGui.QSpacerItem(258,16,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.gridlayout1.addItem(spacerItem,7,0,1,4)

        self.label_6 = QtGui.QLabel(self.frame)

        font = QtGui.QFont()
        font.setPointSize(9)
        self.label_6.setFont(font)
        self.label_6.setObjectName("label_6")
        self.gridlayout1.addWidget(self.label_6,1,0,1,1)

        self.label_3 = QtGui.QLabel(self.frame)

        font = QtGui.QFont()
        font.setPointSize(9)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.gridlayout1.addWidget(self.label_3,4,0,1,1)

        self.label_5 = QtGui.QLabel(self.frame)

        font = QtGui.QFont()
        font.setPointSize(9)
        self.label_5.setFont(font)
        self.label_5.setObjectName("label_5")
        self.gridlayout1.addWidget(self.label_5,6,0,1,1)

        self.lblTotal = QtGui.QLabel(self.frame)
        self.lblTotal.setFrameShape(QtGui.QFrame.NoFrame)
        self.lblTotal.setFrameShadow(QtGui.QFrame.Raised)
        self.lblTotal.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.lblTotal.setObjectName("lblTotal")
        self.gridlayout1.addWidget(self.lblTotal,6,2,1,1)

        self.lblNumberofFiles = QtGui.QLabel(self.frame)
        self.lblNumberofFiles.setFrameShape(QtGui.QFrame.NoFrame)
        self.lblNumberofFiles.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.lblNumberofFiles.setObjectName("lblNumberofFiles")
        self.gridlayout1.addWidget(self.lblNumberofFiles,2,2,1,1)

        self.lblFuzzyPercent = QtGui.QLabel(self.frame)
        self.lblFuzzyPercent.setFrameShape(QtGui.QFrame.NoFrame)
        self.lblFuzzyPercent.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.lblFuzzyPercent.setObjectName("lblFuzzyPercent")
        self.gridlayout1.addWidget(self.lblFuzzyPercent,4,3,1,1)

        self.lblFuzzy = QtGui.QLabel(self.frame)
        self.lblFuzzy.setFrameShape(QtGui.QFrame.NoFrame)
        self.lblFuzzy.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.lblFuzzy.setObjectName("lblFuzzy")
        self.gridlayout1.addWidget(self.lblFuzzy,4,2,1,1)

        spacerItem1 = QtGui.QSpacerItem(121,16,QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        self.gridlayout1.addItem(spacerItem1,0,2,1,2)

        self.lblStatistic = QtGui.QLabel(self.frame)
        self.lblStatistic.setFrameShape(QtGui.QFrame.NoFrame)
        self.lblStatistic.setAlignment(QtCore.Qt.AlignCenter)
        self.lblStatistic.setObjectName("lblStatistic")
        self.gridlayout1.addWidget(self.lblStatistic,1,1,1,3)

        self.lblTranslated = QtGui.QLabel(self.frame)
        self.lblTranslated.setFrameShape(QtGui.QFrame.NoFrame)
        self.lblTranslated.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.lblTranslated.setObjectName("lblTranslated")
        self.gridlayout1.addWidget(self.lblTranslated,3,2,1,1)

        self.lblUntranslated = QtGui.QLabel(self.frame)
        self.lblUntranslated.setFrameShape(QtGui.QFrame.NoFrame)
        self.lblUntranslated.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.lblUntranslated.setObjectName("lblUntranslated")
        self.gridlayout1.addWidget(self.lblUntranslated,5,2,1,1)
        self.gridlayout.addWidget(self.frame,1,0,1,2)

        spacerItem2 = QtGui.QSpacerItem(41,26,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.gridlayout.addItem(spacerItem2,2,0,1,1)

        self.lblStatistic1 = QtGui.QLabel(StatisticsDialog)

        font = QtGui.QFont()
        font.setFamily("DejaVu Sans Condensed")
        font.setPointSize(12)
        font.setWeight(75)
        font.setBold(True)
        self.lblStatistic1.setFont(font)
        self.lblStatistic1.setAlignment(QtCore.Qt.AlignCenter)
        self.lblStatistic1.setObjectName("lblStatistic1")
        self.gridlayout.addWidget(self.lblStatistic1,0,0,1,2)

        self.btnOk = QtGui.QPushButton(StatisticsDialog)
        self.btnOk.setObjectName("btnOk")
        self.gridlayout.addWidget(self.btnOk,2,1,1,1)

        self.retranslateUi(StatisticsDialog)
        QtCore.QMetaObject.connectSlotsByName(StatisticsDialog)

    def retranslateUi(self, StatisticsDialog):
        StatisticsDialog.setWindowTitle(QtGui.QApplication.translate("StatisticsDialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("StatisticsDialog", "  Untranslated:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("StatisticsDialog", "  Translated:", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("StatisticsDialog", "  Number of files:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(QtGui.QApplication.translate("StatisticsDialog", "  Statistic of :", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("StatisticsDialog", "  Fuzzy:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("StatisticsDialog", "  Total:", None, QtGui.QApplication.UnicodeUTF8))
        self.lblStatistic1.setText(QtGui.QApplication.translate("StatisticsDialog", "Information of File and Folder", None, QtGui.QApplication.UnicodeUTF8))
        self.btnOk.setText(QtGui.QApplication.translate("StatisticsDialog", "&OK", None, QtGui.QApplication.UnicodeUTF8))



if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    StatisticsDialog = QtGui.QDialog()
    ui = Ui_StatisticsDialog()
    ui.setupUi(StatisticsDialog)
    StatisticsDialog.show()
    sys.exit(app.exec_())
