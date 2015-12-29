# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
# import sys
# import datetime
# import convert
import simple_locale

from ui.ui_ModernMainWindow_v2 import Ui_MainWindowModern
# from ui.ui_Dialog_EditPrice import *
# from ui.ui_Dialog_EditMatFlow import *
# from ui.ui_DialogCrm_EditSimpleRecord import *
# from ui.ui_DialogCrm_EditCounterparty import *
# from ui.ui_DialogCrm_EditContact import *
# from ui.ui_Dialog_EditSalesOppotunity import *
# from ui.manually.table import *
# from ui.manually.tag_lighter import *
# from ui.manually.popup_text_editor import *
# from ui.manually.parser_browser import gui_ParsingBrowser

# Import custom gui logic
from gui_forms_logic.data_models import cDataModel_CounterpartyList
from gui_forms_logic.record_mediators import cMedPrice, cMedMatFlow, cSimpleMediator
from gui_forms_logic.frame_builder import LabelFrame, RecFrame

# from c_planner import c_planner

import db_main
# import xml_synch
# import c_meganode
# import utils
# import random
import gl_shared

# import threading

# unicode_codec = QtCore.QTextCodec.codecForName(simple_locale.ultimate_encoding)
#
# cnf = gl_shared.ConfigParser.ConfigParser()
#
# cnf.read('.\__secret\main.ini')
# user_name = unicode(cnf.get("UserConfig","UserName").decode("cp1251"))
# is_user_admin = unicode(cnf.getboolean("UserConfig","IsAdmin"))
# user_email = cnf.get("UserConfig","PersonalEmail").decode("cp1251")
# user_group_email = cnf.get("UserConfig","GroupEmail").decode("cp1251")
# cnf = None
#
# TabNums = {"CPs":0, "KnBase":1}

# Constants #
# ----------#
# Turning on/off styles
STYLES = False
STYLE_URL = None
# How many lines to load first time
RECORDS_NUM = 4

class gui_MainWindow(QtGui.QMainWindow,Ui_MainWindowModern):

    def __init__(self, app, parent=None):
        super(gui_MainWindow, self).__init__(parent)
        self.app = app
        self.setupUi(self)


        # Loading stylesheets
        if STYLES:
                style_sheet_src = QtCore.QFile('C:\Ilua\qt4_rnd\ui\Stylesheets\scheme.qss')
                style_sheet_src.open(QtCore.QIODevice.ReadOnly)
                if style_sheet_src.isOpen():
                    self.setStyleSheet(QtCore.QVariant(style_sheet_src.readAll()).toString())
                style_sheet_src.close()


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

        # Right-side logic
        self.mediators_frame_list = []

        # Placing QScrollArea
        self.scroll_area = QtGui.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFocusPolicy(QtCore.Qt.NoFocus)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        # adding Scrollbar to QScrollArea
        self.scr_bar = QtGui.QScrollBar()
        self.scroll_area.setVerticalScrollBar(self.scr_bar)
        # put QScrollArea in main window
        self.horizontalLayout_2.addWidget(self.scroll_area)

        # inserting vertical layout at right
        self.mediators_list_layout = QtGui.QVBoxLayout()
        self.Base_widget = QtGui.QWidget()
        self.Base_widget.setLayout(self.mediators_list_layout)
        # setting Widget for QScrollArea
        self.scroll_area.setWidget(self.Base_widget)

        # (((o))) connect signals to methods
        # TODO implement scroll event
        # self.scr_bar.valueChanged.connect(self.scrolled)


    def click_on_CP(self, index_to, index_from):
        cp_i = index_to.data(35).toPyObject()
        if cp_i is None:
            return

        #
        # while True:
        #     try:
        #         iterator = self._iter_cp_mediator(cp_i)
        #         print(iterator.next().label)
        #     except StopIteration:
        #         break

        for med_i in self._iter_cp_mediator(cp_i):
            # Идём по очереди по представителям данных
            self.make_frame_from_mediator(med_i)
            # print unicode(med_i.label) + ' id : ' + str(id(med_i))



            # print(med_i.label)
            # print(med_i.get_HTML())
            # for f_i in med_i.iter_fields():
            #     print(f_i.field_repr + " : " + str(f_i.field_value))
            # for g_i in med_i.iter_button_calls():
            #     print(g_i.field_repr + " : " + str(g_i.field_value))
            #     g_i()  # вот так просто вызывать
            #

    def _iter_cp_mediator(self, cp):
        '''
        Передаем сюда любого контрагента, получаем в ответ список связанных записей (медиаторов).
        Их можно потом построить при помощи Frame. Фактически, тут к записи привязываются вызовы
        и поля, которые можно потом аккуратно вывести и на gui автоматом.
        Args:
            cp: Контрагент
        Returns: лист медиаторов разного рода для записей, связанных с контрагентом
        '''

        # Цены (как покупателю, так и от поставщика)
        header = cSimpleMediator(self)
        header.set_label(u'Цены')
        header.add_call('dlg_add_price', u'Добавить цену')
        yield header
        for pr_i in db_main.get_prices_list(cp):
            new_med = cMedPrice(self, pr_i)
            new_med.add_call('dlg_edit_price', u'Редактировать', pr_i)
            new_med.add_call('dlg_delete_price', u'Удалить', pr_i)
            yield new_med

        # Список линий покупки
        if cp.discriminator == 'client':
            header = cSimpleMediator(self)
            header.set_label(u'Потоки снабжения')
            header.add_call('dlg_add_matflow', u'Добавить линию снабжения')
            yield header
            for mf_i in db_main.get_mat_flows_list(cp):
                print(mf_i)
                new_med = cMedMatFlow(self, mf_i)
                new_med.add_call('dlg_edit_matflow', u'Редактировать', mf_i)
                new_med.add_call('dlg_delete_matflow', u'Удалить', mf_i)
                yield new_med

    def dlg_add_price(self):
        print("adding new price ")

    def dlg_edit_price(self, price_instance):
        print("editing " + str(price_instance))

    def dlg_delete_price(self, price_instance):
        print("deleting " + str(price_instance))

    def dlg_add_matflow(self):
        print("adding new matflow ")

    def dlg_edit_matflow(self, matflow_instance):
        print("editing " + str(matflow_instance))

    def dlg_delete_matflow(self, matflow_instance):
        print("deleting " + str(matflow_instance))

    def make_frame_from_mediator(self, mediator):
        """
            Automatically building gui for each mediator
        :param mediator: incoming mediator class instance
        :return: None
        """

        if mediator.label != '':
            new_frame = LabelFrame(mediator, self)
            self.mediators_frame_list.append(new_frame)
            self.mediators_list_layout.addWidget(new_frame)

        new_frame_2 = RecFrame(mediator, self)
        self.mediators_frame_list.append(new_frame_2)
        self.mediators_list_layout.addWidget(new_frame_2)





