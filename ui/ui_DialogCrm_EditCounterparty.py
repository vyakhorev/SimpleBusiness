# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Research\THE_PROJ_Refactor\ui\DialogCrm_EditCounterparty.ui'
#
# Created: Sat Jan 03 02:17:01 2015
#      by: PyQt4 UI code generator 4.9.6
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_DialogCrm_EditCounterparty(object):
    def setupUi(self, DialogCrm_EditCounterparty):
        DialogCrm_EditCounterparty.setObjectName(_fromUtf8("DialogCrm_EditCounterparty"))
        DialogCrm_EditCounterparty.resize(520, 225)
        DialogCrm_EditCounterparty.setMinimumSize(QtCore.QSize(520, 225))
        DialogCrm_EditCounterparty.setMaximumSize(QtCore.QSize(520, 225))
        self.verticalLayout = QtGui.QVBoxLayout(DialogCrm_EditCounterparty)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label = QtGui.QLabel(DialogCrm_EditCounterparty)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)
        self.label_hashname = QtGui.QLabel(DialogCrm_EditCounterparty)
        self.label_hashname.setText(_fromUtf8(""))
        self.label_hashname.setObjectName(_fromUtf8("label_hashname"))
        self.gridLayout.addWidget(self.label_hashname, 2, 1, 1, 1)
        self.lineEdit_full_name = QtGui.QLineEdit(DialogCrm_EditCounterparty)
        self.lineEdit_full_name.setObjectName(_fromUtf8("lineEdit_full_name"))
        self.gridLayout.addWidget(self.lineEdit_full_name, 3, 1, 1, 1)
        self.label_2 = QtGui.QLabel(DialogCrm_EditCounterparty)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 3, 0, 1, 1)
        self.lineEdit_vatnum = QtGui.QLineEdit(DialogCrm_EditCounterparty)
        self.lineEdit_vatnum.setObjectName(_fromUtf8("lineEdit_vatnum"))
        self.gridLayout.addWidget(self.lineEdit_vatnum, 4, 1, 1, 1)
        self.lineEdit_acc_code = QtGui.QLineEdit(DialogCrm_EditCounterparty)
        self.lineEdit_acc_code.setObjectName(_fromUtf8("lineEdit_acc_code"))
        self.gridLayout.addWidget(self.lineEdit_acc_code, 5, 1, 1, 1)
        self.lineEdit_visible_name = QtGui.QLineEdit(DialogCrm_EditCounterparty)
        self.lineEdit_visible_name.setObjectName(_fromUtf8("lineEdit_visible_name"))
        self.gridLayout.addWidget(self.lineEdit_visible_name, 1, 1, 1, 1)
        self.comboBox_cptype = QtGui.QComboBox(DialogCrm_EditCounterparty)
        self.comboBox_cptype.setObjectName(_fromUtf8("comboBox_cptype"))
        self.gridLayout.addWidget(self.comboBox_cptype, 0, 1, 1, 1)
        self.label_3 = QtGui.QLabel(DialogCrm_EditCounterparty)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 4, 0, 1, 1)
        self.label_5 = QtGui.QLabel(DialogCrm_EditCounterparty)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.gridLayout.addWidget(self.label_5, 0, 0, 1, 1)
        self.label_4 = QtGui.QLabel(DialogCrm_EditCounterparty)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.gridLayout.addWidget(self.label_4, 5, 0, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.label_help = QtGui.QLabel(DialogCrm_EditCounterparty)
        self.label_help.setWordWrap(True)
        self.label_help.setObjectName(_fromUtf8("label_help"))
        self.verticalLayout.addWidget(self.label_help)
        self.buttonBox = QtGui.QDialogButtonBox(DialogCrm_EditCounterparty)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(DialogCrm_EditCounterparty)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), DialogCrm_EditCounterparty.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), DialogCrm_EditCounterparty.reject)
        QtCore.QMetaObject.connectSlotsByName(DialogCrm_EditCounterparty)

    def retranslateUi(self, DialogCrm_EditCounterparty):
        DialogCrm_EditCounterparty.setWindowTitle(_translate("DialogCrm_EditCounterparty", "Dialog", None))
        self.label.setText(_translate("DialogCrm_EditCounterparty", "Рабочее название", None))
        self.label_2.setText(_translate("DialogCrm_EditCounterparty", "Полное название", None))
        self.label_3.setText(_translate("DialogCrm_EditCounterparty", "ИНН (если есть)", None))
        self.label_5.setText(_translate("DialogCrm_EditCounterparty", "Тип контрагента", None))
        self.label_4.setText(_translate("DialogCrm_EditCounterparty", "Код в 1С (если есть)", None))
        self.label_help.setText(_translate("DialogCrm_EditCounterparty", "Подберите максимально короткое, но читабельное рабочее название. Указание ИНН и/или кода 1С позволит автоматически синхронизироваться с 1С. Если контрагент представлен несколькими юр. лицами, укажите оба кода ИНН / оба кода 1С через знак \";\"", None))

