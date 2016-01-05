# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
from ui.ui_DataCheckWindow import Ui_MainDataWindow

import db_main
import admin_scripts

class gui_MainDataWindow(QtGui.QMainWindow, Ui_MainDataWindow):
    def __init__(self, app, parent=None):
        super(gui_MainDataWindow, self).__init__(parent)
        self.app = app
        self.setupUi(self)
        self.connect(self.treeWidget_InitialData,QtCore.SIGNAL("itemSelectionChanged()"), self.build_report_initial_data)
        self.refresh_initial_data_list()
        self.pushButton_LoadFrom1C.clicked.connect(self.load_from_1C)
        self.pushButton_Refresh.clicked.connect(self.refresh_initial_data_list)

    def build_report_initial_data(self):
        cur_item = self.treeWidget_InitialData.currentItem()
        report = cur_item.data(0,32).toPyObject()
        self.textBrowser_InitialData.setHtml(report.get_html())

    def load_from_1C(self):
        mng = admin_scripts.c_admin_tasks_manager()
        mng.add_task(admin_scripts.c_read_lists_from_1C_task())
        mng.add_task(admin_scripts.c_read_logs_from_1C_task())
        mng.add_task(admin_scripts.c_read_dynamic_data_from_1C_task())
        mng.add_task(admin_scripts.c_read_generalinfo_from_1C_task())
        mng.add_task(admin_scripts.c_update_ccy_stats())
        mng.add_task(admin_scripts.c_build_excessive_links())
        mng.run_tasks()

    def refresh_initial_data_list(self):
        tree = self.treeWidget_InitialData
        tree.clear()
        for it_i in db_main.get_initial_data_report_tree():
            an_item = QtGui.QTreeWidgetItem()
            an_item.setText(0, it_i.get_name())
            an_item.setData(0, 32, it_i)
            tree.addTopLevelItem(an_item)
