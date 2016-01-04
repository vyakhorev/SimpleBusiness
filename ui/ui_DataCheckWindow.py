# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\Code\SimpleBusiness\ui\DataCheckWindow.ui'
#
# Created: Mon Jan 04 21:54:11 2016
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

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.setWindowModality(QtCore.Qt.NonModal)
        MainWindow.resize(924, 643)
        MainWindow.setDocumentMode(False)
        MainWindow.setTabShape(QtGui.QTabWidget.Rounded)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.horizontalLayout_16 = QtGui.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_16.setObjectName(_fromUtf8("horizontalLayout_16"))
        self.horizontalLayout_17 = QtGui.QHBoxLayout()
        self.horizontalLayout_17.setObjectName(_fromUtf8("horizontalLayout_17"))
        self.treeWidget_InitialData = QtGui.QTreeWidget(self.centralwidget)
        self.treeWidget_InitialData.setMaximumSize(QtCore.QSize(303, 16777215))
        self.treeWidget_InitialData.setObjectName(_fromUtf8("treeWidget_InitialData"))
        self.horizontalLayout_17.addWidget(self.treeWidget_InitialData)
        self.textBrowser_InitialData = QtGui.QTextBrowser(self.centralwidget)
        self.textBrowser_InitialData.setObjectName(_fromUtf8("textBrowser_InitialData"))
        self.horizontalLayout_17.addWidget(self.textBrowser_InitialData)
        self.horizontalLayout_16.addLayout(self.horizontalLayout_17)
        MainWindow.setCentralWidget(self.centralwidget)
        self.action_Run_Simulate = QtGui.QAction(MainWindow)
        self.action_Run_Simulate.setObjectName(_fromUtf8("action_Run_Simulate"))
        self.action_Synhronize_xm_with_db = QtGui.QAction(MainWindow)
        self.action_Synhronize_xm_with_db.setObjectName(_fromUtf8("action_Synhronize_xm_with_db"))
        self.action_upload_budget_csv = QtGui.QAction(MainWindow)
        self.action_upload_budget_csv.setObjectName(_fromUtf8("action_upload_budget_csv"))
        self.action_2 = QtGui.QAction(MainWindow)
        self.action_2.setObjectName(_fromUtf8("action_2"))
        self.action_3 = QtGui.QAction(MainWindow)
        self.action_3.setObjectName(_fromUtf8("action_3"))
        self.action_4 = QtGui.QAction(MainWindow)
        self.action_4.setObjectName(_fromUtf8("action_4"))
        self.action_5 = QtGui.QAction(MainWindow)
        self.action_5.setObjectName(_fromUtf8("action_5"))
        self.action_6 = QtGui.QAction(MainWindow)
        self.action_6.setObjectName(_fromUtf8("action_6"))
        self.action_fast_NewContact = QtGui.QAction(MainWindow)
        self.action_fast_NewContact.setObjectName(_fromUtf8("action_fast_NewContact"))
        self.action = QtGui.QAction(MainWindow)
        self.action.setObjectName(_fromUtf8("action"))
        self.action_AddFastNote = QtGui.QAction(MainWindow)
        self.action_AddFastNote.setObjectName(_fromUtf8("action_AddFastNote"))
        self.action_AddNewContact = QtGui.QAction(MainWindow)
        self.action_AddNewContact.setObjectName(_fromUtf8("action_AddNewContact"))
        self.action_7 = QtGui.QAction(MainWindow)
        self.action_7.setObjectName(_fromUtf8("action_7"))
        self.action_8 = QtGui.QAction(MainWindow)
        self.action_8.setObjectName(_fromUtf8("action_8"))
        self.action_AddNewCP = QtGui.QAction(MainWindow)
        self.action_AddNewCP.setObjectName(_fromUtf8("action_AddNewCP"))

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "Simple Business ", None))
        self.treeWidget_InitialData.headerItem().setText(0, _translate("MainWindow", "Item", None))
        self.treeWidget_InitialData.headerItem().setText(1, _translate("MainWindow", "Status", None))
        self.action_Run_Simulate.setText(_translate("MainWindow", "Запуск симуляции", None))
        self.action_Synhronize_xm_with_db.setText(_translate("MainWindow", "Загрузить из 1С", None))
        self.action_upload_budget_csv.setText(_translate("MainWindow", "Выгрузить в 1С", None))
        self.action_2.setText(_translate("MainWindow", "#ЗапросТовара", None))
        self.action_3.setText(_translate("MainWindow", "#Бюджет", None))
        self.action_4.setText(_translate("MainWindow", "#Офер", None))
        self.action_5.setText(_translate("MainWindow", "#Прайс", None))
        self.action_6.setText(_translate("MainWindow", "#Беседа", None))
        self.action_fast_NewContact.setText(_translate("MainWindow", "Новый контакт", None))
        self.action.setText(_translate("MainWindow", "Заметка", None))
        self.action_AddFastNote.setText(_translate("MainWindow", "+ Быстрая заметка", None))
        self.action_AddNewContact.setText(_translate("MainWindow", "+ Контакт", None))
        self.action_7.setText(_translate("MainWindow", "+ Клиент", None))
        self.action_8.setText(_translate("MainWindow", "+ Поставщик", None))
        self.action_AddNewCP.setText(_translate("MainWindow", "+ Контрагент", None))

