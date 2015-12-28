# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
import sys
import datetime
import convert
import simple_locale

from ui.ui_ModernMainWindow import Ui_MainWindowModern
from ui.ui_Dialog_EditPrice import *
from ui.ui_Dialog_EditMatFlow import *
from ui.ui_DialogCrm_EditSimpleRecord import *
from ui.ui_DialogCrm_EditCounterparty import *
from ui.ui_DialogCrm_EditContact import *
from ui.ui_Dialog_EditSalesOppotunity import *
from ui.manually.table import *
from ui.manually.tag_lighter import *
from ui.manually.popup_text_editor import *
from ui.manually.parser_browser import gui_ParsingBrowser

# Import custom gui logic
from gui_forms_logic.data_models import cDataModel_CounterpartyList

from c_planner import c_planner

import db_main
import xml_synch
import c_meganode
import utils
import random
import gl_shared

import threading

unicode_codec = QtCore.QTextCodec.codecForName(simple_locale.ultimate_encoding)

cnf = gl_shared.ConfigParser.ConfigParser()

cnf.read('.\__secret\main.ini')
user_name = unicode(cnf.get("UserConfig","UserName").decode("cp1251"))
is_user_admin = unicode(cnf.getboolean("UserConfig","IsAdmin"))
user_email = cnf.get("UserConfig","PersonalEmail").decode("cp1251")
user_group_email = cnf.get("UserConfig","GroupEmail").decode("cp1251")
cnf = None

TabNums = {"CPs":0, "KnBase":1}

class gui_MainWindow(QtGui.QMainWindow,Ui_MainWindowModern):

    def __init__(self, app, parent=None):
        super(gui_MainWindow, self).__init__(parent)
        self.app = app
        self.setupUi(self)

        ############
        # Counterparty tab
        ############

        # Left-side logic

        self.data_model_counterparties = cDataModel_CounterpartyList()
        self.data_model_counterparties_proxy = QtGui.QSortFilterProxyModel()
        self.data_model_counterparties_proxy.setSourceModel(self.data_model_counterparties)
        self.data_model_counterparties_proxy.setDynamicSortFilter(True)
        self.data_model_counterparties_proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

        self.listView_ClientList.setModel(self.data_model_counterparties)
        self.lineEdit_ClientFilter.textChanged.connect(self.data_model_counterparties_proxy.setFilterRegExp)

        self.listView_ClientList.selectionModel().currentChanged.connect(self.click_on_CP)


    def click_on_CP(self, index_to, index_from):
        a_rec = index_to.data(35).toPyObject()
        if not(a_rec is None):
            print(a_rec)




