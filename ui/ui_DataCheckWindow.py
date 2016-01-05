# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\Code\SimpleBusiness\ui\DataCheckWindow.ui'
#
# Created: Tue Jan 05 04:28:08 2016
#      by: PyQt4 UI code generator 4.11.3
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

class Ui_MainDataWindow(object):
    def setupUi(self, MainDataWindow):
        MainDataWindow.setObjectName(_fromUtf8("MainDataWindow"))
        MainDataWindow.setWindowModality(QtCore.Qt.NonModal)
        MainDataWindow.resize(924, 643)
        MainDataWindow.setDocumentMode(False)
        MainDataWindow.setTabShape(QtGui.QTabWidget.Rounded)
        self.centralwidget = QtGui.QWidget(MainDataWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.pushButton_LoadFrom1C = QtGui.QPushButton(self.centralwidget)
        self.pushButton_LoadFrom1C.setMaximumSize(QtCore.QSize(150, 16777215))
        self.pushButton_LoadFrom1C.setObjectName(_fromUtf8("pushButton_LoadFrom1C"))
        self.horizontalLayout.addWidget(self.pushButton_LoadFrom1C)
        self.pushButton_Refresh = QtGui.QPushButton(self.centralwidget)
        self.pushButton_Refresh.setMaximumSize(QtCore.QSize(150, 16777215))
        self.pushButton_Refresh.setObjectName(_fromUtf8("pushButton_Refresh"))
        self.horizontalLayout.addWidget(self.pushButton_Refresh)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.treeWidget_InitialData = QtGui.QTreeWidget(self.centralwidget)
        self.treeWidget_InitialData.setMaximumSize(QtCore.QSize(300, 16777215))
        self.treeWidget_InitialData.setObjectName(_fromUtf8("treeWidget_InitialData"))
        self.verticalLayout.addWidget(self.treeWidget_InitialData)
        self.horizontalLayout_2.addLayout(self.verticalLayout)
        self.textBrowser_InitialData = QtGui.QTextBrowser(self.centralwidget)
        self.textBrowser_InitialData.setObjectName(_fromUtf8("textBrowser_InitialData"))
        self.horizontalLayout_2.addWidget(self.textBrowser_InitialData)
        MainDataWindow.setCentralWidget(self.centralwidget)
        self.action_Run_Simulate = QtGui.QAction(MainDataWindow)
        self.action_Run_Simulate.setObjectName(_fromUtf8("action_Run_Simulate"))
        self.action_Synhronize_xm_with_db = QtGui.QAction(MainDataWindow)
        self.action_Synhronize_xm_with_db.setObjectName(_fromUtf8("action_Synhronize_xm_with_db"))
        self.action_upload_budget_csv = QtGui.QAction(MainDataWindow)
        self.action_upload_budget_csv.setObjectName(_fromUtf8("action_upload_budget_csv"))
        self.action_2 = QtGui.QAction(MainDataWindow)
        self.action_2.setObjectName(_fromUtf8("action_2"))
        self.action_3 = QtGui.QAction(MainDataWindow)
        self.action_3.setObjectName(_fromUtf8("action_3"))
        self.action_4 = QtGui.QAction(MainDataWindow)
        self.action_4.setObjectName(_fromUtf8("action_4"))
        self.action_5 = QtGui.QAction(MainDataWindow)
        self.action_5.setObjectName(_fromUtf8("action_5"))
        self.action_6 = QtGui.QAction(MainDataWindow)
        self.action_6.setObjectName(_fromUtf8("action_6"))
        self.action_fast_NewContact = QtGui.QAction(MainDataWindow)
        self.action_fast_NewContact.setObjectName(_fromUtf8("action_fast_NewContact"))
        self.action = QtGui.QAction(MainDataWindow)
        self.action.setObjectName(_fromUtf8("action"))
        self.action_AddFastNote = QtGui.QAction(MainDataWindow)
        self.action_AddFastNote.setObjectName(_fromUtf8("action_AddFastNote"))
        self.action_AddNewContact = QtGui.QAction(MainDataWindow)
        self.action_AddNewContact.setObjectName(_fromUtf8("action_AddNewContact"))
        self.action_7 = QtGui.QAction(MainDataWindow)
        self.action_7.setObjectName(_fromUtf8("action_7"))
        self.action_8 = QtGui.QAction(MainDataWindow)
        self.action_8.setObjectName(_fromUtf8("action_8"))
        self.action_AddNewCP = QtGui.QAction(MainDataWindow)
        self.action_AddNewCP.setObjectName(_fromUtf8("action_AddNewCP"))

        self.retranslateUi(MainDataWindow)
        QtCore.QMetaObject.connectSlotsByName(MainDataWindow)

    def retranslateUi(self, MainDataWindow):
        MainDataWindow.setWindowTitle(_translate("MainDataWindow", "Simple Business ", None))
        self.pushButton_LoadFrom1C.setText(_translate("MainDataWindow", "Загрузить из 1С", None))
        self.pushButton_Refresh.setText(_translate("MainDataWindow", "Обновить", None))
        self.treeWidget_InitialData.headerItem().setText(0, _translate("MainDataWindow", "Item", None))
        self.action_Run_Simulate.setText(_translate("MainDataWindow", "Запуск симуляции", None))
        self.action_Synhronize_xm_with_db.setText(_translate("MainDataWindow", "Загрузить из 1С", None))
        self.action_upload_budget_csv.setText(_translate("MainDataWindow", "Выгрузить в 1С", None))
        self.action_2.setText(_translate("MainDataWindow", "#ЗапросТовара", None))
        self.action_3.setText(_translate("MainDataWindow", "#Бюджет", None))
        self.action_4.setText(_translate("MainDataWindow", "#Офер", None))
        self.action_5.setText(_translate("MainDataWindow", "#Прайс", None))
        self.action_6.setText(_translate("MainDataWindow", "#Беседа", None))
        self.action_fast_NewContact.setText(_translate("MainDataWindow", "Новый контакт", None))
        self.action.setText(_translate("MainDataWindow", "Заметка", None))
        self.action_AddFastNote.setText(_translate("MainDataWindow", "+ Быстрая заметка", None))
        self.action_AddNewContact.setText(_translate("MainDataWindow", "+ Контакт", None))
        self.action_7.setText(_translate("MainDataWindow", "+ Клиент", None))
        self.action_8.setText(_translate("MainDataWindow", "+ Поставщик", None))
        self.action_AddNewCP.setText(_translate("MainDataWindow", "+ Контрагент", None))

