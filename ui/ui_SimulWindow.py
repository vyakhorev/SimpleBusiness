# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\Code\SimpleBusiness\ui\SimulWindow.ui'
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

class Ui_MainSimulWindow(object):
    def setupUi(self, MainSimulWindow):
        MainSimulWindow.setObjectName(_fromUtf8("MainSimulWindow"))
        MainSimulWindow.setWindowModality(QtCore.Qt.NonModal)
        MainSimulWindow.resize(924, 643)
        MainSimulWindow.setDocumentMode(False)
        MainSimulWindow.setTabShape(QtGui.QTabWidget.Rounded)
        self.centralwidget = QtGui.QWidget(MainSimulWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.horizontalLayout_16 = QtGui.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_16.setObjectName(_fromUtf8("horizontalLayout_16"))
        self.Global_tabs = QtGui.QTabWidget(self.centralwidget)
        self.Global_tabs.setEnabled(True)
        self.Global_tabs.setTabPosition(QtGui.QTabWidget.North)
        self.Global_tabs.setTabShape(QtGui.QTabWidget.Rounded)
        self.Global_tabs.setDocumentMode(False)
        self.Global_tabs.setObjectName(_fromUtf8("Global_tabs"))
        self.tab_Simulation = QtGui.QWidget()
        self.tab_Simulation.setObjectName(_fromUtf8("tab_Simulation"))
        self.horizontalLayout_13 = QtGui.QHBoxLayout(self.tab_Simulation)
        self.horizontalLayout_13.setObjectName(_fromUtf8("horizontalLayout_13"))
        self.horizontalLayout_11 = QtGui.QHBoxLayout()
        self.horizontalLayout_11.setObjectName(_fromUtf8("horizontalLayout_11"))
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.lineEdit_find_var_mainsim = QtGui.QLineEdit(self.tab_Simulation)
        self.lineEdit_find_var_mainsim.setObjectName(_fromUtf8("lineEdit_find_var_mainsim"))
        self.verticalLayout_2.addWidget(self.lineEdit_find_var_mainsim)
        self.listView_main_sim = QtGui.QListView(self.tab_Simulation)
        self.listView_main_sim.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.listView_main_sim.setObjectName(_fromUtf8("listView_main_sim"))
        self.verticalLayout_2.addWidget(self.listView_main_sim)
        self.horizontalLayout_11.addLayout(self.verticalLayout_2)
        self.verticalLayout_11 = QtGui.QVBoxLayout()
        self.verticalLayout_11.setObjectName(_fromUtf8("verticalLayout_11"))
        self.SIM_info_tabs = QtGui.QTabWidget(self.tab_Simulation)
        self.SIM_info_tabs.setTabPosition(QtGui.QTabWidget.West)
        self.SIM_info_tabs.setTabShape(QtGui.QTabWidget.Rounded)
        self.SIM_info_tabs.setObjectName(_fromUtf8("SIM_info_tabs"))
        self.SIM_INF_plot = QtGui.QWidget()
        self.SIM_INF_plot.setObjectName(_fromUtf8("SIM_INF_plot"))
        self.verticalLayout = QtGui.QVBoxLayout(self.SIM_INF_plot)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout_14 = QtGui.QHBoxLayout()
        self.horizontalLayout_14.setObjectName(_fromUtf8("horizontalLayout_14"))
        self.button_home = QtGui.QPushButton(self.SIM_INF_plot)
        self.button_home.setObjectName(_fromUtf8("button_home"))
        self.horizontalLayout_14.addWidget(self.button_home)
        self.button_zoom = QtGui.QPushButton(self.SIM_INF_plot)
        self.button_zoom.setObjectName(_fromUtf8("button_zoom"))
        self.horizontalLayout_14.addWidget(self.button_zoom)
        self.button_pan = QtGui.QPushButton(self.SIM_INF_plot)
        self.button_pan.setObjectName(_fromUtf8("button_pan"))
        self.horizontalLayout_14.addWidget(self.button_pan)
        self.button_saveplot = QtGui.QPushButton(self.SIM_INF_plot)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("../../Users/vyakhorev/.designer/backup/icons/save_icon.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("../../Users/vyakhorev/.designer/backup/icons/save_icon.png")), QtGui.QIcon.Normal, QtGui.QIcon.On)
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("../../Users/vyakhorev/.designer/backup/icons/save_icon.png")), QtGui.QIcon.Active, QtGui.QIcon.Off)
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("../../Users/vyakhorev/.designer/backup/icons/save_icon.png")), QtGui.QIcon.Active, QtGui.QIcon.On)
        self.button_saveplot.setIcon(icon)
        self.button_saveplot.setObjectName(_fromUtf8("button_saveplot"))
        self.horizontalLayout_14.addWidget(self.button_saveplot)
        self.verticalLayout.addLayout(self.horizontalLayout_14)
        self.SIM_INF_mpl_plot = MatplotlibWidget(self.SIM_INF_plot)
        self.SIM_INF_mpl_plot.setObjectName(_fromUtf8("SIM_INF_mpl_plot"))
        self.verticalLayout.addWidget(self.SIM_INF_mpl_plot)
        self.SIM_info_tabs.addTab(self.SIM_INF_plot, _fromUtf8(""))
        self.SIM_INF_report = QtGui.QWidget()
        self.SIM_INF_report.setObjectName(_fromUtf8("SIM_INF_report"))
        self.horizontalLayout_19 = QtGui.QHBoxLayout(self.SIM_INF_report)
        self.horizontalLayout_19.setObjectName(_fromUtf8("horizontalLayout_19"))
        self.textBrowser_Simulation = QtGui.QTextBrowser(self.SIM_INF_report)
        self.textBrowser_Simulation.setObjectName(_fromUtf8("textBrowser_Simulation"))
        self.horizontalLayout_19.addWidget(self.textBrowser_Simulation)
        self.SIM_info_tabs.addTab(self.SIM_INF_report, _fromUtf8(""))
        self.verticalLayout_11.addWidget(self.SIM_info_tabs)
        self.horizontalLayout_11.addLayout(self.verticalLayout_11)
        self.horizontalLayout_13.addLayout(self.horizontalLayout_11)
        self.Global_tabs.addTab(self.tab_Simulation, _fromUtf8(""))
        self.tab_SimulLog = QtGui.QWidget()
        self.tab_SimulLog.setObjectName(_fromUtf8("tab_SimulLog"))
        self.verticalLayout_10 = QtGui.QVBoxLayout(self.tab_SimulLog)
        self.verticalLayout_10.setObjectName(_fromUtf8("verticalLayout_10"))
        self.horizontalLayout_15 = QtGui.QHBoxLayout()
        self.horizontalLayout_15.setObjectName(_fromUtf8("horizontalLayout_15"))
        self.pushButton_log_run_simul_random = QtGui.QPushButton(self.tab_SimulLog)
        self.pushButton_log_run_simul_random.setObjectName(_fromUtf8("pushButton_log_run_simul_random"))
        self.horizontalLayout_15.addWidget(self.pushButton_log_run_simul_random)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_15.addItem(spacerItem)
        self.button_log_run_simul = QtGui.QPushButton(self.tab_SimulLog)
        self.button_log_run_simul.setMaximumSize(QtCore.QSize(16777215, 41))
        self.button_log_run_simul.setObjectName(_fromUtf8("button_log_run_simul"))
        self.horizontalLayout_15.addWidget(self.button_log_run_simul)
        self.seed_cmbx = QtGui.QComboBox(self.tab_SimulLog)
        self.seed_cmbx.setMinimumSize(QtCore.QSize(300, 0))
        self.seed_cmbx.setEditable(True)
        self.seed_cmbx.setObjectName(_fromUtf8("seed_cmbx"))
        self.horizontalLayout_15.addWidget(self.seed_cmbx)
        self.verticalLayout_10.addLayout(self.horizontalLayout_15)
        self.tabWidget_testsim = QtGui.QTabWidget(self.tab_SimulLog)
        self.tabWidget_testsim.setTabPosition(QtGui.QTabWidget.West)
        self.tabWidget_testsim.setTabShape(QtGui.QTabWidget.Rounded)
        self.tabWidget_testsim.setObjectName(_fromUtf8("tabWidget_testsim"))
        self.tab_log = QtGui.QWidget()
        self.tab_log.setObjectName(_fromUtf8("tab_log"))
        self.verticalLayout_9 = QtGui.QVBoxLayout(self.tab_log)
        self.verticalLayout_9.setObjectName(_fromUtf8("verticalLayout_9"))
        self.lineEdit_SearchInLog = QtGui.QLineEdit(self.tab_log)
        self.lineEdit_SearchInLog.setObjectName(_fromUtf8("lineEdit_SearchInLog"))
        self.verticalLayout_9.addWidget(self.lineEdit_SearchInLog)
        self.log_table_browser = QtGui.QTableView(self.tab_log)
        self.log_table_browser.setObjectName(_fromUtf8("log_table_browser"))
        self.verticalLayout_9.addWidget(self.log_table_browser)
        self.tabWidget_testsim.addTab(self.tab_log, _fromUtf8(""))
        self.tab_variables = QtGui.QWidget()
        self.tab_variables.setObjectName(_fromUtf8("tab_variables"))
        self.horizontalLayout_12 = QtGui.QHBoxLayout(self.tab_variables)
        self.horizontalLayout_12.setObjectName(_fromUtf8("horizontalLayout_12"))
        self.verticalLayout_14 = QtGui.QVBoxLayout()
        self.verticalLayout_14.setObjectName(_fromUtf8("verticalLayout_14"))
        self.lineEdit_testsim_findvar = QtGui.QLineEdit(self.tab_variables)
        self.lineEdit_testsim_findvar.setObjectName(_fromUtf8("lineEdit_testsim_findvar"))
        self.verticalLayout_14.addWidget(self.lineEdit_testsim_findvar)
        self.listView_log_var_list = QtGui.QListView(self.tab_variables)
        self.listView_log_var_list.setObjectName(_fromUtf8("listView_log_var_list"))
        self.verticalLayout_14.addWidget(self.listView_log_var_list)
        self.horizontalLayout_12.addLayout(self.verticalLayout_14)
        self.mplwidget_testsim = MatplotlibWidget(self.tab_variables)
        self.mplwidget_testsim.setObjectName(_fromUtf8("mplwidget_testsim"))
        self.horizontalLayout_12.addWidget(self.mplwidget_testsim)
        self.tabWidget_testsim.addTab(self.tab_variables, _fromUtf8(""))
        self.verticalLayout_10.addWidget(self.tabWidget_testsim)
        self.Global_tabs.addTab(self.tab_SimulLog, _fromUtf8(""))
        self.horizontalLayout_16.addWidget(self.Global_tabs)
        MainSimulWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtGui.QStatusBar(MainSimulWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainSimulWindow.setStatusBar(self.statusbar)
        self.action_Run_Simulate = QtGui.QAction(MainSimulWindow)
        self.action_Run_Simulate.setObjectName(_fromUtf8("action_Run_Simulate"))
        self.action_Synhronize_xm_with_db = QtGui.QAction(MainSimulWindow)
        self.action_Synhronize_xm_with_db.setObjectName(_fromUtf8("action_Synhronize_xm_with_db"))
        self.action_upload_budget_csv = QtGui.QAction(MainSimulWindow)
        self.action_upload_budget_csv.setObjectName(_fromUtf8("action_upload_budget_csv"))
        self.action_2 = QtGui.QAction(MainSimulWindow)
        self.action_2.setObjectName(_fromUtf8("action_2"))
        self.action_3 = QtGui.QAction(MainSimulWindow)
        self.action_3.setObjectName(_fromUtf8("action_3"))
        self.action_4 = QtGui.QAction(MainSimulWindow)
        self.action_4.setObjectName(_fromUtf8("action_4"))
        self.action_5 = QtGui.QAction(MainSimulWindow)
        self.action_5.setObjectName(_fromUtf8("action_5"))
        self.action_6 = QtGui.QAction(MainSimulWindow)
        self.action_6.setObjectName(_fromUtf8("action_6"))
        self.action_fast_NewContact = QtGui.QAction(MainSimulWindow)
        self.action_fast_NewContact.setObjectName(_fromUtf8("action_fast_NewContact"))
        self.action = QtGui.QAction(MainSimulWindow)
        self.action.setObjectName(_fromUtf8("action"))
        self.action_AddFastNote = QtGui.QAction(MainSimulWindow)
        self.action_AddFastNote.setObjectName(_fromUtf8("action_AddFastNote"))
        self.action_AddNewContact = QtGui.QAction(MainSimulWindow)
        self.action_AddNewContact.setObjectName(_fromUtf8("action_AddNewContact"))
        self.action_7 = QtGui.QAction(MainSimulWindow)
        self.action_7.setObjectName(_fromUtf8("action_7"))
        self.action_8 = QtGui.QAction(MainSimulWindow)
        self.action_8.setObjectName(_fromUtf8("action_8"))
        self.action_AddNewCP = QtGui.QAction(MainSimulWindow)
        self.action_AddNewCP.setObjectName(_fromUtf8("action_AddNewCP"))

        self.retranslateUi(MainSimulWindow)
        self.Global_tabs.setCurrentIndex(0)
        self.SIM_info_tabs.setCurrentIndex(0)
        self.tabWidget_testsim.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainSimulWindow)

    def retranslateUi(self, MainSimulWindow):
        MainSimulWindow.setWindowTitle(_translate("MainSimulWindow", "Simple Business ", None))
        self.button_home.setText(_translate("MainSimulWindow", "Home", None))
        self.button_zoom.setText(_translate("MainSimulWindow", "Zoom", None))
        self.button_pan.setText(_translate("MainSimulWindow", "Pan", None))
        self.button_saveplot.setText(_translate("MainSimulWindow", "Save plot", None))
        self.SIM_info_tabs.setTabText(self.SIM_info_tabs.indexOf(self.SIM_INF_plot), _translate("MainSimulWindow", "Plot", None))
        self.SIM_info_tabs.setTabText(self.SIM_info_tabs.indexOf(self.SIM_INF_report), _translate("MainSimulWindow", "Report", None))
        self.Global_tabs.setTabText(self.Global_tabs.indexOf(self.tab_Simulation), _translate("MainSimulWindow", "Прогноз", None))
        self.pushButton_log_run_simul_random.setText(_translate("MainSimulWindow", "Случайная эпоха", None))
        self.button_log_run_simul.setText(_translate("MainSimulWindow", "Запуск выбранной эпохи:", None))
        self.tabWidget_testsim.setTabText(self.tabWidget_testsim.indexOf(self.tab_log), _translate("MainSimulWindow", "Лог", None))
        self.tabWidget_testsim.setTabText(self.tabWidget_testsim.indexOf(self.tab_variables), _translate("MainSimulWindow", "Переменные", None))
        self.Global_tabs.setTabText(self.Global_tabs.indexOf(self.tab_SimulLog), _translate("MainSimulWindow", "Тест - симуляция", None))
        self.action_Run_Simulate.setText(_translate("MainSimulWindow", "Запуск симуляции", None))
        self.action_Synhronize_xm_with_db.setText(_translate("MainSimulWindow", "Загрузить из 1С", None))
        self.action_upload_budget_csv.setText(_translate("MainSimulWindow", "Выгрузить в 1С", None))
        self.action_2.setText(_translate("MainSimulWindow", "#ЗапросТовара", None))
        self.action_3.setText(_translate("MainSimulWindow", "#Бюджет", None))
        self.action_4.setText(_translate("MainSimulWindow", "#Офер", None))
        self.action_5.setText(_translate("MainSimulWindow", "#Прайс", None))
        self.action_6.setText(_translate("MainSimulWindow", "#Беседа", None))
        self.action_fast_NewContact.setText(_translate("MainSimulWindow", "Новый контакт", None))
        self.action.setText(_translate("MainSimulWindow", "Заметка", None))
        self.action_AddFastNote.setText(_translate("MainSimulWindow", "+ Быстрая заметка", None))
        self.action_AddNewContact.setText(_translate("MainSimulWindow", "+ Контакт", None))
        self.action_7.setText(_translate("MainSimulWindow", "+ Клиент", None))
        self.action_8.setText(_translate("MainSimulWindow", "+ Поставщик", None))
        self.action_AddNewCP.setText(_translate("MainSimulWindow", "+ Контрагент", None))

from matplotlibwidget import MatplotlibWidget
