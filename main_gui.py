# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
import sys
import datetime
import convert
import simple_locale

from ui.ui_MainWindow import *
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

from c_planner import c_planner

import db_main
import xml_synch
import c_meganode
import utils
import random
import gl_shared

import threading

from c_simulation_results_container import iter_dataframe_reports

from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar

unicode_codec = QtCore.QTextCodec.codecForName(simple_locale.ultimate_encoding)

cnf = gl_shared.ConfigParser.ConfigParser()

cnf.read('.\__secret\main.ini')
user_name = unicode(cnf.get("UserConfig","UserName").decode("cp1251"))
is_user_admin = unicode(cnf.getboolean("UserConfig","IsAdmin"))
user_email = cnf.get("UserConfig","PersonalEmail").decode("cp1251")
user_group_email = cnf.get("UserConfig","GroupEmail").decode("cp1251")
cnf = None

TabNums = {"CPs":0, "Contacts":1, "KnBase":2, "Processes":3, "Forecast":4, "TestSim":5, "Data":6}

def send_background_email_to_group(a_subj, a_body):
    # TODO: do I have to clean this thread?..
    try:
        utils.do_send_bot_email([user_group_email], a_subj, a_body)
    except:
        print "Unable to send e-mail to " + user_group_email
        print gl_shared.traceback.format_exc()

def try_send_email_about_new_record(new_crm_rec):
    subj = u"[INT-news][%s] %s [Theme: %s]"%(user_name,new_crm_rec.headline, new_crm_rec.hashtags_string)
    body = new_crm_rec.long_html_text
    t_email = threading.Thread(target=send_background_email_to_group, args=(subj, body))
    t_email.start()

def qtdate_unpack(a_qdate):
    return a_qdate.toPyDate() #Говорят, такая незадукоментированная штука есть

def qtdate_pack(a_datetime):
    return QtCore.QDate(a_datetime.year, a_datetime.month, a_datetime.day)

class gui_MainWindow(QtGui.QMainWindow,Ui_MainWindow):

    def __init__(self,app, parent=None):
        super(gui_MainWindow, self).__init__(parent)
        self.app = app
        self.setupUi(self) #method build by form designer - puts all the widgets at their place
        ##################################################################
        if not(is_user_admin):
            self.action_Run_Simulate.setEnabled(False)
            self.action_Synhronize_xm_with_db.setEnabled(False)
            self.action_upload_budget_csv.setEnabled(False)
        #Инициализирую "модели данных" (привязка - ниже)
        self.gui_models_mat_flows_table = gui_client_material_flows_model()
        self.gui_models_sales_leads_table = gui_client_sales_leads_model()
        self.gui_models_client_prices_table = gui_client_prices_table_model()
        self.gui_models_supplier_prices_table = gui_supplier_prices_table_model()
        self.gui_models_testsimlog_table = gui_testsimlog_table_model()

        self.gui_models_projects_tree = gui_project_tree_model()

        self.gui_models_agent_type_list = gui_agent_type_list_model()

        self.gui_models_contacts = gui_contacts_model()
        self.gui_models_contacts_proxy = QtGui.QSortFilterProxyModel()
        self.gui_models_contacts_proxy.setSourceModel(self.gui_models_contacts)
        self.gui_models_contacts_proxy.setDynamicSortFilter(True)
        self.gui_models_contacts_proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

        self.gui_models_counterparty_tree = gui_counterparty_tree_model()
        self.gui_models_counterparty_tree_proxy = QtGui.QSortFilterProxyModel()
        self.gui_models_counterparty_tree_proxy.setSourceModel(self.gui_models_counterparty_tree)
        self.gui_models_counterparty_tree_proxy.setDynamicSortFilter(True)
        self.gui_models_counterparty_tree_proxy.setFilterKeyColumn(0)
        self.gui_models_counterparty_tree_proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

        self.gui_models_knbase_list = gui_knbase_model()
        self.gui_models_knbase_list_proxy = QtGui.QSortFilterProxyModel()
        self.gui_models_knbase_list_proxy.setSourceModel(self.gui_models_knbase_list)
        self.gui_models_knbase_list_proxy.setDynamicSortFilter(True)
        self.gui_models_knbase_list_proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

        self.gui_models_knbase_hashtag_list = gui_knbase_hashtag_model()
        self.gui_models_knbase_hashtag_list_proxy = QtGui.QSortFilterProxyModel()
        self.gui_models_knbase_hashtag_list_proxy.setSourceModel(self.gui_models_knbase_hashtag_list)
        self.gui_models_knbase_hashtag_list_proxy.setDynamicSortFilter(True)
        self.gui_models_knbase_hashtag_list_proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

        self.gui_models_testsim_varlist = gui_testsim_varlist_model()
        self.gui_models_testsim_varlist_proxy = QtGui.QSortFilterProxyModel()
        self.gui_models_testsim_varlist_proxy.setSourceModel(self.gui_models_testsim_varlist)
        self.gui_models_testsim_varlist_proxy.setDynamicSortFilter(True)
        self.gui_models_testsim_varlist_proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

        self.gui_models_mainsim_varlist = gui_mainsim_varlist_model()
        self.gui_models_mainsim_varlist_proxy = QtGui.QSortFilterProxyModel()
        self.gui_models_mainsim_varlist_proxy.setSourceModel(self.gui_models_mainsim_varlist)
        self.gui_models_mainsim_varlist_proxy.setDynamicSortFilter(True)
        self.gui_models_mainsim_varlist_proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

        self.gui_models_testsimlog_table_proxy = QtGui.QSortFilterProxyModel()
        self.gui_models_testsimlog_table_proxy.setSourceModel(self.gui_models_testsimlog_table)
        self.gui_models_testsimlog_table_proxy.setDynamicSortFilter(True)
        self.gui_models_testsimlog_table_proxy.setFilterKeyColumn(1)
        self.gui_models_testsimlog_table_proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        ##################################################################
        self.DlgEditSimpleRecord = None
        self.DlgEditContact = None
        self.DlgEditCPdata = None
        self.DlgEditSalesOppotunity = None
        self.DlgEditPrice = None
        self.DlgEditMatFlow = None


        ##################################################################
        #Глобальнее вкладки
        self.Global_tabs.currentChanged.connect(self.update_ui_tab_change)
        self.connect(self.action_Synhronize_xm_with_db, QtCore.SIGNAL("triggered()"),self.write_db)  #Синхронизация
        self.connect(self.action_upload_budget_csv, QtCore.SIGNAL("triggered()"), self.upload_budget_csv)
        self.connect(self.action_Run_Simulate, QtCore.SIGNAL("triggered()"), self.action_run_simulation)
        self.connect(self.action_AddFastNote, QtCore.SIGNAL("triggered()"), self.add_crm_blank_record)
        self.connect(self.action_AddNewContact, QtCore.SIGNAL("triggered()"), self.add_crm_contact)
        self.connect(self.action_AddNewCP, QtCore.SIGNAL("triggered()"), self.crm_add_new_counterparty)
        ##################################################################
        #Вкладка с компаниями
        self.treeView_counterparties.setModel(self.gui_models_counterparty_tree_proxy)
        self.connect(self.lineEdit_find_counterparty, QtCore.SIGNAL("textChanged(QString)"), self.gui_models_counterparty_tree_proxy.setFilterRegExp)
        self.tableView_client_material_flows.setModel(self.gui_models_mat_flows_table)
        self.tableView_client_oppotunities.setModel(self.gui_models_sales_leads_table)
        self.tableView_prices.setModel(self.gui_models_client_prices_table)
        self.tableView_SupplierPrices.setModel(self.gui_models_supplier_prices_table)

        self.connect(self.tableView_client_material_flows,QtCore.SIGNAL("doubleClicked(QModelIndex)"),self.edit_material_flow_to_client)
        self.connect(self.tableView_prices,QtCore.SIGNAL("doubleClicked(QModelIndex)"),self.edit_price_to_client)
        self.connect(self.tableView_SupplierPrices,QtCore.SIGNAL("doubleClicked(QModelIndex)"),self.edit_price_to_supplier)
        self.connect(self.tableView_client_oppotunities,QtCore.SIGNAL("doubleClicked(QModelIndex)"),self.edit_sales_lead_to_client)

        self.connect(self.treeView_counterparties.selectionModel(), QtCore.SIGNAL("currentChanged(QModelIndex, QModelIndex)"), self.click_on_a_counterparty)
        self.connect(self.but_estimate_ship_stats,QtCore.SIGNAL("clicked()"),self.estimate_mat_flows)
        self.connect(self.pushButton_AddPriceToClient,QtCore.SIGNAL("clicked()"),self.add_price_to_client)
        self.connect(self.pushButton_EditPriceToClient,QtCore.SIGNAL("clicked()"),self.edit_price_to_client)
        self.connect(self.pushButton_DeletePriceFromClient,QtCore.SIGNAL("clicked()"),self.delete_price_to_client)
        self.connect(self.pushButton_AddMaterialFlowToClient,QtCore.SIGNAL("clicked()"),self.add_material_flow_to_client)
        self.connect(self.pushButton_EditMaterialFlowFromClient,QtCore.SIGNAL("clicked()"),self.edit_material_flow_to_client)
        self.connect(self.pushButton_DeleteMaterialFlowFromClient,QtCore.SIGNAL("clicked()"),self.delete_material_flow_to_client)
        #self.connect(self.pushButton_HashClientRequest, QtCore.SIGNAL("clicked()"), self.crm_add_client_request)
        self.connect(self.pushButton_HashClientOffer, QtCore.SIGNAL("clicked()"), self.crm_price_offer)
        self.connect(self.pushButton_HashBudget, QtCore.SIGNAL("clicked()"), self.crm_add_client_cons_budget)
        self.connect(self.pushButton_NewCounterparty, QtCore.SIGNAL("clicked()"), self.crm_add_new_counterparty)
        self.connect(self.pushButton_EditCounterparty, QtCore.SIGNAL("clicked()"), self.crm_edit_counterparty)

        self.connect(self.pushButton_AddPriceToSupplier,QtCore.SIGNAL("clicked()"),self.add_price_to_supplier)
        self.connect(self.pushButton_EditPriceToSupplier,QtCore.SIGNAL("clicked()"),self.edit_price_to_supplier)
        self.connect(self.pushButton_DeletePriceFromSupplier,QtCore.SIGNAL("clicked()"),self.delete_price_to_supplier)
        self.connect(self.pushButton_HashSupplierPrice,QtCore.SIGNAL("clicked()"),self.crm_price_offer_input)

        self.connect(self.pushButton_AddOppToClient,QtCore.SIGNAL("clicked()"),self.add_sales_lead_to_client)
        self.connect(self.pushButton_EditOppClient,QtCore.SIGNAL("clicked()"),self.edit_sales_lead_to_client)
        self.connect(self.pushButton_DeleteOppClient,QtCore.SIGNAL("clicked()"),self.delete_sales_lead_to_client)

        self.connect(self.pushButton_ToCPKnBase, QtCore.SIGNAL("clicked()"),self.goto_knbase_from_cp)
        self.connect(self.pushButton_ToCPKnBase_Consumption, QtCore.SIGNAL("clicked()"),self.goto_knbase_from_cp_cons)
        self.connect(self.pushButton_ToCPKnBase_offers, QtCore.SIGNAL("clicked()"),self.goto_knbase_from_cp_cons)
        self.connect(self.pushButton_ToCPKnBase_offers, QtCore.SIGNAL("clicked()"),self.goto_knbase_from_cp_offers)
        self.connect(self.pushButton_ToCPKnBase_prices, QtCore.SIGNAL("clicked()"),self.goto_knbase_from_cp_prices)

        ##################################################################
        # Вкладка с Базой Знаний
        self.connect(self.pushButton_KnBaseEmptyNote, QtCore.SIGNAL("clicked()"), self.add_crm_blank_record)
        self.connect(self.pushButton_PrintKnBaseView, QtCore.SIGNAL("clicked()"), self.print_kn_base_selection)
        # По тематике
        self.listView_KnBaseHashtags.setModel(self.gui_models_knbase_hashtag_list_proxy)
        self.connect(self.lineEdit_KnBaseSearchHahtag, QtCore.SIGNAL("textChanged(QString)"), self.gui_models_knbase_hashtag_list_proxy.setFilterRegExp)
        self.connect(self.listView_KnBaseHashtags.selectionModel(), QtCore.SIGNAL("currentChanged(QModelIndex, QModelIndex)"), self.crm_click_on_hashtag)
        self.connect(self.pushButton_SwitchFromHashtagToRecords, QtCore.SIGNAL("clicked()"), self.crm_from_hashtag_to_records)
        self.connect(self.pushButton_RenameHashtag, QtCore.SIGNAL("clicked()"), self.crm_knbase_rename_hashtag)
        self.connect(self.pushButton_update_themefilt, QtCore.SIGNAL("clicked()"),self.knbase_apply_themefilter)
        # По записям
        self.listView_KnBase.setModel(self.gui_models_knbase_list_proxy)
        self.connect(self.lineEdit_SearchHashKnBase, QtCore.SIGNAL("textChanged(QString)"), self.knbase_easy_search_record)
        self.connect(self.listView_KnBase.selectionModel(), QtCore.SIGNAL("currentChanged(QModelIndex, QModelIndex)"), self.crm_click_on_record)
        self.connect(self.pushButton_AddNoteKnBase, QtCore.SIGNAL("clicked()"), self.add_crm_blank_record)
        self.connect(self.pushButton_EditNoteKnBase, QtCore.SIGNAL("clicked()"), self.edit_crm_record)
        self.connect(self.pushButton_DeleteNoteKnBase, QtCore.SIGNAL("clicked()"), self.delete_crm_record)
        self.connect(self.pushButton_KnBaseRunRecordSearch, QtCore.SIGNAL("clicked()"), self.knbase_deep_search_record)
        # Эксперимент со ссылками
        self.textBrowser_KnBase = gui_ParsingBrowser(self)
        self.horizontalLayout_textBrowser_KnBase.addWidget(self.textBrowser_KnBase)
        self.connect(self.textBrowser_KnBase, QtCore.SIGNAL("anchorClicked(QUrl)"), self.navigate_KnBase)
        self.textBrowser_KnBase.setOpenLinks(False)
        ##################################################################
        # Вкладка с контактами
        self.connect(self.pushButton_add_contact, QtCore.SIGNAL("clicked()"), self.add_crm_contact)
        self.connect(self.pushButton_edit_contact, QtCore.SIGNAL("clicked()"), self.edit_crm_contact)
        self.connect(self.pushButton_delete_contact, QtCore.SIGNAL("clicked()"), self.delete_crm_contact)
        self.listView_contacts.setModel(self.gui_models_contacts_proxy)
        self.connect(self.listView_contacts.selectionModel(), QtCore.SIGNAL("currentChanged(QModelIndex, QModelIndex)"), self.crm_click_on_contact)
        self.connect(self.lineEdit_search_contact, QtCore.SIGNAL("textChanged(QString)"), self.gui_models_contacts_proxy.setFilterRegExp)
        self.connect(self.pushButton_WriteALetterToContact, QtCore.SIGNAL("clicked()"),self.crm_contact_compose_email)
        ##################################################################
        #Вкладка с графиками (Simulation)
        #Обновление дерева обсерверов
        self.listView_main_sim.setModel(self.gui_models_mainsim_varlist_proxy)
        self.connect(self.listView_main_sim.selectionModel(), QtCore.SIGNAL("currentChanged(QModelIndex, QModelIndex)"), self.build_simulation_reports)
        self.connect(self.lineEdit_find_var_mainsim, QtCore.SIGNAL("textChanged(QString)"), self.gui_models_mainsim_varlist_proxy.setFilterRegExp)
        self.connect(self.button_zoom,QtCore.SIGNAL("clicked()"), self.zoom)
        self.connect(self.button_pan,QtCore.SIGNAL("clicked()"), self.pan)
        self.connect(self.button_home,QtCore.SIGNAL("clicked()"), self.home)
        self.connect(self.button_saveplot,QtCore.SIGNAL("clicked()"), self.palette)
        #Тулбарчик манипуляций над графиком
        self.toolbar = NavigationToolbar(self.SIM_INF_mpl_plot.figure.canvas, self)
        self.toolbar.hide()
        ##################################################################
        #Вкладка с проектами (Projects)
        self.project_tree_view.setModel(self.gui_models_projects_tree)  #Инициализация "модели" выше
        self.connect(self.project_tree_view.selectionModel(), QtCore.SIGNAL("currentChanged(QModelIndex, QModelIndex)"), self.click_on_project_tree)
        self.connect(self.but_projects_set_finished,QtCore.SIGNAL("clicked()"),self.set_project_node_finished)  #Временное решение
        ##################################################################
        #Вкладка с начальными данными
        self.connect(self.treeWidget_InitialData,QtCore.SIGNAL("itemSelectionChanged()"), self.build_report_initial_data)
        ##################################################################
        #Вкладка с тестовыми симуляциями (Log)
        self.connect(self.button_log_run_simul, QtCore.SIGNAL("clicked()"), self.run_test_simulation_selected_seed)
        self.connect(self.pushButton_log_run_simul_random, QtCore.SIGNAL("clicked()"), self.run_test_simulation_random_seed)
        self.log_table_browser.setModel(self.gui_models_testsimlog_table_proxy)
        self.listView_log_var_list.setModel(self.gui_models_testsim_varlist_proxy)
        self.connect(self.lineEdit_SearchInLog, QtCore.SIGNAL("textChanged(QString)"), self.gui_models_testsimlog_table_proxy.setFilterRegExp)
        self.connect(self.lineEdit_testsim_findvar, QtCore.SIGNAL("textChanged(QString)"), self.gui_models_testsim_varlist_proxy.setFilterRegExp)
        self.connect(self.listView_log_var_list.selectionModel(), QtCore.SIGNAL("currentChanged(QModelIndex, QModelIndex)"), self.log_show_a_variable)
        ##################################################################
        #Выход
        #TODO: закрыть сессию по закрытию окошка
        ##################################################################
        self.startUi()

    def get_DlgEditSimpleRecord(self):
        if self.DlgEditSimpleRecord is None:
            self.DlgEditSimpleRecord = gui_DialogCrm_EditSimpleRecord(self)
        return self.DlgEditSimpleRecord

    def get_DlgEditContact(self):
        if self.DlgEditContact is None:
            self.DlgEditContact = gui_DialogCrm_EditContact(self)
        return self.DlgEditContact

    def get_DlgEditCPdata(self):
        if self.DlgEditCPdata is None:
            self.DlgEditCPdata = gui_DialogCrm_EditCounterpartyData(self)
        return self.DlgEditCPdata

    def get_DlgEditSalesOppotunity(self):
        if self.DlgEditSalesOppotunity is None:
            self.DlgEditSalesOppotunity = gui_Dialog_EditSalesOppotunity(self)
        return self.DlgEditSalesOppotunity

    def get_DlgEditPrice(self):
        if self.DlgEditPrice  is None:
            self.DlgEditPrice = gui_Dialog_EditPrice(self)
        return self.DlgEditPrice

    def get_DlgEditMatFlow(self):
        if self.DlgEditMatFlow  is None:
            self.DlgEditMatFlow = gui_Dialog_EditMatFlow(self)
        return self.DlgEditMatFlow

    def update_ui_tab_change(self, tab_num):
        #При смене вкладки обновляем содержимое
        tab_wid = self.Global_tabs.widget(tab_num)
        if tab_wid:
            if tab_wid.objectName() == "tab_SupplyChainManagment":
                self.gui_models_projects_tree.updateNodeTree()
            elif tab_wid.objectName() == "tab_Clients":      #Clients
                self.gui_models_counterparty_tree.update_counterparty_tree()
                self.gui_models_counterparty_tree_proxy.sort(1, QtCore.Qt.AscendingOrder)
                self.text_client_report.setHtml("")
                # TODO: обнуление текста
            elif tab_wid.objectName() == "tab_Simulation":      #Simulation
                self.gui_models_mainsim_varlist.update_with_observations()
            elif tab_wid.objectName() == "tab_SimulLog":      #Log
                self.update_log_lists()
            elif tab_wid.objectName() == "tab_InitialData":      #Initial data
                self.refresh_initial_data_list()
            elif tab_wid.objectName() == "tab_KnBase":
                self.gui_models_knbase_list.update_list()
                self.gui_models_knbase_hashtag_list.update_list()
            elif tab_wid.objectName() == "tab_Contacts":
                self.gui_models_contacts.update_list()

    def startUi(self):
        #Проверить, что в update_ui_tab_change и startUi все одинаково
        #Model-based тут не надо - они и так собираются при старте
        self.update_log_lists()
        self.refresh_initial_data_list()
        self.gui_models_counterparty_tree_proxy.sort(1, QtCore.Qt.AscendingOrder)

    def action_run_simulation(self):
        the_planner = c_planner()
        param_dict = db_main.the_settings_manager.get_simul_settings()
        the_planner.run_observed_simulation(param_dict["epoch_num"], param_dict["until"])
        self.gui_models_mainsim_varlist.update_with_observations()
        self.update_log_lists()

    def write_db(self):
        # xml_synch.synch_with_1C_xml()
        # self.startUi() #Обновим списки
        pass

    def upload_budget_csv(self):
        # #TODO: еще добавить обработку при обновлении конкретного matflow
        # #Печатаем ожидания о потреблении в файлик.
        # print(u"Обновляю бюджет продаж...")
        # db_main.fix_sales_budget()
        # print(u"Выгружаю бюджет продаж...")
        # xml_synch.print_budget_to_csv()
        # print(u"Бюджет продаж выгружен.")
        pass

    def refresh_initial_data_list(self):
        tree = self.treeWidget_InitialData
        tree.clear()
        for it_i in db_main.get_initial_data_report_tree():
            an_item = QtGui.QTreeWidgetItem()
            an_item.setText(0, it_i.get_name())
            an_item.setData(0,32,it_i)
            tree.addTopLevelItem(an_item)

    def build_report_initial_data(self):
        cur_item = self.treeWidget_InitialData.currentItem()
        report = cur_item.data(0,32).toPyObject()
        self.textBrowser_InitialData.setHtml(report.get_html())

    def click_on_a_counterparty(self, index_to, index_from):
        an_agent = index_to.data(35).toPyObject()
        if an_agent is not None:
            report = db_main.the_report_filler.get_report_for_object(an_agent)
            self.text_client_report.setHtml(report.get_html())
            if an_agent.discriminator == "client":
                self.refresh_material_flow_table(an_agent)
                self.refresh_sales_leads_table(an_agent)
                self.refresh_prices_table(an_agent)
                self.tab_counterparty_settings.setTabEnabled(1, True)
                self.tab_counterparty_settings.setTabEnabled(2, True)
                self.tab_counterparty_settings.setTabEnabled(3, True)
                self.tab_counterparty_settings.setTabEnabled(4, False)
            elif an_agent.discriminator == "supplier":
                self.refresh_supplier_prices_table(an_agent)
                self.tab_counterparty_settings.setTabEnabled(1, False)
                self.tab_counterparty_settings.setTabEnabled(2, False)
                self.tab_counterparty_settings.setTabEnabled(3, False)
                self.tab_counterparty_settings.setTabEnabled(4, True)
            elif an_agent.discriminator == "agent":
                self.tab_counterparty_settings.setTabEnabled(1, False)
                self.tab_counterparty_settings.setTabEnabled(2, False)
                self.tab_counterparty_settings.setTabEnabled(3, False)
                self.tab_counterparty_settings.setTabEnabled(4, False)
        else:
            self.tab_counterparty_settings.setTabEnabled(1, False)
            self.tab_counterparty_settings.setTabEnabled(2, False)
            self.tab_counterparty_settings.setTabEnabled(3, False)
            self.tab_counterparty_settings.setTabEnabled(4, False)
            a_node = index_to.data(55).toPyObject()
            if a_node.typeInfo() == "GROUP":
                s = ""
                for ag_i in a_node.iter_all_agents_in_a_group():
                    s += unicode(ag_i.name) + u"<br>"
                self.text_client_report.setHtml(s)
            else:
                self.text_client_report.setHtml("")

    def get_selected_counterparty(self):
        cp_index = self.treeView_counterparties.currentIndex()
        cp_model = cp_index.data(35).toPyObject()
        return cp_model

    def estimate_mat_flows(self):
        client_model = self.get_selected_counterparty()
        if client_model is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Вы не выбрали клиента, необходимо выбрать"))
        else:
            a_msg = u"Будет произведена переоценка потребления всех материалов по клиенту " + unicode(client_model.name) +\
                    u", действие нельзя отменить - подтверждаете операцию?"
            a_reply = QtGui.QMessageBox.question(self, unicode(u'Подтвердите'), a_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
            if a_reply == QtGui.QMessageBox.Yes:
                client_model.update_stats_on_material_flows(db_main.estimate_shipment_stats(client_model))
                for mf_i in client_model.material_flows:
                    db_main.the_session_handler.merge_object_to_session(mf_i)
                db_main.the_session_handler.commit_session()
                self.refresh_material_flow_table(client_model)
                #Создаём заметку в базе (предлагаем создать)
                edit_dialog = self.get_DlgEditSimpleRecord()
                htmltext_template = db_main.crm_template_new_budget(client_model)
                htmltext_template += u" статистика потребления"
                edit_dialog.set_state_to_add_new([], htmltext_template, u"Бюджет продаж - статистика")
                ans = edit_dialog.run_dialog()
                if ans[0] == 1:
                    db_main.the_session_handler.add_object_to_session(ans[1])
                    db_main.the_session_handler.commit_session()

    def refresh_material_flow_table(self, cl_model):
        self.gui_models_mat_flows_table.update_material_flow_table(cl_model)

    def refresh_sales_leads_table(self, cl_model):
        self.gui_models_sales_leads_table.update_table(cl_model)

    def refresh_prices_table(self,cl_model):
        self.gui_models_client_prices_table.update_prices_table(cl_model)

    def refresh_supplier_prices_table(self, supp_model):
        self.gui_models_supplier_prices_table.update_prices_table(supp_model)

    def add_price_to_client(self):
        client_model = self.get_selected_counterparty()
        if client_model is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Вы не выбрали клиента, необходимо выбрать"))
        elif client_model.discriminator <> 'client':
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Вы выбрали не клиента, выберите клиента"))
        else:
            edit_dialog = self.get_DlgEditPrice()
            edit_dialog.set_state_to_add_new(client_model)
            ans = edit_dialog.run_dialog()
            if ans[0] == 1:
                #Записали в базу данных
                db_main.the_session_handler.add_object_to_session(ans[1])
                db_main.the_session_handler.commit_session()
                #Не забыли добавить в табличку
                self.gui_models_client_prices_table.insertNewPrice(ans[1])
                # TODO: заметку кинуть

    def edit_price_to_client(self):
        pr_indx = self.tableView_prices.currentIndex()
        price_inst = pr_indx.data(45).toPyObject()  #45ая роль - получаем всю переменную
        if price_inst is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Вы не выбрали цену для редактирования"))
        else:
            edit_dialog = self.get_DlgEditPrice()
            edit_dialog.set_state_to_edit(price_inst)
            ans = edit_dialog.run_dialog()
            if ans[0] == 1:
                #Записали в базу данных
                db_main.the_session_handler.commit_session()
                #Не забыли обновить табличку
                self.gui_models_client_prices_table.changeExistingPrice(pr_indx)
                # TODO: заметку кинуть

    def delete_price_to_client(self):
        pr_indx = self.tableView_prices.currentIndex()
        price_inst = pr_indx.data(45).toPyObject()  #45ая роль - получаем всю переменную
        if price_inst is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Вы не выбрали цену для удаления"))
        else:
            a_msg = unicode(u"Подтверждаете удаление цены на ")
            if price_inst.is_for_group:
                a_msg +=  unicode(price_inst.material_type.material_type_name)
            else:
                a_msg +=  unicode(price_inst.material.material_name)
            a_msg += unicode(u" ?")
            a_reply = QtGui.QMessageBox.question(self, unicode(u'Подтвердите'), a_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
            if a_reply == QtGui.QMessageBox.Yes:
                db_main.the_session_handler.delete_concrete_object(price_inst)
                self.gui_models_client_prices_table.deleteRow(pr_indx)
            # TODO: заметку кинуть

    def add_price_to_supplier(self):
        supplier_model = self.get_selected_counterparty()
        if supplier_model is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Вы не выбрали поставщика, необходимо выбрать"))
        elif supplier_model.discriminator <> 'supplier':
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Вы выбрали не поставщика, выберите поставщика"))
        else:
            edit_dialog = self.get_DlgEditPrice()
            edit_dialog.set_state_to_add_new(supplier_model)
            ans = edit_dialog.run_dialog()
            if ans[0] == 1:
                #Записали в базу данных
                db_main.the_session_handler.add_object_to_session(ans[1])
                db_main.the_session_handler.commit_session()
                #Не забыли добавить в табличку
                self.gui_models_supplier_prices_table.insertNewPrice(ans[1])
                # TODO: заметку кинуть

    def edit_price_to_supplier(self):
        pr_indx = self.tableView_SupplierPrices.currentIndex()
        price_inst = pr_indx.data(45).toPyObject()  #45ая роль - получаем всю переменную
        if price_inst is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Вы не выбрали цену для редактирования"))
        else:
            edit_dialog = self.get_DlgEditPrice()
            edit_dialog.set_state_to_edit(price_inst)
            ans = edit_dialog.run_dialog()
            if ans[0] == 1:
                #Записали в базу данных
                db_main.the_session_handler.commit_session()
                #Не забыли обновить табличку
                self.gui_models_supplier_prices_table.changeExistingPrice(pr_indx)
                # TODO: заметку кинуть

    def delete_price_to_supplier(self):
        pr_indx = self.tableView_SupplierPrices.currentIndex()
        price_inst = pr_indx.data(45).toPyObject()  #45ая роль - получаем всю переменную
        if price_inst is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Вы не выбрали цену для удаления"))
        else:
            a_msg = unicode(u"Подтверждаете удаление цены на ")
            if price_inst.is_for_group:
                a_msg +=  unicode(price_inst.material_type.material_type_name)
            else:
                a_msg +=  unicode(price_inst.material.material_name)
            a_msg += unicode(u" ?")
            a_reply = QtGui.QMessageBox.question(self, unicode(u'Подтвердите'), a_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
            if a_reply == QtGui.QMessageBox.Yes:
                db_main.the_session_handler.delete_concrete_object(price_inst)
                self.gui_models_supplier_prices_table.deleteRow(pr_indx)
            # TODO: заметку кинуть

    def add_material_flow_to_client(self):
        client_model = self.get_selected_counterparty()
        if client_model is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Вы не выбрали клиента, необходимо выбрать"))
        else:
            edit_dialog = self.get_DlgEditMatFlow()
            edit_dialog.set_state_to_add_new(client_model)
            ans = edit_dialog.run_dialog()
            if ans[0] == 1:
                a_mf = ans[1]
                #Записали в базу данных
                db_main.the_session_handler.add_object_to_session(a_mf)
                db_main.the_session_handler.commit_session()
                #Не забыли добавить в табличку
                self.gui_models_mat_flows_table.insertNewMatFl(a_mf)
                #Создаём заметку
                edit_dialog = gui_DialogCrm_EditSimpleRecord(self) #Bad idea
                htmltext_template = db_main.crm_template_new_budget_for_new_matflow(a_mf)
                edit_dialog.set_state_to_add_new([], htmltext_template, u"Бюджет продаж - новая линия сбыта")
                ans_2 = edit_dialog.run_dialog()
                if ans_2[0] == 1:
                    db_main.the_session_handler.add_object_to_session(ans_2[1])
                    db_main.the_session_handler.commit_session()
                    try_send_email_about_new_record(new_rec)

    def edit_material_flow_to_client(self):
        mf_indx = self.tableView_client_material_flows.currentIndex()
        mat_fl = mf_indx.data(45).toPyObject()  #45ая роль - получаем всю переменную
        if mat_fl is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Вы не выбрали поток снабжения для редактирования"))
        else:
            old_volume = mat_fl.stats_mean_volume
            old_freq = mat_fl.stats_mean_timedelta
            edit_dialog = self.get_DlgEditMatFlow()
            edit_dialog.set_state_to_edit(mat_fl)
            ans = edit_dialog.run_dialog()
            if ans[0] == 1:
                #Записали в базу данных
                db_main.the_session_handler.commit_session()
                #Не забыли обновить табличку
                self.gui_models_mat_flows_table.changeExistingMatFl(mf_indx)
                #Создаем заметку
                edit_dialog = gui_DialogCrm_EditSimpleRecord(self) #Bad idea
                htmltext_template = db_main.crm_template_change_volume_in_budget(mat_fl, old_volume, old_freq)
                edit_dialog.set_state_to_add_new([], htmltext_template, u"Бюджет продаж - уточнение")
                is_ok, new_rec = edit_dialog.run_dialog()
                if is_ok == 1:
                    db_main.the_session_handler.add_object_to_session(new_rec)
                    db_main.the_session_handler.commit_session()
                    try_send_email_about_new_record(new_rec)

    def delete_material_flow_to_client(self):
        mf_indx = self.tableView_client_material_flows.currentIndex()
        mat_fl = mf_indx.data(45).toPyObject()  #45ая роль - получаем всю переменную
        if mat_fl is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Вы не выбрали поток снабжения для удаления"))
        else:
            a_msg = unicode(u"Подтверждаете удаление потока снабжения по ")
            a_msg += unicode(mat_fl.material_type.material_type_name)
            a_msg += unicode(u" ?")
            a_reply = QtGui.QMessageBox.question(self, unicode(u'Подтвердите'), a_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
            if a_reply == QtGui.QMessageBox.Yes:
                db_main.the_session_handler.delete_concrete_object(mat_fl)
                self.gui_models_mat_flows_table.deleteRow(mf_indx)

    def add_sales_lead_to_client(self):
        if self.DlgEditSalesOppotunity is None:  #be lazy
            self.DlgEditSalesOppotunity = gui_Dialog_EditSalesOppotunity(self)
        client_model = self.get_selected_counterparty()
        if client_model is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Вы не выбрали клиента, необходимо выбрать"))
        else:
            edit_dialog = self.get_DlgEditSalesOppotunity()
            edit_dialog.set_state_to_add_new(client_model) #Тут должно быть сбрасывание полей
            is_ok, new_lead = edit_dialog.run_dialog()
            if is_ok == 1:
                #Записали в базу данных
                db_main.the_session_handler.add_object_to_session(new_lead)
                db_main.the_session_handler.commit_session()
                #Не забыли добавить в табличку
                self.gui_models_sales_leads_table.insertNew(new_lead)
                #Создаём заметку
                edit_dialog = gui_DialogCrm_EditSimpleRecord(self) #Bad idea
                htmltext_template, text_header = db_main.crm_template_new_sales_lead(new_lead)
                edit_dialog.set_state_to_add_new([], htmltext_template, text_header)
                is_ok_with_rec, new_rec = edit_dialog.run_dialog()
                if is_ok_with_rec == 1:
                    db_main.the_session_handler.add_object_to_session(new_rec)
                    db_main.the_session_handler.commit_session()
                    try_send_email_about_new_record(new_rec)

    def edit_sales_lead_to_client(self):
        if self.DlgEditSalesOppotunity is None:  #be lazy
            self.DlgEditSalesOppotunity = gui_Dialog_EditSalesOppotunity(self)
        lead_indx = self.tableView_client_oppotunities.currentIndex()
        a_lead = lead_indx.data(45).toPyObject()  #45ая роль - получаем всю переменную
        if a_lead is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Вы не выбрали сделку в работе для редактирования"))
        else:
            old_lead = a_lead.get_dummy_copy()
            edit_dialog = self.get_DlgEditSalesOppotunity()
            edit_dialog.set_state_to_edit(a_lead)
            is_ok, new_lead = edit_dialog.run_dialog() #new_lead = a_lead
            if is_ok == 1:
                #Записали в базу данных
                db_main.the_session_handler.commit_session()
                #Не забыли обновить табличку
                self.gui_models_sales_leads_table.changeExisting(lead_indx)
                #Создаем заметку
                edit_dialog = gui_DialogCrm_EditSimpleRecord(self) #Bad idea Or not that bad ?
                htmltext_template, text_header = db_main.crm_template_change_sales_lead(old_lead, new_lead)
                edit_dialog.set_state_to_add_new([], htmltext_template, text_header)
                is_ok_with_rec, new_rec = edit_dialog.run_dialog()
                if is_ok_with_rec == 1:
                    db_main.the_session_handler.add_object_to_session(new_rec)
                    db_main.the_session_handler.commit_session()
                    try_send_email_about_new_record(new_rec)

    def delete_sales_lead_to_client(self):
        lead_indx = self.tableView_client_oppotunities.currentIndex()
        lead_i = lead_indx.data(45).toPyObject()  #45ая роль - получаем всю переменную
        if lead_i is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Вы не выбрали возможность для забвения"))
        else:
            a_msg = unicode(u"Подтверждаете забвение возможности по товару %s? Или, может, сроки перенесете?") %(unicode(lead_i.material_type.material_type_name))
            a_reply = QtGui.QMessageBox.question(self, unicode(u'Подтвердите'), a_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
            if a_reply == QtGui.QMessageBox.Yes:
                db_main.the_session_handler.delete_concrete_object(lead_i)
                self.gui_models_sales_leads_table.deleteRow(lead_indx)

    def build_simulation_reports(self, index_to, index_from):
        #Строим HTML-отчет
        report = index_to.data(35).toPyObject()
        self.textBrowser_Simulation.setHtml(report.get_html())
        self.plotter(report.get_dataframe_to_plot(), report.get_name())

    def zoom(self):
        self.toolbar.zoom()
    def pan(self):
        self.toolbar.pan()
    def home(self):
        self.toolbar.home()
    def palette(self):
        self.toolbar.save_figure()

   #Базовый построитель графиков
    def plotter(self,dframe,legend,title = '',clear = True,dots_form = '-'):
        #TODO: а что тут с памятью?...
        if clear == True:
            self.SIM_INF_mpl_plot.figure.clear()
        ax = self.SIM_INF_mpl_plot.figure.add_subplot(111)
        ax.plot(dframe, dots_form)
        ax.figure.suptitle(title)
        if legend <> "":
            ax.legend(legend,loc = 'best')
        ax.figure.canvas.draw()
        def onclick(event):  #Это как-то очень заумно
            print 'button=%d, x=%d, y=%d, xdata=%f, ydata=%f'%(
            event.button, event.x, event.y, event.xdata, event.ydata)
        #cid = ax.figure.canvas.mpl_connect('button_press_event', onclick)

    def update_log_lists(self):
        self.seed_cmbx.clear()
        for ep_i in db_main.iter_epoch_data():
            self.seed_cmbx.addItem("epoch #" +str(ep_i.epoh_num) + " seed #" +str(ep_i.seed_value), ep_i.seed_value)

    def log_show_a_variable(self, index_to, index_from):
        data = index_to.data(35).toPyObject()
        if data is not None:
            [obs_name, pd_dataframe] = data
            #TODO: а что тут с памятью?...
            self.mplwidget_testsim.figure.clear()
            ax = self.mplwidget_testsim.figure.add_subplot(111)
            ax.plot(pd_dataframe, "-")
            ax.figure.suptitle(unicode(obs_name))
            ax.figure.canvas.draw()

    def run_test_simulation_selected_seed(self):
        a_seed = self.seed_cmbx.itemData(self.seed_cmbx.currentIndex(),32).toPyObject()
        self.run_test_simulation(a_seed)

    def run_test_simulation_random_seed(self):
        a_seed =  random.randint(0, sys.maxint)
        self.run_test_simulation(a_seed)

    def run_test_simulation(self, test_seed):
        the_planner = c_planner()
        log_dict = the_planner.run_and_return_log(test_seed)
        # Обновим табличку с логами
        start_date = db_main.the_settings_manager.get_param_value("initial_data_date")
        self.gui_models_testsimlog_table.update_logs(start_date, log_dict["log_list"])
        # Обновим список переменных
        sim_results = log_dict["sim_results"]  #Сложно...
        self.gui_models_testsim_varlist.update_with_observations(sim_results)

    def click_on_project_tree(self, index_to, index_from):
        node_data = index_to.data(35).toPyObject()
        if node_data is not None:
            #a = node_data[QtCore.QString("data_type")]  #так можно тип проверить
            v = node_data[QtCore.QString("data_value")]
            rep_i = db_main.the_report_filler.get_report_for_object(v)
            self.textBrowser_project.setHtml(rep_i.get_html())
        else:
            self.textBrowser_project.setHtml("")

    def set_project_node_finished(self):
        index_i = self.project_tree_view.selectedIndexes()[0] #Тут все столбцы
        node_i = index_i.internalPointer()
        if node_i.typeInfo() == "STEP":
            step_data = node_i.get_data()
            db_main.the_session_handler.merge_object_to_session(step_data)
            if step_data.is_completed == 1:
                step_data.set_uncompleted()
            else:
                step_data.set_completed()
            step_data.project.update_status()
            db_main.the_session_handler.commit_session()
        if node_i.typeInfo() == "PROJECT":
            proj_data = node_i.get_data()
            db_main.the_session_handler.merge_object_to_session(proj_data)
            if proj_data.is_completed == 1:
                proj_data.set_uncompleted()
            else:
                proj_data.set_completed()
            proj_data.set_completed()
            db_main.the_session_handler.commit_session()

    def crm_add_client_cons_budget(self):
        client_model = self.get_selected_counterparty()
        if client_model is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Вы не выбрали клиента, необходимо выбрать"))
        else:
            edit_dialog = self.get_DlgEditSimpleRecord()
            htmltext_template = db_main.crm_template_new_budget(client_model)
            edit_dialog.set_state_to_add_new([], htmltext_template, u"Бюджет продаж")
            is_ok, new_rec = edit_dialog.run_dialog()
            if is_ok == 1:
                db_main.the_session_handler.add_object_to_session(new_rec)
                db_main.the_session_handler.commit_session()
                try_send_email_about_new_record(new_rec)

    def crm_price_offer(self):
        client_model = self.get_selected_counterparty()
        if client_model is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Вы не выбрали клиента, необходимо выбрать"))
        else:
            edit_dialog = self.get_DlgEditSimpleRecord()
            htmltext_template = db_main.crm_template_priceoffer(client_model)
            edit_dialog.set_state_to_add_new([], htmltext_template, u"Коммерческое предложение")
            is_ok, new_rec = edit_dialog.run_dialog()
            if is_ok == 1:
                db_main.the_session_handler.add_object_to_session(new_rec)
                db_main.the_session_handler.commit_session()
                try_send_email_about_new_record(new_rec)

    def crm_price_offer_input(self):
        supplier_model = self.get_selected_counterparty()
        if supplier_model is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Вы не выбрали поставщика, необходимо выбрать"))
        else:
            edit_dialog = self.get_DlgEditSimpleRecord()
            htmltext_template = db_main.crm_template_price_input(supplier_model)
            edit_dialog.set_state_to_add_new([], htmltext_template, u"Коммерческое предложение")
            is_ok, new_rec = edit_dialog.run_dialog()
            if is_ok == 1:
                db_main.the_session_handler.add_object_to_session(new_rec)
                db_main.the_session_handler.commit_session()
                try_send_email_about_new_record(new_rec)

    def crm_click_on_record(self, index_to, index_from):
        a_rec = index_to.data(35).toPyObject()
        if a_rec is not None:
            self.textBrowser_KnBase.setHtml(a_rec.get_html_text())
            self.lineEdit_smart_hashtag_search.setText(a_rec.hashtags_string)

    def knbase_deep_search_record(self):
        #Глубокий поиск - проходим ещё и по тексту каждой заметки
        text_to_search = unicode(self.lineEdit_SearchHashKnBase.text())
        self.gui_models_knbase_list_proxy.setFilterRegExp("")  #Убираем фильтр - будем на уровне модели фильтровать
        self.gui_models_knbase_list.set_deep_filter_on_records(text_to_search)

    def knbase_easy_search_record(self, new_text):
        #Поверхностный поиск - просто включаем proxy. И выключаем режим deep в модели
        self.gui_models_knbase_list_proxy.setFilterRegExp(new_text)
        self.gui_models_knbase_list.turn_off_deep_filter()

    def knbase_apply_themefilter(self):
        # Делает фильтр "И" по всем забитым словам в "по тематике".
        hashtag_string = unicode(self.lineEdit_smart_hashtag_search.text())
        words = utils.parse_all_words_and_clean_hashtags(hashtag_string)
        hashtags = db_main.get_hashtags_from_names(words)
        filtered_records = db_main.get_records_list_andfilt_by_hashtags(hashtags)
        s = u"Фильтрация по запросу:<br>"
        for ht_i in hashtags:
            s += ht_i.hashtext() + " "
        s += "<br><br>"
        for rec_i in filtered_records:
            s += rec_i.get_html_text() + "<br><br>"
        self.textBrowser_KnBase.setHtml(s)

    def crm_click_on_hashtag(self, index_to, index_from):
        a_ht = index_to.data(35).toPyObject()
        if a_ht is not None:
            rep_i = db_main.the_report_filler.get_report_for_object(a_ht)  #TODO: не надо тут инстацировать - память...
            self.textBrowser_KnBase.setHtml(rep_i.get_html())
            self.lineEdit_smart_hashtag_search.setText(a_ht.text)

    def crm_from_hashtag_to_records(self):
        #Берем текущий хештэг и ставим его в фильтр по записям
        a_ht = self.get_selected_crm_hashtag()
        self.lineEdit_SearchHashKnBase.setText(a_ht.hashtext())
        self.knbase_easy_search_record(a_ht.hashtext())
        self.tabWidget_KnBaseSource.setCurrentIndex(1)

    def crm_knbase_rename_hashtag(self):
        # Меняем название хештэга и подменяем текст во всех связанных записях.
        a_msg = u"Вы уверены, что хотите переименовать хештэг? Если новое имя совпадет с существующим, все записи потеряются."
        a_msg += u"Если это хештэг с именем компании, записи перестанут подтягиваться в карточку."
        a_reply = QtGui.QMessageBox.question(self, unicode(u'Подтвердите'), a_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if a_reply == QtGui.QMessageBox.Yes:
            a_ht = self.get_selected_crm_hashtag()
            [ans_text, ans] = QtGui.QInputDialog.getText(self, u"Переименовать тэг", u"Введите новое название для " + a_ht.hashtext())
            if ans:
                old_tag_name = unicode(a_ht.text)
                new_tag_name = utils.trim_whitespaces(unicode(ans_text))
                db_main.rename_hashtag_usages(old_tag_name, new_tag_name)
                self.gui_models_knbase_hashtag_list.update_list()
                self.gui_models_knbase_list.update_list()

    def get_selected_crm_hashtag(self):
        ht_index = self.listView_KnBaseHashtags.currentIndex()
        selected_ht = ht_index.data(35).toPyObject()
        return selected_ht

    def get_selected_crm_record(self):
        rec_index = self.listView_KnBase.currentIndex()
        selected_record = rec_index.data(35).toPyObject()
        return selected_record

    def crm_add_new_counterparty(self):
        counterpaty_selected = self.get_selected_counterparty()
        if counterpaty_selected is not None: #Если None, то просто не будет выбран тип
            type = counterpaty_selected.discriminator  # 'agent' / 'supplier' / 'client'
        else:
            type = ""
        edit_dialog =  self.get_DlgEditCPdata()
        edit_dialog.set_state_to_add_new(type)
        ans = edit_dialog.run_dialog()
        if ans[0] == 1:
            db_main.the_session_handler.add_object_to_session(ans[1])
            db_main.the_session_handler.commit_session()

    def crm_edit_counterparty(self):
        counterpaty_selected = self.get_selected_counterparty()
        if counterpaty_selected is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Вы не выбрали контрагента, необходимо выбрать"))
        else:
            pass

    def add_crm_blank_record(self):
        edit_dialog = self.get_DlgEditSimpleRecord()
        edit_dialog.set_state_to_add_new()
        is_ok, new_rec = edit_dialog.run_dialog()
        if is_ok == 1:
            db_main.the_session_handler.add_object_to_session(new_rec)
            db_main.the_session_handler.commit_session()
            try_send_email_about_new_record(new_rec)
        if self.Global_tabs.currentIndex() <> TabNums["KnBase"]:
            self.Global_tabs.setCurrentIndex(TabNums["KnBase"])

    def edit_crm_record(self):
        selected_record = self.get_selected_crm_record()
        if selected_record is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Вы не выбрали запись, необходимо выбрать"))
        else:
            edit_dialog = self.get_DlgEditSimpleRecord()
            edit_dialog.set_state_to_edit(selected_record)
            ans = edit_dialog.run_dialog()
            if ans[0] == 1:
                db_main.the_session_handler.merge_object_to_session(ans[1])  #На всякий случай
                db_main.the_session_handler.commit_session()

    def delete_crm_record(self):
        selected_record = self.get_selected_crm_record()
        if selected_record is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Вы не выбрали запись для удаления"))
        else:
            a_msg = unicode(u"Подтверждаете удаление: ")
            a_msg += unicode(selected_record.headline)
            a_msg += unicode(u" ?")
            a_reply = QtGui.QMessageBox.question(self, unicode(u'Подтвердите'), a_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
            if a_reply == QtGui.QMessageBox.Yes:
                db_main.the_session_handler.delete_concrete_object(selected_record)
                #Здесь наверняка ошибки будут из-за Proxy
                self.gui_models_knbase_list.deleteRow(self.listView_KnBase.currentIndex())

    def add_crm_contact(self):
        edit_dialog = self.get_DlgEditContact()
        edit_dialog.set_state_to_add_new()
        ans = edit_dialog.run_dialog()
        if ans[0] == 1:
            db_main.the_session_handler.add_object_to_session(ans[1])
            db_main.the_session_handler.commit_session()
            self.gui_models_contacts.update_list()  #TODO: апдейт индекса
        if self.Global_tabs.currentIndex() <> TabNums["Contacts"]:
            self.Global_tabs.setCurrentIndex(TabNums["Contacts"])

    def edit_crm_contact(self):
        edit_dialog = self.get_DlgEditContact()
        selected_contact = self.get_selected_contact()
        if selected_contact is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Вы не выбрали контакт для редактирования"))
        else:
            edit_dialog.set_state_to_edit(selected_contact)
            ans = edit_dialog.run_dialog()
            if ans[0] == 1:
                db_main.the_session_handler.commit_session()
                self.gui_models_contacts.update_list()  #TODO: апдейт индекса

    def delete_crm_contact(self):
        selected_contact = self.get_selected_contact()
        if selected_contact is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Вы не выбрали контакт для удаления"))
        else:
            a_msg = unicode(u"Подтверждаете удаление: ")
            a_msg += unicode(selected_contact.name + " @ " + selected_contact.company.name)
            a_msg += unicode(u" ?")
            a_reply = QtGui.QMessageBox.question(self, unicode(u'Подтвердите'), a_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
            if a_reply == QtGui.QMessageBox.Yes:
                db_main.the_session_handler.delete_concrete_object(selected_contact)
                #Здесь наверняка ошибки будут из-за Proxy
                self.gui_models_contacts.update_list()  #TODO: апдейт индекса
                self.textBrowser_contact_data.setHtml("")

    def get_selected_contact(self):
        rec_index = self.listView_contacts.currentIndex()
        selected_contact = rec_index.data(35).toPyObject()
        return selected_contact

    def crm_click_on_contact(self, index_to, index_from):
        a_contact = index_to.data(35).toPyObject()
        if a_contact is not None:
            rep_i = db_main.the_report_filler.get_report_for_object(a_contact) #TODO: не надо тут инстацировать - память...
            self.textBrowser_contact_data.setHtml(rep_i.get_html())

    def crm_contact_compose_email(self):
        # Отправляем письмо контакту (открываем в почтовой программе - через браузерную ссылку)
        a_cnt = self.get_selected_contact()
        if a_cnt is not None:
            to_list = []
            cc_list = [user_group_email]
            a_body = ""
            a_subj = ""
            for dt_i in a_cnt.details:
                if dt_i.is_email():
                    to_list += [dt_i.cont_value]
            if a_cnt.is_person:
                a_body += u"Уважаемый %s," % (a_cnt.name)
            a_subj += u"СИ Интерлайн <-> %s" %(a_cnt.company.name)
            utils.create_and_open_email_link(to_list, cc_list, a_subj, a_body)

    def run_shortcut_to_knbase(self, hashtag_texts = None):
        # Переходит на страничку с базой знаний. Пишет в "по тематике" фильтр по всем хештегам.
        if hashtag_texts is not None:
            s = ""
            for ht_txt in hashtag_texts:
                s += ht_txt + " "
            self.lineEdit_smart_hashtag_search.setText(s)
            self.tabWidget_KnBaseSource.setCurrentIndex(0)
            self.Global_tabs.setCurrentIndex(TabNums["KnBase"])
            self.knbase_apply_themefilter()

    def goto_knbase_from_cp(self):
        # Можно ускорить: тут сначала из тэгов текст, потом обратно для общности парсится..
        cp_model = self.get_selected_counterparty()
        if cp_model is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Выберете контрагента и нажмите ещё раз"))
        else:
            self.run_shortcut_to_knbase([cp_model.hashtag_name()])

    def goto_knbase_from_cp_cons(self):
        cp_model = self.get_selected_counterparty()
        if cp_model is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Выберете контрагента и нажмите ещё раз"))
        else:
            self.run_shortcut_to_knbase([cp_model.hashtag_name(), u"#Бюджет"]) #TODO: фильтр И/ИЛИ

    def goto_knbase_from_cp_offers(self):
        cp_model = self.get_selected_counterparty()
        if cp_model is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Выберете контрагента и нажмите ещё раз"))
        else:
            self.run_shortcut_to_knbase([cp_model.hashtag_name(), u"#Офер"])

    def goto_knbase_from_cp_prices(self):
        cp_model = self.get_selected_counterparty()
        if cp_model is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Выберете контрагента и нажмите ещё раз"))
        else:
            self.run_shortcut_to_knbase([cp_model.hashtag_name(), u"#Прайс"])

    def print_kn_base_selection(self):
        preview = QtGui.QPrintPreviewDialog()
        preview.paintRequested.connect(lambda p: self.textBrowser_KnBase.print_(p))
        preview.exec_()

    def navigate_KnBase(self, some_url):
        print some_url.toString()

class gui_Dialog_EditPrice(QtGui.QDialog, Ui_Dialog_EditClientPrice):

    def __init__(self, parent=None):
        super(gui_Dialog_EditPrice, self).__init__(parent)
        self.setupUi(self) #Метод от QtDesigner
        self.my_price_entity = None
        #Так подтягиваем данные
        self.general_materials_model = gui_general_material_list_model(do_load = 0)
        self.payterm_model = gui_payment_terms_list_model()
        self.client_model = gui_counterparty_list_model(agent_discriminator='client', do_load = 0)
        self.comboBox_SupPrForWichClient.setModel(self.client_model)
        #TODO: фильтровать условия платежа
        self.comboBox_payment_terms.setModel(self.payterm_model)
        self.comboBox_material.setModel(self.general_materials_model)
        self.var_is_correct = False
        self.my_mode = 0   #1 - edit, 0 - new
        self.dateEdit_PriceValidFrom.setMinimumDate(qtdate_pack(datetime.date.today()))
        self.dateEdit_PriceValidTill.setMinimumDate(qtdate_pack(datetime.date.today()))
        self.connect(self.checkBox_is_for_group,QtCore.SIGNAL("stateChanged(int)"),self.update_materials_combobox)
        self.connect(self.comboBox_payment_terms,QtCore.SIGNAL("currentIndexChanged(int)"),self.update_ccy_label)
        self.connect(self.comboBox_material,QtCore.SIGNAL("currentIndexChanged(int)"),self.update_unit_label)
        self.connect(self.checkBox_SupPrIsForSpecClient,QtCore.SIGNAL("stateChanged(int)"),self.resort_clients)
        self.connect(self.checkBox_IsValidBetweenDates,QtCore.SIGNAL("stateChanged(int)"),self.update_valid_between)
        self.connect(self.checkBox_SpecialCond,QtCore.SIGNAL("stateChanged(int)"),self.update_sp_cond_chbox)
        self.connect(self.comboBox_material,QtCore.SIGNAL("currentIndexChanged(int)"),self.resort_clients)
        self.connect(self.checkBox_ClPrPerOrderOnly,QtCore.SIGNAL("stateChanged(int)"),self.update_only_per_order_chbox)
        self.connect(self.checkBox_ClPrIsShipmentTo,QtCore.SIGNAL("stateChanged(int)"),self.update_shipment_to_chbox)
        self.pushButton_LimitToWeek.clicked.connect(self.set_within_week)
        self.pushButton_LimitToMonth.clicked.connect(self.set_within_month)
        self.pushButton_LimitToQuater.clicked.connect(self.set_within_quater)

    def set_state_to_add_new(self, agent_model):
        #Вызываю перед открытием
        self.my_mode = 0
        self.agent_model = agent_model
        self.setWindowTitle(unicode(u"Добавление цены для ") + unicode(self.agent_model.name))
        if self.agent_model.discriminator == 'client':
            self._turn_to_client_mode()
        elif self.agent_model.discriminator == 'supplier':
            self._turn_to_supplier_mode()
        else:
            raise BaseException("Wrong agent type")
        self.__when_open()

    def set_state_to_edit(self, price_entity):
        #Вызываю перед открытием
        self.my_mode = 1
        self.my_price_entity = price_entity
        if price_entity.discriminator == "sell_price":
            self.agent_model = price_entity.client_model
            self._turn_to_client_mode()
        elif price_entity.discriminator == "buy_price":
            self.agent_model = price_entity.supplier_model
            self._turn_to_supplier_mode()
        else:
            raise BaseException("Wrong price type")
        self.setWindowTitle(unicode(u"Изменение цены для ") + unicode(self.agent_model.name))
        self.__when_open()

    def _turn_to_client_mode(self):
        self.groupBox_SupplierPriceDetails.setVisible(False)
        self.groupBox_ClientPriceDetails.setVisible(True)
        self.checkBox_IsFactoring.setVisible(True)
        new_h = 400 - self.groupBox_SupplierPriceDetails.height()
        self.resize(self.width(), new_h)
        self.my_obj_mode = 'client'

    def _turn_to_supplier_mode(self):
        self.groupBox_SupplierPriceDetails.setVisible(True)
        self.groupBox_ClientPriceDetails.setVisible(False)
        self.checkBox_IsFactoring.setVisible(False)
        new_h = 400 - self.groupBox_ClientPriceDetails.height()
        self.resize(self.width(), new_h)
        self.my_obj_mode = 'supplier'

    def __when_open(self):
        if self.my_mode == 1: # Edit
            pr = self.my_price_entity
            self.lineEdit_price.setText(simple_locale.number2string(pr.price_value))
            #Находим индекс элемента (чтобы в комбобоксе то что надо выбрать).
            # 40 - роль для поиска по ключу, ключ - строка, уникальная глобально - string_key()
            #(имя таблицы в базе данных + rec_id записи)
            indx = self.comboBox_payment_terms.findData(pr.payterm.string_key(),40)
            self.comboBox_payment_terms.setCurrentIndex(indx)
            if pr.is_for_group:
                self.checkBox_is_for_group.setCheckState(QtCore.Qt.Checked)
                #Грузим группы материалов в комбобокс
                self.general_materials_model.switch_to_material_types()
                indx = self.comboBox_material.findData(pr.material_type.string_key(),40)
            else:
                self.checkBox_is_for_group.setCheckState(QtCore.Qt.Unchecked)
                #Грузим все номенклатуры в комбобокс
                self.general_materials_model.switch_to_materials()
                indx = self.comboBox_material.findData(pr.material.string_key(),40)
            self.comboBox_material.setCurrentIndex(indx)
            if pr.nonformal_conditions is None: pr.nonformal_conditions = ""
            if pr.nonformal_conditions <> "":
                self.checkBox_SpecialCond.setCheckState(QtCore.Qt.Checked)
                self.update_sp_cond_chbox()
                self.plainTextEdit_special_conditions.setPlainText(pr.nonformal_conditions)
            else:
                self.checkBox_SpecialCond.setCheckState(QtCore.Qt.Unchecked)
                self.update_sp_cond_chbox()
                self.plainTextEdit_special_conditions.setPlainText(u"")
            self.label_currency_name.setText(str(pr.payterm.ccy_quote))
            # Новые фишки
            if pr.min_order_quantity is not None:
                self.lineEdit_ClPrMinOQ.setText(str(pr.min_order_quantity))
            else:
                self.lineEdit_ClPrMinOQ.setText("0")
            if pr.min_order_sum is not None:
                self.lineEdit_ClPrMinOS.setText(str(pr.min_order_sum))
            else:
                self.lineEdit_ClPrMinOS.setText("0")
            if pr.is_valid_between_dates:
                # Это повлечет вызов события
                self.checkBox_IsValidBetweenDates.setCheckState(QtCore.Qt.Checked)
                self.update_valid_between()
                self.dateEdit_PriceValidFrom.setDate(qtdate_pack(pr.date_valid_from))
                self.dateEdit_PriceValidTill.setDate(qtdate_pack(pr.date_valid_till))
            else:
                self.checkBox_IsValidBetweenDates.setCheckState(QtCore.Qt.Unchecked)
                self.update_valid_between()
                self.dateEdit_PriceValidFrom.setDate(qtdate_pack(datetime.datetime.today()))
                self.dateEdit_PriceValidTill.setDate(qtdate_pack(datetime.datetime.today()))
            # Теперь специфичные для клиента / поставщика
            if self.my_obj_mode == 'client':
                if pr.is_delivery:
                    self.checkBox_ClPrIsShipmentTo.setCheckState(QtCore.Qt.Checked)
                    self.lineEdit_ClPrPlaceOfShipment.setText(pr.delivery_place)
                else:
                    self.checkBox_ClPrIsShipmentTo.setCheckState(QtCore.Qt.Unchecked)
                    self.lineEdit_ClPrPlaceOfShipment.setText(u"")
                if pr.is_per_order_only:
                    self.checkBox_ClPrPerOrderOnly.setCheckState(QtCore.Qt.Checked)
                else:
                    self.checkBox_ClPrPerOrderOnly.setCheckState(QtCore.Qt.Unchecked)
                self.update_shipment_to_chbox()
                self.lineEdit_ClPrOrderFulfilmentTerm.setText(str(pr.order_fulfilment_timedelta))
                if pr.is_factoring:
                    self.checkBox_IsFactoring.setCheckState(QtCore.Qt.Checked)
                else:
                    self.checkBox_IsFactoring.setCheckState(QtCore.Qt.Unchecked)
            elif self.my_obj_mode == 'supplier':
                self.lineEdit_SupPrIncotermsPlace.setText(pr.incoterms_place)
                if pr.is_only_for_sp_client:
                    self.checkBox_SupPrIsForSpecClient.setCheckState(QtCore.Qt.Checked)
                    self.resort_clients()
                else:
                    self.checkBox_SupPrIsForSpecClient.setCheckState(QtCore.Qt.Unchecked)
                self.lineEdit_LeadTime.setText(str(pr.lead_time))
        elif self.my_mode == 0: # New
            self.comboBox_payment_terms.setCurrentIndex(-1)
            self.lineEdit_price.setText("")
            self.label_currency_name.setText("")
            self.label_currency_name_2.setText("")
            self.label_units.setText("")
            self.label_units_2.setText("")
            self.checkBox_is_for_group.setCheckState(QtCore.Qt.Checked)
            self.update_materials_combobox()
            self.checkBox_IsFactoring.setCheckState(QtCore.Qt.Unchecked)
            self.lineEdit_ClPrMinOQ.setText("0")
            self.lineEdit_ClPrMinOS.setText("0")
            self.checkBox_IsValidBetweenDates.setCheckState(QtCore.Qt.Checked)
            self.update_valid_between()
            d1 = datetime.date.today()
            d2 = d1 + datetime.timedelta(days=180)
            self.dateEdit_PriceValidFrom.setDate(qtdate_pack(d1))
            self.dateEdit_PriceValidTill.setDate(qtdate_pack(d2))
            if self.my_obj_mode == 'client':
                self.checkBox_ClPrPerOrderOnly.setCheckState(QtCore.Qt.Checked)
                self.update_only_per_order_chbox()
                self.checkBox_ClPrIsShipmentTo.setCheckState(QtCore.Qt.Unchecked)
                self.update_shipment_to_chbox()
                self.lineEdit_ClPrPlaceOfShipment.setText("")
            elif self.my_obj_mode == 'supplier':
                self.lineEdit_SupPrIncotermsPlace.setText("EXW " + self.agent_model.name)
                self.lineEdit_LeadTime.setText(str(5))
                self.checkBox_SupPrIsForSpecClient.setCheckState(QtCore.Qt.Unchecked)
                self.resort_clients()
            self.plainTextEdit_special_conditions.setPlainText(u"")
            self.checkBox_SpecialCond.setCheckState(QtCore.Qt.Unchecked)
            self.update_sp_cond_chbox()


    def update_valid_between(self):
        if self.checkBox_IsValidBetweenDates.checkState() == QtCore.Qt.Checked:
            self.dateEdit_PriceValidFrom.setVisible(True)
            self.dateEdit_PriceValidTill.setVisible(True)
            self.dateEdit_PriceValidFrom.setEnabled(True)
            self.dateEdit_PriceValidTill.setEnabled(True)
            self.pushButton_LimitToWeek.setEnabled(True)
            self.pushButton_LimitToMonth.setEnabled(True)
            self.pushButton_LimitToQuater.setEnabled(True)
            self.pushButton_LimitToWeek.setVisible(True)
            self.pushButton_LimitToMonth.setVisible(True)
            self.pushButton_LimitToQuater.setVisible(True)
        else:
            self.dateEdit_PriceValidFrom.setVisible(False)
            self.dateEdit_PriceValidTill.setVisible(False)
            self.dateEdit_PriceValidFrom.setEnabled(False)
            self.dateEdit_PriceValidTill.setEnabled(False)
            self.pushButton_LimitToWeek.setEnabled(False)
            self.pushButton_LimitToMonth.setEnabled(False)
            self.pushButton_LimitToQuater.setEnabled(False)
            self.pushButton_LimitToWeek.setVisible(False)
            self.pushButton_LimitToMonth.setVisible(False)
            self.pushButton_LimitToQuater.setVisible(False)

    def set_within_week(self):
        d1 = datetime.date.today()
        d2 = d1 + datetime.timedelta(days = 7)
        self.set_between_dates(d1,d2)

    def set_within_month(self):
        d1 = datetime.date.today()
        d2 = d1 + datetime.timedelta(days = 30)
        self.set_between_dates(d1,d2)

    def set_within_quater(self):
        d1 = datetime.date.today()
        d2 = d1 + datetime.timedelta(days = 90)
        self.set_between_dates(d1,d2)

    def set_between_dates(self, d1, d2):
        self.dateEdit_PriceValidFrom.setDate(qtdate_pack(d1))
        self.dateEdit_PriceValidTill.setDate(qtdate_pack(d2))

    def update_sp_cond_chbox(self):
        if self.checkBox_SpecialCond.checkState() == QtCore.Qt.Checked:
            self.plainTextEdit_special_conditions.setEnabled(True)
            self.plainTextEdit_special_conditions.setVisible(True)
        else:
            self.plainTextEdit_special_conditions.setEnabled(False)
            self.plainTextEdit_special_conditions.setVisible(False)

    def update_only_per_order_chbox(self):
        if self.checkBox_ClPrPerOrderOnly.checkState() == QtCore.Qt.Checked:
            self.lineEdit_ClPrOrderFulfilmentTerm.setText(str(60))
        else:
            self.lineEdit_ClPrOrderFulfilmentTerm.setText(str(5))

    def update_shipment_to_chbox(self):
        if self.checkBox_ClPrIsShipmentTo.checkState() == QtCore.Qt.Checked:
            self.lineEdit_ClPrPlaceOfShipment.setVisible(True)
            self.lineEdit_ClPrPlaceOfShipment.setEnabled(True)
        else:
            self.lineEdit_ClPrPlaceOfShipment.setVisible(False)
            self.lineEdit_ClPrPlaceOfShipment.setEnabled(False)

    def update_materials_combobox(self):
        if self.checkBox_is_for_group.checkState() == QtCore.Qt.Checked:
            #Грузим группы материалов в комбобокс
            self.general_materials_model.switch_to_material_types()
        else: #self.checkBox_is_for_group.checkState() == QtCore.Qt.Unchecked:
            #Грузим все номенклатуры в комбобокс
            self.general_materials_model.switch_to_materials()
        self.comboBox_material.setCurrentIndex(-1)

    def resort_clients(self):
        if self.my_obj_mode == 'supplier': # В ином случае вызова не будет
            if self.checkBox_SupPrIsForSpecClient.isChecked():
                self.comboBox_SupPrForWichClient.setEnabled(True)
                self.comboBox_SupPrForWichClient.setVisible(True)
                tp = self.general_materials_model.check_type()
                if tp == 'materials':
                    mat_type = self.get_material().material_type
                elif tp == 'groups':
                    mat_type = self.get_material()
                self.client_model.update_list()
                self.client_model.set_matgr_for_sorting(mat_type)
            else:
                self.comboBox_SupPrForWichClient.setCurrentIndex(-1)
                self.comboBox_SupPrForWichClient.setEnabled(False)
                self.comboBox_SupPrForWichClient.setVisible(False)

    def update_ccy_label(self, i):
        # 35 - наша роль для передачи данных
        payterm = self.comboBox_payment_terms.itemData(i, 35).toPyObject()
        if payterm is not None:
            self.label_currency_name.setText(unicode(payterm.ccy_quote))
            self.label_currency_name_2.setText(unicode(payterm.ccy_quote))
            if payterm.ccy_quote <> payterm.ccy_pay:
                ccy = u"%s (у.е.)"%(payterm.ccy_quote)
                if payterm.fixation_at_shipment:
                    ccy += u" фиксация при отгрузке"
                else:
                    ccy += u" курс по оплате"
            else:
                ccy = u"%s"%(payterm.ccy_quote)
            prepaym = ""
            for t, p in payterm.payterm_stages.get_prepayments():
                if t < 0:
                    prepaym += u"аванс %d%%; "%(int(p))
                elif t == 0:
                    prepaym += u"предоплата %d%%; "%(int(p))
            postpaym = ""
            for t, p in payterm.payterm_stages.get_postpayments():
                prepaym += u"оплата %d%% через %d дней; "%(int(p), int(t))
            desc = u"Расчеты в %s; %s %s"%(ccy, prepaym, postpaym)
            self.label_PayTermDescription.setText(desc)

    def update_unit_label(self, i):
        # 35 - наша роль для передачи данных
        an_item = self.comboBox_material.itemData(i, 35).toPyObject()
        if an_item is not None:
            self.label_units.setText(an_item.measure_unit)
            self.label_units_2.setText(an_item.measure_unit)

    def get_material(self):
        row = self.comboBox_material.currentIndex()
        if row>=0:
            # 35 - это роль модели данных (ниже в этом модуле)
            selected_item = self.comboBox_material.itemData(row, 35).toPyObject()
            return selected_item

    def get_paycond(self):
        row = self.comboBox_payment_terms.currentIndex()
        if row>=0:
            # 35 - это роль модели данных (ниже в этом модуле)
            selected_item = self.comboBox_payment_terms.itemData(row, 35).toPyObject()
            return selected_item

    def get_price_value(self):
        try:
            return convert.convert_formated_str_2_float(self.lineEdit_price.text())
        except ValueError:
            a_title = unicode(u"Ошибка ввода")
            a_message = unicode(u"Неверно указана цена")
            QtGui.QMessageBox.information(self,a_title,a_message)
            self.var_is_correct = False
            return None

    def get_is_factoring(self):
        if self.checkBox_IsFactoring.checkState() == QtCore.Qt.Checked:
            # Проверим, подходят ли условия платежа
            paycond = self.get_paycond()
            if paycond.fixation_at_shipment:
                # Todo: проверка на валюту - рубли (надо где-то такой объект сделать - основная валюта)
                return True
            else:
                a_title = unicode(u"Ошибка ввода")
                a_message = unicode(u"Условия оплаты не подходят для факторинга")
                QtGui.QMessageBox.information(self,a_title,a_message)
                self.var_is_correct = False
                return None
        else:
            return False

    def get_MOQ(self):
        try:
            if self.lineEdit_ClPrMinOQ.text() == "":
                return 0
            else:
                return convert.convert_formated_str_2_float(self.lineEdit_ClPrMinOQ.text())
        except ValueError:
            return None

    def get_MOS(self):
        try:
            if self.lineEdit_ClPrMinOQ.text() == "":
                return 0
            else:
                return convert.convert_formated_str_2_float(self.lineEdit_ClPrMinOS.text())
        except ValueError:
            return None

    def get_valid_from_date(self):
        return qtdate_unpack(self.dateEdit_PriceValidFrom.date())

    def get_valid_till_date(self):
        return qtdate_unpack(self.dateEdit_PriceValidTill.date())

    def get_order_fulfilment_timedelta(self):
        try:
            td = int(convert.convert_formated_str_2_float(self.lineEdit_ClPrOrderFulfilmentTerm.text()))
            if td>0:
                return td
            else:
                return None
        except ValueError:
            return None

    def get_lead_time(self):
        try:
            td = int(convert.convert_formated_str_2_float(self.lineEdit_LeadTime.text()))
            if td>0:
                return td
            else:
                return None
        except ValueError:
            return None

    def get_the_special_client(self):
        row = self.comboBox_SupPrForWichClient.currentIndex()
        if row>=0:
            # 35 - это роль модели данных (ниже в этом модуле)
            selected_item = self.comboBox_SupPrForWichClient.itemData(row, 35).toPyObject()
            return selected_item

    def inp_erh(self,inp,a_message):
        if inp is None:
            QtGui.QMessageBox.information(self,unicode(u"Ошибка ввода"),unicode(u"Неверно указана графа: ") + a_message)
            self.var_is_correct = False
            return None
        else:
            return inp

    def accept(self):
        # Хорошая идея - создавать dummy переменную для заполнения формы, а потом просто с неё слизывать.
        # Ну или ORM как-то иначе настроить.
        #Перегрузка стандартного метода - читай QDialog
        self.var_is_correct = True
        #Пробегаемся по комбобоксам - проверка заполненности
        if self.var_is_correct:
            general_material = self.inp_erh(self.get_material(),unicode(u"материал"))
            if self.checkBox_is_for_group.checkState() == QtCore.Qt.Checked:
                is_for_group = True
                material_type = general_material
            elif self.checkBox_is_for_group.checkState() == QtCore.Qt.Unchecked:
                is_for_group = False
                material = general_material
        if self.var_is_correct:
            payterm = self.inp_erh(self.get_paycond(),unicode(u"условия платежа"))
        if self.var_is_correct:
            price_value = self.get_price_value()
        if self.var_is_correct:
            MOQ = self.inp_erh(self.get_MOQ(),unicode(u"MOQ (мин. объем заказа)"))
        if self.var_is_correct:
            MOS = self.inp_erh(self.get_MOS(),unicode(u"MOS (мин. стоимость заказа)"))
        if self.checkBox_IsValidBetweenDates.checkState() == QtCore.Qt.Checked:
            is_valid_between_dates = True
            date_valid_from = self.get_valid_from_date()
            date_valid_till = self.get_valid_till_date()
        else:
            is_valid_between_dates = False
        if self.my_obj_mode == 'client': #Это только для цены клиента
            if self.var_is_correct: #Важно, что после get_paycond - надо убедиться, что выбраны
                is_factoring = self.get_is_factoring()
            if self.checkBox_ClPrPerOrderOnly.checkState() == QtCore.Qt.Checked:
                is_per_order_only = True
            else:
                is_per_order_only = False
            if self.checkBox_ClPrIsShipmentTo.checkState() == QtCore.Qt.Checked:
                is_delivery = True
                delivery_place = unicode(self.lineEdit_ClPrPlaceOfShipment.text())
            else:
                is_delivery = False
            order_fulfilment_timedelta = self.inp_erh(self.get_order_fulfilment_timedelta(), unicode(u"срок отгрузки"))
        elif self.my_obj_mode == 'supplier':
            incoterms_place = unicode(self.lineEdit_SupPrIncotermsPlace.text())
            lead_time = self.inp_erh(self.get_lead_time(),unicode(u"lead time"))
            if self.checkBox_SupPrIsForSpecClient.checkState() == QtCore.Qt.Checked:
                is_only_for_sp_client = True
                for_client = self.inp_erh(self.get_the_special_client(),unicode(u"клиент"))
            else:
                is_only_for_sp_client = False
        else:
            raise BaseException(self.my_obj_mode + " - not expected here")
        if self.var_is_correct:
            if self.checkBox_SpecialCond.checkState() == QtCore.Qt.Checked:
                special_cond = unicode(self.plainTextEdit_special_conditions.toPlainText())
            else:
                special_cond = ""
        if self.var_is_correct:
            #Собираем переменную только когда убедились, что всё "ок"
            if self.my_mode == 0: #добавляем новую
                if self.agent_model.discriminator == "client":
                    self.my_price_entity = db_main.c_sell_price()
                    self.my_price_entity.client_model = self.agent_model
                elif self.agent_model.discriminator == "supplier":
                    self.my_price_entity = db_main.c_buy_price()
                    self.my_price_entity.supplier_model = self.agent_model
            self.my_price_entity.is_for_group = is_for_group
            if is_for_group:
                self.my_price_entity.material_type = material_type
                self.my_price_entity.material = None
            else:
                self.my_price_entity.material_type = None
                self.my_price_entity.material = material
            self.my_price_entity.payterm = payterm
            self.my_price_entity.price_value = price_value
            self.my_price_entity.min_order_quantity = MOQ
            self.my_price_entity.min_order_sum = MOS
            self.my_price_entity.is_valid_between_dates = is_valid_between_dates
            if is_valid_between_dates:
                self.my_price_entity.date_valid_from = date_valid_from
                self.my_price_entity.date_valid_till = date_valid_till
            else:
                self.my_price_entity.date_valid_from = None
                self.my_price_entity.date_valid_till = None
            if self.my_price_entity.discriminator == "sell_price":
                self.my_price_entity.is_factoring = is_factoring
                self.my_price_entity.is_per_order_only = is_per_order_only
                self.my_price_entity.is_delivery = is_delivery
                if is_delivery:
                    self.my_price_entity.delivery_place = delivery_place
                else:
                    self.my_price_entity.delivery_place = u""
                self.my_price_entity.order_fulfilment_timedelta = order_fulfilment_timedelta
            elif self.my_price_entity.discriminator == "buy_price":
                self.my_price_entity.incoterms_place = incoterms_place
                self.my_price_entity.lead_time = lead_time
                self.my_price_entity.is_only_for_sp_client = is_only_for_sp_client
                if is_only_for_sp_client:
                    self.my_price_entity.for_client = for_client
                else:
                    self.my_price_entity.for_client = None
            else:
                raise BaseException(self.my_price_entity.discriminator + " - not expected here")
            self.my_price_entity.nonformal_conditions = special_cond
            super(gui_Dialog_EditPrice, self).accept()

    def reject(self):
        #Перегрузка стандартного метода - читай QDialog
        if self.my_mode == 0: #if new, not from database
            self.my_price_entity = None
        super(gui_Dialog_EditPrice, self).reject()

    def run_dialog(self):
        user_decision = self.exec_()  #0 или 1
        if user_decision == QtGui.QDialog.Accepted:
            return [user_decision, self.my_price_entity]
        elif user_decision == QtGui.QDialog.Rejected:
            return [user_decision, None]

class gui_Dialog_EditMatFlow(QtGui.QDialog, Ui_Dialog_EditMatFlow):
    def __init__(self, parent=None):
        super(gui_Dialog_EditMatFlow, self).__init__(parent)
        self.setupUi(self) #Метод от QtDesigner
        self.my_mf_entity = None
        self.my_mode = 0   #1 - edit, 0 - new
        self.var_is_correct = False
        self.general_materials_model = gui_general_material_list_model()
        self.general_materials_model.switch_to_material_types()
        self.comboBox_material_type.setModel(self.general_materials_model)
        self.matdist_model = gui_matflow_matdist_model()
        self.tableView_materials_and_probs.setModel(self.matdist_model)
        self.cmbx_in_table_model = gui_materials_list_model(parent=self,do_update=0)
        self.tableView_materials_and_probs.setItemDelegateForColumn(0, gui_DelegateSelectMaterial(self, self.cmbx_in_table_model))
        self.connect(self.pushButton_EstimateStatistics, QtCore.SIGNAL("clicked()"), self.reestimate_from_statistics)
        self.connect(self.pushButton_normalize_probs, QtCore.SIGNAL("clicked()"), self.matdist_model.normalize_probs)
        self.connect(self.comboBox_material_type, QtCore.SIGNAL("currentIndexChanged(int)"),self.material_type_selected)
        self.connect(self.pushButton_add_material, QtCore.SIGNAL("clicked()"), self.add_material)
        self.connect(self.pushButton_delete_material, QtCore.SIGNAL("clicked()"), self.remove_material)
        self.connect(self.pushButton_down_025, QtCore.SIGNAL("clicked()"), self.put_volume_down_025)
        self.connect(self.pushButton_up_025, QtCore.SIGNAL("clicked()"), self.put_volume_up_025)

    def set_state_to_add_new(self, client_model):
        self.my_mode = 0
        self.client_model = client_model
        self.setWindowTitle(unicode(u"Добавление линии снабжения для ") + unicode(self.client_model.name))
        self.__when_open()

    def set_state_to_edit(self, mf_entity):
        self.my_mode = 1
        self.my_mf_entity = mf_entity
        self.client_model = mf_entity.client_model
        self.setWindowTitle(unicode(u"Изменение линии снабжения для ") + unicode(self.client_model.name))
        self.__when_open()

    def add_material(self):
        #Чтобы не переделывать модель данных для словаря с вероятностями
        self.matdist_model.insertBlankLine()

    def remove_material(self):
        ind = self.tableView_materials_and_probs.currentIndex()
        self.matdist_model.deleteRecord(ind)

    def __when_open(self):
        # Я не очень понимаю, зачем я всё в отдельный метод вынес..
        if self.my_mode == 1: #edit
            #Находим индекс элемента (чтобы в комбобоксе то что надо выбрать).
            # 40 - роль для поиска по ключу, ключ - строка, уникальная глобально - string_key()
            indx = self.comboBox_material_type.findData(self.my_mf_entity.material_type.string_key(),40)
            self.comboBox_material_type.setCurrentIndex(indx)
            self.comboBox_material_type.setEnabled(False)
            self.cmbx_in_table_model.set_parent_material_type(self.my_mf_entity.material_type)
            self.cmbx_in_table_model.update_list()
            self.lineEdit_cons_volume_mean.setText(simple_locale.number2string(self.my_mf_entity.stats_mean_volume))
            self.lineEdit_cons_period_mean.setText(simple_locale.number2string(self.my_mf_entity.stats_mean_timedelta))
            self.lineEdit_cons_vol_dev.setText(simple_locale.number2string(round(self.my_mf_entity.get_volume_std_in_proc(),2)))
            self.lineEdit_cons_period_std.setText(simple_locale.number2string(self.my_mf_entity.stats_std_timedelta))
            if self.my_mf_entity.are_materials_equal:
                self.checkBox_are_materials_substitude.setCheckState(QtCore.Qt.Checked)
            else:
                self.checkBox_are_materials_substitude.setCheckState(QtCore.Qt.Unchecked)
            if self.my_mf_entity.put_supplier_order_if_not_available:
                self.checkBox_direct_order.setCheckState(QtCore.Qt.Checked)
            else:
                self.checkBox_direct_order.setCheckState(QtCore.Qt.Unchecked)
            prob_dict = utils.c_random_dict()
            self.matdists_dict = dict()  #Изменится только при записи
            if self.my_mode == 1: #Изменение
                for md_i in db_main.get_matdist_list(self.my_mf_entity):
                    prob_dict.add_elem(md_i.material, md_i.choice_prob)
                    self.matdists_dict[md_i.material] = md_i  #Этот словарик потом проверяется при закрытии формы
            self.matdist_model.update_matdist_table(prob_dict)
        elif self.my_mode == 0: #new
            self.comboBox_material_type.setCurrentIndex(-1)
            self.comboBox_material_type.setEnabled(True)
            zer = simple_locale.number2string(0.)
            self.lineEdit_cons_volume_mean.setText(zer)
            self.lineEdit_cons_period_mean.setText(zer)
            self.lineEdit_cons_vol_dev.setText(zer)
            self.lineEdit_cons_period_std.setText(zer)
            self.matdists_dict = dict() #При запиписи заполнится - в общем-то, можно без него

    def material_type_selected(self, new_index):
        if self.my_mode == 0: #new
            if new_index>=0:
                new_mat_type = self.comboBox_material_type.itemData(new_index, 35).toPyObject()
                self.matdist_model.reset_all()
                self.cmbx_in_table_model.set_parent_material_type(new_mat_type)
                self.cmbx_in_table_model.update_list()
                ans = QtGui.QMessageBox.question(self,
                                                 unicode(self.client_model.name + " - " + new_mat_type.material_type_name),
                                                 unicode(u"Оценить по статистике?"), QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
                if ans == QtGui.QMessageBox.Yes:
                    self.reestimate_from_statistics()

    def reestimate_from_statistics(self):
        mt = self.get_material_type()
        if mt is not None:
            mfd = db_main.estimate_shipment_stats(self.client_model, mt)[0]  #там лист просто возвращается
            self.lineEdit_cons_volume_mean.setText(simple_locale.number2string(mfd["qtty_exp"]))
            self.lineEdit_cons_period_mean.setText(simple_locale.number2string(mfd["timedelta_exp"]))
            if mfd["qtty_exp"] > 0:
                cons_volume_std_prc = round(mfd["qtty_std"] / mfd["qtty_exp"] * 100, 2)
            else:
                cons_volume_std_prc = 0
            self.lineEdit_cons_vol_dev.setText(simple_locale.number2string(cons_volume_std_prc))
            self.lineEdit_cons_period_std.setText(simple_locale.number2string(mfd["timedelta_std"]))
            self.matdist_model.update_matdist_table(mfd["mat_dist"])

    def inp_erh(self,inp,a_message):
        if inp is None:
            QtGui.QMessageBox.information(self,unicode(u"Ошибка ввода"),unicode(u"Неверно указана графа: ") + a_message)
            self.var_is_correct = False
            return None
        else:
            return inp

    def get_material_type(self):
        row = self.comboBox_material_type.currentIndex()
        if row>=0:
            # 35 - это роль модели данных (ниже в этом модуле)
            selected_item = self.comboBox_material_type.itemData(row, 35).toPyObject()
            return selected_item

    def get_cons_volume_mean_value(self):
        try:
            return convert.convert_formated_str_2_float(self.lineEdit_cons_volume_mean.text())
        except ValueError:
            # a_title = unicode(u"Ошибка ввода")
            # a_message = unicode(u"Неверно указан ожидаемый объём потребления")
            # QtGui.QMessageBox.information(self,a_title,a_message)
            self.var_is_correct = False
            return None

    def get_cons_volume_stdev_value(self):
        try:
            return convert.convert_formated_str_2_float(self.lineEdit_cons_vol_dev.text())
        except ValueError:
            self.var_is_correct = False
            return None

    def get_periodicy_expectation_value(self):
        try:
            return convert.convert_formated_str_2_float(self.lineEdit_cons_period_mean.text())
        except ValueError:
            self.var_is_correct = False
            return None

    def get_periodicy_stdev_value(self):
        try:
            return convert.convert_formated_str_2_float(self.lineEdit_cons_period_std.text())
        except ValueError:
            self.var_is_correct = False
            return None

    def get_are_materials_substitude(self):
        if self.checkBox_are_materials_substitude.checkState() == QtCore.Qt.Checked:
            return True
        elif self.checkBox_are_materials_substitude.checkState() == QtCore.Qt.Unchecked:
            return False

    def get_is_direct_order(self):
        if self.checkBox_direct_order.checkState() == QtCore.Qt.Checked:
            return True
        elif self.checkBox_direct_order.checkState() == QtCore.Qt.Unchecked:
            return False

    def put_volume_down_025(self):
        self.change_volume(-0.25)

    def put_volume_up_025(self):
        self.change_volume(0.25)

    def change_volume(self, level):
        old_volume = self.get_cons_volume_mean_value()
        old_freq = self.get_periodicy_expectation_value()
        old_freq_std = self.get_periodicy_stdev_value()
        if old_volume is not None and old_freq is not None and old_freq_std is not None:
            #Когда у клиентов меняется объём потребления, сильней меняется частота, а не объём
            k = 0.3/0.7
            # И тут я решил квадратное уравнение исходя из того, что
            # (new_volume/new_freq) = (old_volume/old_freq) * (1+level)
            disc_root = utils.math.sqrt(utils.math.pow((1+k),2)+4*k*level)
            level_freq = (disc_root - (1.+k))/(2.*k)
            level_volume = k * level_freq
            new_volume = round(old_volume * (1+level_volume),2)
            new_freq = round(old_freq / (1+level_freq),2)
            new_freq_std = round(old_freq_std / (1+level_freq),2)
            self.lineEdit_cons_volume_mean.setText(simple_locale.number2string(new_volume))
            self.lineEdit_cons_period_mean.setText(simple_locale.number2string(new_freq))
            self.lineEdit_cons_period_std.setText(simple_locale.number2string(new_freq_std))

    def save_materials(self):
        # В форме у нас просто словарик хранится. Чтобы по кнопке "ОК" оно записалось в базу, нужно синхронизировать.
        self.var_is_correct = self.matdist_model.is_data_correct()
        if self.var_is_correct:
            self.matdist_model.normalize_probs()
            prob_dict = self.matdist_model.get_prob_dict()
            all_materials = []
            for mat_i, prob_i in prob_dict.randomdict.iteritems():
                all_materials += [mat_i]
                if self.matdists_dict.has_key(mat_i):
                    self.matdists_dict[mat_i].choice_prob = prob_i
                else:  #новый добавился
                    self.matdists_dict[mat_i] = db_main.c_material_flow_matdist(material_flow = self.my_mf_entity,
                                                                                material = mat_i, choice_prob = prob_i)
            if len(all_materials) < len(self.matdists_dict):
                # Значит, у нас в словаре в форме сохранились элементы, которые мы удалили. Давайте их удалять
                # Именно поэтому вызов сессии происходит здесь, а не в основной форме, по получению ответа.
                for mat_i in self.matdists_dict.keys():
                    if not(mat_i in all_materials):
                        md_to_del = self.matdists_dict.pop(mat_i)
                        db_main.the_session_handler.delete_concrete_object(md_to_del)
        else:
            a_title = unicode(u"Ошибка ввода")
            a_message = unicode(u"Неверно заполнена таблица с материалами")
            QtGui.QMessageBox.information(self,a_title,a_message)

    def accept(self):
        # Перегрузка стандартного метода - читай QDialog
        # self.var_is_correct - глобальная в диалоге. Везде ниже в методах её меняем, если что не так.
        self.var_is_correct = True
        if self.var_is_correct:
            material_type = self.inp_erh(self.get_material_type(),unicode(u"материал"))
        if self.var_is_correct:
            cons_expectation =  self.inp_erh(self.get_cons_volume_mean_value(),unicode(u"объём потребления"))
        if self.var_is_correct:
            cons_deviation = self.inp_erh(self.get_cons_volume_stdev_value(),unicode(u"отклонение объёмов"))
            if cons_deviation <= 1:
                self.var_is_correct = False
                QtGui.QMessageBox.information(self,unicode(u"Ошибка ввода"),unicode(u"Слишком малое отклонение объёмов"))
            if cons_deviation >= 300:
                self.var_is_correct = False
                QtGui.QMessageBox.information(self,unicode(u"Ошибка ввода"),unicode(u"Слишком большое отклонение объёмов"))
        if self.var_is_correct:
            periodicy_expectation = self.inp_erh(self.get_periodicy_expectation_value(),unicode(u"регулярность заказа"))
        if self.var_is_correct:
            periodicy_std = self.inp_erh(self.get_periodicy_stdev_value(),unicode(u"задержки заказа"))
        if self.var_is_correct:
            self.save_materials()
            if self.var_is_correct:
                if self.my_mode == 0: #Новый добавляем
                    self.my_mf_entity = db_main.c_material_flow()
                    self.my_mf_entity.client_model = self.client_model
                are_materials_substitude = self.get_are_materials_substitude()
                is_direct_order = self.get_is_direct_order()
                self.my_mf_entity.are_materials_equal = are_materials_substitude
                self.my_mf_entity.put_supplier_order_if_not_available = is_direct_order
                self.my_mf_entity.material_type = material_type
                self.my_mf_entity.stats_mean_timedelta = periodicy_expectation
                self.my_mf_entity.stats_std_timedelta = periodicy_std
                self.my_mf_entity.stats_mean_volume = cons_expectation
                # Проценты только после заполнения объёма
                self.my_mf_entity.set_volume_std_from_proc(cons_deviation)
                db_main.the_session_handler.commit_session()
                super(gui_Dialog_EditMatFlow, self).accept()

    def reject(self):
        #Перегрузка стандартного метода - читай QDialog
        if self.my_mode == 0: #if new, not from database
            self.my_mf_entity = None
        super(gui_Dialog_EditMatFlow, self).reject()

    def run_dialog(self):
        user_decision = self.exec_()  #0 или 1
        if user_decision == QtGui.QDialog.Accepted:
            return [user_decision, self.my_mf_entity]
        elif user_decision == QtGui.QDialog.Rejected:
            return [user_decision, None]

class gui_Dialog_EditSalesOppotunity(QtGui.QDialog, Ui_Dialog_EditSalesOppotunity):
    def __init__(self, parent=None):
        super(gui_Dialog_EditSalesOppotunity, self).__init__(parent)
        self.setupUi(self) #Метод от QtDesigner
        self.my_lead_entity = None
        self.client_model = None
        self.my_mode = 0   #1 - edit, 0 - new
        self.var_is_correct = False
        self.general_materials_model = gui_general_material_list_model()
        self.general_materials_model.switch_to_material_types()
        self.comboBox_material_type.setModel(self.general_materials_model)
        self.horizontalSlider_succprob.setRange(0,90)
        self.horizontalSlider_succprob.setSingleStep(10)
        self.horizontalSlider_surelevel.setRange(0,90)
        self.horizontalSlider_surelevel.setSingleStep(10)
        #self.dateEdit_start_early.setMinimumDate(QDate)
        self.connect(self.comboBox_material_type, QtCore.SIGNAL("currentIndexChanged(int)"),self.material_type_selected)
        self.connect(self.pushButton_changedates_to_m, QtCore.SIGNAL("clicked()"), self.dates_to_m)
        self.connect(self.pushButton_changedates_to_q, QtCore.SIGNAL("clicked()"), self.dates_to_q)
        self.connect(self.pushButton_changedates_to_hy, QtCore.SIGNAL("clicked()"), self.dates_to_hy)
        self.connect(self.pushButton_changedates_to_y, QtCore.SIGNAL("clicked()"), self.dates_to_y)

    def move_dates(self, how_many_days = 1):
        new_days_between = round(how_many_days * 2./3.)
        new_d1 = datetime.date.today() + datetime.timedelta(days=how_many_days)
        new_d2 = new_d1 + datetime.timedelta(days=new_days_between)
        self.dateEdit_start_early.setDate(qtdate_pack(new_d1))
        self.dateEdit_start_late.setDate(qtdate_pack(new_d2))

    def dates_to_m(self):
        self.move_dates(30)

    def dates_to_q(self):
        self.move_dates(90)

    def dates_to_hy(self):
        self.move_dates(180)

    def dates_to_y(self):
        self.move_dates(360)

    def material_type_selected(self, new_index):
        if self.my_mode == 0: #new
            if new_index>=0:
                new_mat_type = self.comboBox_material_type.itemData(new_index, 35).toPyObject()
                self.label_meas_unit.setText(new_mat_type.measure_unit)

    def set_state_to_add_new(self, client_model):
        self.my_mode = 0
        self.client_model = client_model
        self.setWindowTitle(unicode(u"Добавление лида по работе с ") + unicode(self.client_model.name))
        self.comboBox_material_type.setCurrentIndex(-1)
        self.comboBox_material_type.setEnabled(True)
        # Тюнингуем ручки
        self.horizontalSlider_succprob.setValue(0)
        self.horizontalSlider_surelevel.setValue(0)
        # Заполняем поля
        self.dateEdit_start_early.setDate(qtdate_pack(datetime.datetime.today()))
        self.dateEdit_start_late.setDate(qtdate_pack(datetime.datetime.today()))
        self.lineEdit_expected_qtty.setText(simple_locale.number2string(0))
        self.lineEdit_expected_periodicity.setText(simple_locale.number2string(0))

    def set_state_to_edit(self, lead_entity):
        self.my_mode = 1
        self.my_lead_entity = lead_entity
        self.client_model = self.my_lead_entity.client_model
        self.setWindowTitle(unicode(u"Изменение лида по работе с ") + unicode(self.client_model.name))
        # Выбираем в комбобоксе
        indx = self.comboBox_material_type.findData(self.my_lead_entity.material_type.string_key(),40)
        self.comboBox_material_type.setCurrentIndex(indx)
        self.comboBox_material_type.setEnabled(False)
        # Тюнингуем ручки
        self.horizontalSlider_succprob.setValue(self.my_lead_entity.success_prob*100)
        self.horizontalSlider_surelevel.setValue(self.my_lead_entity.sure_level*100)
        # Заполняем поля
        self.dateEdit_start_early.setDate(qtdate_pack(self.my_lead_entity.expected_start_date_from))
        self.dateEdit_start_late.setDate(qtdate_pack(self.my_lead_entity.expected_start_date_till))
        self.lineEdit_expected_qtty.setText(simple_locale.number2string(self.my_lead_entity.expected_qtty))
        self.lineEdit_expected_periodicity.setText(simple_locale.number2string(self.my_lead_entity.expected_timedelta))
        # Ну и про галочку не забудем
        self.checkBox_instock_promise.setChecked(self.my_lead_entity.instock_promise)

    def accept(self):
        is_var_ok = True
        if is_var_ok:
            row = self.comboBox_material_type.currentIndex()
            if row>=0:
                mat_type = self.comboBox_material_type.itemData(row, 35).toPyObject()
            else:
                QtGui.QMessageBox.information(self,unicode(u"Ошибка ввода"),unicode(u"Не выбран материал"))
                self.comboBox_material_type.setFocus()
                is_var_ok = False
        if is_var_ok:
            d1 = qtdate_unpack(self.dateEdit_start_early.date())
            d2 = qtdate_unpack(self.dateEdit_start_late.date())
            if d2 <= d1:
                QtGui.QMessageBox.information(self,unicode(u"Ошибка ввода"),unicode(u"Даты противоречивы - поправьте"))
                self.dateEdit_start_late.setFocus()
                is_var_ok = False
        if is_var_ok:
            if d1 <= (datetime.date.today() + datetime.timedelta(days = 15)):
                err_msg = unicode(u"Дата старта слишком близка. Если отгрузка действительно близка, переведите лид в "
                                  u"поток снабжения кнопкой под списком всех сделок в работе")
                QtGui.QMessageBox.information(self,unicode(u"Ошибка ввода"), err_msg)
                #self.pushButton_create_matflow.setFocus()
                is_var_ok = False
        if is_var_ok:
            try:
                expected_qtty = convert.convert_formated_str_2_float(self.lineEdit_expected_qtty.text())
            except ValueError:
                err_msg = unicode(u"Необходимо ввести число в поле с ожидаемым объёмом потребленя")
                QtGui.QMessageBox.information(self,unicode(u"Ошибка ввода"), err_msg)
                self.lineEdit_expected_qtty.setFocus()
                is_var_ok = False
            if expected_qtty <= 0:
                err_msg = unicode(u"Объём не может быть нулевым!")
                QtGui.QMessageBox.information(self,unicode(u"Ошибка ввода"), err_msg)
                self.lineEdit_expected_qtty.setFocus()
                is_var_ok = False
        if is_var_ok:
            try:
                expected_periodicity = convert.convert_formated_str_2_float(self.lineEdit_expected_periodicity.text())
            except ValueError:
                err_msg = unicode(u"Необходимо ввести число в поле с ожидаемым объёмой периодичностью")
                QtGui.QMessageBox.information(self,unicode(u"Ошибка ввода"), err_msg)
                self.lineEdit_expected_periodicity.setFocus()
                is_var_ok = False
            if expected_periodicity <= 0:
                err_msg = unicode(u"Периодичность не может быть меньше нуля!")
                QtGui.QMessageBox.information(self,unicode(u"Ошибка ввода"), err_msg)
                self.lineEdit_expected_periodicity.setFocus()
                is_var_ok = False
        if is_var_ok:
            sure_level = self.horizontalSlider_surelevel.value() / 100.
            succ_prob = self.horizontalSlider_succprob.value() / 100.
            instock_promise = self.checkBox_instock_promise.isChecked()
        if is_var_ok:
            if self.my_mode == 0: #Новый добавляем
                self.my_lead_entity = db_main.c_sales_oppotunity()
                self.my_lead_entity.client_model = self.client_model
            self.my_lead_entity.material_type = mat_type
            self.my_lead_entity.success_prob = succ_prob
            self.my_lead_entity.sure_level = sure_level
            print expected_qtty, expected_periodicity
            self.my_lead_entity.expected_qtty = expected_qtty
            self.my_lead_entity.expected_timedelta = expected_periodicity
            self.my_lead_entity.expected_start_date_from = d1
            self.my_lead_entity.expected_start_date_till = d2
            self.my_lead_entity.instock_promise = instock_promise
            super(gui_Dialog_EditSalesOppotunity, self).accept()

    def reject(self):
        if self.my_mode == 0: #if new, not from database
            self.my_lead_entity = None
        super(gui_Dialog_EditSalesOppotunity, self).reject()

    def run_dialog(self):
        user_decision = self.exec_()  #0 или 1
        if user_decision == QtGui.QDialog.Accepted:
            return [user_decision, self.my_lead_entity]
        elif user_decision == QtGui.QDialog.Rejected:
            return [user_decision, None]

class gui_DialogCrm_EditSimpleRecord(QtGui.QDialog, Ui_DialogCrm_EditSimpleRecord):
    def __init__(self, parent=None):
        super(gui_DialogCrm_EditSimpleRecord, self).__init__(parent)
        self.setupUi(self) #Метод от QtDesigner
        self.textEdit_longtext = gui_EditTextRecord(self)
        self.textEdit_longtext.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.horizontalLayout_for_textedit.addWidget(self.textEdit_longtext)

        # self.textEdit_longtext = QtGui.QTextEdit(DialogCrm_EditSimpleRecord)
        # self.textEdit_longtext.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        # self.textEdit_longtext.setObjectName(_fromUtf8("textEdit_longtext"))
        # self.verticalLayout.addWidget(self.textEdit_longtext)

        self.connect(self.pushButton_bulletList, QtCore.SIGNAL("clicked()"), self.editor_bulletList)
        self.connect(self.pushButton_numberList, QtCore.SIGNAL("clicked()"), self.editor_numberList)
        self.connect(self.pushButton_bold, QtCore.SIGNAL("clicked()"), self.editor_bold)
        self.connect(self.pushButton_italic, QtCore.SIGNAL("clicked()"), self.editor_italic)
        self.connect(self.pushButton_underline, QtCore.SIGNAL("clicked()"), self.editor_underline)
        self.connect(self.pushButton_undo, QtCore.SIGNAL("clicked()"), self.textEdit_longtext.undo)
        self.connect(self.pushButton_redo, QtCore.SIGNAL("clicked()"), self.textEdit_longtext.redo)
        self.connect(self.pushButton_print, QtCore.SIGNAL("clicked()"), self.editor_print_preview)
        self.table_dialog = ui_EditorHtmlTableSettings(self, self.textEdit_longtext)
        self.connect(self.pushButton_table, QtCore.SIGNAL("clicked()"), self.table_dialog.show)
        self.highlighter = ui_TagHighlighter(self.textEdit_longtext, "Classic")
        # We need our own context menu for tables
        self.textEdit_longtext.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.textEdit_longtext.customContextMenuRequested.connect(self.context)

    def editor_bold(self):
        if self.textEdit_longtext.fontWeight() == QtGui.QFont.Bold:
            self.textEdit_longtext.setFontWeight(QtGui.QFont.Normal)
        else:
            self.textEdit_longtext.setFontWeight(QtGui.QFont.Bold)

    def editor_italic(self):
        state = self.textEdit_longtext.fontItalic()
        self.textEdit_longtext.setFontItalic(not state)

    def editor_underline(self):
        state = self.textEdit_longtext.fontUnderline()
        self.textEdit_longtext.setFontUnderline(not state)

    def editor_bulletList(self):
        cursor = self.textEdit_longtext.textCursor()
        cursor.insertList(QtGui.QTextListFormat.ListDisc)

    def editor_numberList(self):
        cursor = self.textEdit_longtext.textCursor()
        cursor.insertList(QtGui.QTextListFormat.ListDecimal)

    def editor_print_preview(self):
        preview = QtGui.QPrintPreviewDialog()
        preview.paintRequested.connect(lambda p: self.textEdit_longtext.print_(p))
        preview.exec_()

    def context(self,pos):
        cursor = self.textEdit_longtext.textCursor()
        # Grab the current table, if there is one
        table = cursor.currentTable()
        # Above will return 0 if there is no current table, in which case
        # we call the normal context menu. If there is a table, we create
        # our own context menu specific to table interaction
        if table:
            menu = QtGui.QMenu(self)
            appendRowAction = QtGui.QAction(u"Добавить строку",self)
            appendRowAction.triggered.connect(lambda: table.appendRows(1))
            appendColAction = QtGui.QAction(u"Добавить столбец",self)
            appendColAction.triggered.connect(lambda: table.appendColumns(1))
            removeRowAction = QtGui.QAction(u"Удалить строку",self)
            removeRowAction.triggered.connect(self.removeRow)
            removeColAction = QtGui.QAction(u"Удалить столбце",self)
            removeColAction.triggered.connect(self.removeCol)
            insertRowAction = QtGui.QAction(u"Вставить строку",self)
            insertRowAction.triggered.connect(self.insertRow)
            insertColAction = QtGui.QAction(u"Вставить столбец",self)
            insertColAction.triggered.connect(self.insertCol)
            mergeAction = QtGui.QAction(u"Объединить ячейки",self)
            mergeAction.triggered.connect(lambda: table.mergeCells(cursor))
            # Only allow merging if there is a selection
            if not cursor.hasSelection():
                mergeAction.setEnabled(False)
            splitAction = QtGui.QAction(u"Разделить ячейки",self)
            cell = table.cellAt(cursor)
            # Only allow splitting if the current cell is larger
            # than a normal cell
            if cell.rowSpan() > 1 or cell.columnSpan() > 1:
                splitAction.triggered.connect(lambda: table.splitCell(cell.row(),cell.column(),1,1))
            else:
                splitAction.setEnabled(False)
            menu.addAction(appendRowAction)
            menu.addAction(appendColAction)
            menu.addSeparator()
            menu.addAction(removeRowAction)
            menu.addAction(removeColAction)
            menu.addSeparator()
            menu.addAction(insertRowAction)
            menu.addAction(insertColAction)
            menu.addSeparator()
            menu.addAction(mergeAction)
            menu.addAction(splitAction)
            # Convert the widget coordinates into global coordinates
            pos = self.mapToGlobal(pos)
            # Move the menu to the new position
            menu.move(pos)
            menu.show()
        else:
            event = QtGui.QContextMenuEvent(QtGui.QContextMenuEvent.Mouse,QtCore.QPoint())
            self.textEdit_longtext.contextMenuEvent(event)

    def removeRow(self):
        # Grab the cursor
        cursor = self.textEdit_longtext.textCursor()
        # Grab the current table (we assume there is one, since
        # this is checked before calling)
        table = cursor.currentTable()
        # Get the current cell
        cell = table.cellAt(cursor)
        # Delete the cell's row
        table.removeRows(cell.row(),1)

    def removeCol(self):
        # Grab the cursor
        cursor = self.textEdit_longtext.textCursor()
        # Grab the current table (we assume there is one, since
        # this is checked before calling)
        table = cursor.currentTable()
        # Get the current cell
        cell = table.cellAt(cursor)
        # Delete the cell's column
        table.removeColumns(cell.column(),1)

    def insertRow(self):
        # Grab the cursor
        cursor = self.textEdit_longtext.textCursor()
        # Grab the current table (we assume there is one, since
        # this is checked before calling)
        table = cursor.currentTable()
        # Get the current cell
        cell = table.cellAt(cursor)
        # Insert a new row at the cell's position
        table.insertRows(cell.row(),1)

    def insertCol(self):
        # Grab the cursor
        cursor = self.textEdit_longtext.textCursor()
        # Grab the current table (we assume there is one, since
        # this is checked before calling)
        table = cursor.currentTable()
        # Get the current cell
        cell = table.cellAt(cursor)
        # Insert a new row at the cell's position
        table.insertColumns(cell.column(),1)

    def clear_fonts(self):
        # TODO: тут нужно всё поправить + поднимать вызов по событию "вставка" в браузер.
        readable_font = QtGui.QFont()
        readable_font.setPointSize(10)
        readable_font.setStyleHint(QtGui.QFont.Courier)
        self.textEdit_longtext.selectAll()
        self.textEdit_longtext.setCurrentFont(readable_font)

    def set_state_to_add_new(self, suggested_tags = None, text_template = "", header = ""):
        # self.record_entity создается перед закрытием с кнопкой "ОК"
        self.setWindowTitle(unicode(u"Создание заметки"))
        existing_hashtags = db_main.get_hashtags_text_list()
        self.highlighter.update_keywords(existing_hashtags)
        self.textEdit_longtext.refresh_hash_completion(existing_hashtags)
        self.my_mode = 0
        self.record_entity = None
        self.preset_tags = []
        self.label_date_added.setText(datetime.date.today().strftime("%Y %B %d (%A)")) # перед "ОК" всё равно меняется
        self.lineEdit_headline.setText(header)
        s = ""
        if suggested_tags is None:
            suggested_tags = []
        suggested_tags.append(user_name)
        for h_i in suggested_tags:
            s += "#" + h_i + ", "
        if len(suggested_tags) > 0: s += "<br><br>"
        s += text_template
        self.textEdit_longtext.setHtml(s)
        self.clear_fonts()

    def set_state_to_edit(self, record_entity):
        # self.record_entity используется только для заполнения формы и меняется только перед закрытием если "ОК"
        self.setWindowTitle(unicode(u"Изменение заметки"))
        self.clear_fonts()
        existing_hashtags = db_main.get_hashtags_text_list()
        self.highlighter.update_keywords(existing_hashtags)
        self.textEdit_longtext.refresh_hash_completion(existing_hashtags)
        self.my_mode = 1
        self.record_entity = record_entity
        self.preset_tags = self.record_entity.get_tags_text()
        self.label_date_added.setText(self.record_entity.date_added.strftime("%Y.%m.%d"))
        self.lineEdit_headline.setText(self.record_entity.headline)
        self.textEdit_longtext.setHtml(self.record_entity.long_html_text)
        self.clear_fonts()

    def accept(self):
        self.clear_fonts()
        is_ok = True
        if is_ok:
            if self.lineEdit_headline.text() == "":
                QtGui.QMessageBox.information(self,unicode(u"Ошибка ввода"),
                                              unicode(u"Добавьте заголовок"))
                self.lineEdit_headline.setFocus()
                is_ok = False
        tag_list = utils.parse_hashtags(unicode(self.textEdit_longtext.toPlainText()))
        if is_ok:  #Проверяем те тэги, что были предначертаны - от них можно отказаться
            for ht_i in self.preset_tags:
                if not(ht_i in tag_list):
                    ans = QtGui.QMessageBox.question(self,unicode(u"Пропущен хэш-тэг"), unicode(u'Добавить #' + ht_i + u" ?"),
                                                     QtGui.QMessageBox.Yes, QtGui.QMessageBox.No,QtGui.QMessageBox.Cancel)
                    if ans == QtGui.QMessageBox.Yes:
                        self.textEdit_longtext.insertHtml(ht_i)
                        tag_list += [ht_i]
                    elif ans == QtGui.QMessageBox.No: #Ну нет так нет. Значит, лишний был.
                        pass
                    elif ans == QtGui.QMessageBox.Cancel:
                        is_ok = False
                        break
        if is_ok:  #Но всё-таки что-нибудь да должно быть
            if len(tag_list) == 0:
                is_ok = False
                QtGui.QMessageBox.information(self,unicode(u"Ошибка ввода"),
                                              unicode(u"В тексте нет ни одного хэш-тэга - добавьте"))
        if is_ok:  #Проверяем теги на существование в базе
            record_tags = db_main.get_hashtags_from_names(tag_list)
            #print record_tags  #TODO: проверить что тут none нету
            found_names = [rec_i.text for rec_i in record_tags]
            not_found = []
            for ht_i in tag_list:
                if not(ht_i in found_names):
                    not_found += [ht_i]
            for ht_i in not_found:
                msg = unicode(u'Впервые вижу тэг #' + ht_i + u' - уверены, что не опечатались?')
                ans = QtGui.QMessageBox.question(self,unicode(u'Новый хэш-тэг'), unicode(msg),
                                                 QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
                if ans == QtGui.QMessageBox.Yes:
                    #Создаем новый тэг
                    new_h = db_main.c_hastag(text = ht_i)
                    record_tags += [new_h]
                elif ans == QtGui.QMessageBox.No:
                    is_ok = False
                    break
        if is_ok:
            # Собираем переменную и в базу
            if self.my_mode == 0: #Новый
                self.record_entity = db_main.c_crm_record()
                self.record_entity.date_added = datetime.date.today()
            self.record_entity.match_with_tags(record_tags)
            self.record_entity.fix_hashtag_text() #подобранные тэги записываются в строку для быстрого доступа
            self.record_entity.long_html_text = unicode(self.textEdit_longtext.toHtml(),encoding='utf-8')
            self.record_entity.headline = unicode(self.lineEdit_headline.text(),encoding='utf-8')
            super(gui_DialogCrm_EditSimpleRecord, self).accept()

    def reject(self):
        super(gui_DialogCrm_EditSimpleRecord, self).reject()

    def run_dialog(self):
        user_decision = self.exec_()  #0 или 1
        if user_decision == QtGui.QDialog.Accepted:
            return [user_decision, self.record_entity]
        elif user_decision == QtGui.QDialog.Rejected:
            return [user_decision, None]

class gui_DialogCrm_EditCounterpartyData(QtGui.QDialog, Ui_DialogCrm_EditCounterparty):
    def __init__(self, parent=None):
        super(gui_DialogCrm_EditCounterpartyData, self).__init__(parent)
        self.setupUi(self) #Метод от QtDesigner
        self.comboBox_cptype.setModel(parent.gui_models_agent_type_list)
        self.connect(self.lineEdit_visible_name, QtCore.SIGNAL("textChanged(QString)"), self.update_visible_hashtag)

    def update_visible_hashtag(self, new_name):
        new_name_n = unicode(unicode_codec.toUnicode(new_name))
        self.label_hashname.setText(u"#" + utils.trim_whitespaces(new_name_n).lower())

    def set_state_to_add_new(self, type_name = ""):
        self.setWindowTitle(unicode(u"Создание контрагента"))
        self.my_mode = 0
        self.cp_entity = None
        type_indx = self.comboBox_cptype.findData(type_name,40)
        if type_indx>=0:
            self.comboBox_cptype.setCurrentIndex(type_indx)
        self.comboBox_cptype.setEnabled(True)
        self.lineEdit_visible_name.setText("")
        self.lineEdit_full_name.setText("")
        self.lineEdit_vatnum.setText("")
        self.lineEdit_acc_code.setText("")

    def set_state_to_edit(self, cp_entity):
        self.setWindowTitle(unicode(u"Изменение контрагента"))
        self.my_mode = 1
        self.cp_entity = cp_entity  #Обращаемся только уже при записи
        type_indx = self.comboBox_cptype.findData(cp_entity.discriminator,40)
        self.comboBox_cptype.setCurrentIndex(type_indx)
        self.comboBox_cptype.setEnabled(False)
        self.lineEdit_visible_name.setText(cp_entity.name)
        self.lineEdit_full_name.setText(cp_entity.full_name)
        self.lineEdit_vatnum.setText(cp_entity.inn)
        self.lineEdit_acc_code.setText(cp_entity.account_system_code)

    def accept(self):
        #Логика здесь
        is_var_ok = True
        if is_var_ok:
            ind = self.comboBox_cptype.currentIndex()
            selected_type = self.comboBox_cptype.itemData(ind, 35).toPyObject()
            if selected_type is None:
                QtGui.QMessageBox.information(self,unicode(u"Ошибка ввода"),unicode(u"Необходимо выбрать тип контрагента"))
                is_var_ok = False
        if is_var_ok: #Проверяем, что имя есть
            work_name = unicode(self.lineEdit_visible_name.text())
            if work_name == "":
                QtGui.QMessageBox.information(self,unicode(u"Ошибка ввода"),unicode(u"Необходимо ввести название"))
                is_var_ok = False
        if is_var_ok: #Проверяем, что такого имени в базе больше нет
            # По идее, имя уникально. Но на всякий случай, проверяем сразу весь лист - мы же из Access еще подтянем..
            agents_with_same_name = db_main.get_agent_list_by_name(work_name)
            if len(agents_with_same_name) > 0:
                a_msg = u"Найден контрагент с таким же именем - смените имя!"
                QtGui.QMessageBox.information(self, unicode(u"Ошибка ввода"), a_msg)
                is_var_ok = False
        if is_var_ok: #Проверяем, что ИНН есть
            cp_inn = unicode(self.lineEdit_vatnum.text())
            if cp_inn == "":
                a_msg = u"Вы не ввели ИНН. Подтвержаете ввод без ИНН?"
                a_reply = QtGui.QMessageBox.question(self, unicode(u'Подтвердите'), a_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
                if not(a_reply == QtGui.QMessageBox.Yes):
                    is_var_ok = False
        if is_var_ok: #Проверяем, что такого ИНН в базе больше нет
            agents_with_same_inn = db_main.get_agent_list_by_inn(work_name)
            if len(agents_with_same_inn) > 0:
                a_msg = u"Найден контрагент с таким же ИНН - не могу перезаписать"
                QtGui.QMessageBox.information(self, unicode(u"Ошибка ввода"), a_msg)
                is_var_ok = False
        if is_var_ok:
            cp_acc_code = unicode(self.lineEdit_acc_code.text())
            cp_full_name = unicode(self.lineEdit_full_name.text())
        if is_var_ok:
            if self.my_mode == 1:
                old_name = self.cp_entity.name
                new_name = work_name
                if old_name.lower() <> new_name.lower():
                    a_msg = u"Уверены, что хотите переименовать контрагента? Имя должно приводить к уникальному хештэгу - это не проверяется."
                    a_msg += u"Если назовёте контрагента ключевым хештэгом, записи просто перепутаются."
                    a_reply = QtGui.QMessageBox.question(self, unicode(u'Подтвердите'), a_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
                    if not(a_reply == QtGui.QMessageBox.Yes):
                        is_var_ok = False
        if is_var_ok:
            if self.my_mode == 0:  #Создание новой
                self.cp_entity = selected_type()
            if self.my_mode == 1:
                old_name = self.cp_entity.name.lower()
                new_name = work_name.lower()
                db_main.rename_hashtag_usages(old_name, new_name)
            self.cp_entity.name = work_name
            self.cp_entity.full_name = cp_full_name
            self.cp_entity.inn = cp_inn
            self.cp_entity.account_system_code = cp_acc_code
            super(gui_DialogCrm_EditCounterpartyData, self).accept()

    def reject(self):
        super(gui_DialogCrm_EditCounterpartyData, self).reject()

    def run_dialog(self):
        user_decision = self.exec_()  #0 или 1
        if user_decision == QtGui.QDialog.Accepted:
            return [user_decision, self.cp_entity]
        elif user_decision == QtGui.QDialog.Rejected:
            return [user_decision, None]

class gui_DialogCrm_EditContact(QtGui.QDialog, Ui_DialogCrm_EditContact):
    def __init__(self, parent=None):
        super(gui_DialogCrm_EditContact, self).__init__(parent)
        self.setupUi(self) #Метод от QtDesigner
        self.my_entity = None
        self.cp_list_model = gui_counterparty_list_model()
        self.cont_details_model = gui_contacts_details_model()
        self.comboBox_company.setModel(self.cp_list_model)
        self.tableView_contact_info.setModel(self.cont_details_model)
        self.connect(self.checkBox_is_person, QtCore.SIGNAL("stateChanged(int)"), self.chbx_person_change)
        self.connect(self.pushButton_add_cell_work, QtCore.SIGNAL("clicked()"), self.add_details_cell_work)
        self.connect(self.pushButton_add_cell_personal, QtCore.SIGNAL("clicked()"), self.add_details_cell_personal)
        self.connect(self.pushButton_add_phone, QtCore.SIGNAL("clicked()"), self.add_details_phone)
        self.connect(self.pushButton_add_email, QtCore.SIGNAL("clicked()"), self.add_details_email)
        self.connect(self.pushButton_add_skype, QtCore.SIGNAL("clicked()"), self.add_details_skype)
        self.connect(self.pushButton_add_birthday, QtCore.SIGNAL("clicked()"), self.add_details_birthdate)
        self.connect(self.pushButton_add_website, QtCore.SIGNAL("clicked()"), self.add_details_website)
        self.connect(self.pushButton_add_address_post, QtCore.SIGNAL("clicked()"), self.add_details_address_post)
        self.connect(self.pushButton_add_address_fact, QtCore.SIGNAL("clicked()"), self.add_details_address_fact)
        self.connect(self.pushButton_add_row, QtCore.SIGNAL("clicked()"), self.add_details_any)
        self.connect(self.pushButton_delete_row, QtCore.SIGNAL("clicked()"), self.delete_detail)

    def chbx_person_change(self, new_state):
        # Не все кнопки нужны не для физического лица - так, удобство
        migrating_widgets = [self.pushButton_add_cell_work, self.pushButton_add_birthday, self.pushButton_add_skype,
                             self.pushButton_add_cell_personal, self.lineEdit_name, self.lineEdit_job]
        if new_state == QtCore.Qt.Checked:
            for b_i in migrating_widgets:
                b_i.setEnabled(True)
        elif new_state == QtCore.Qt.Unchecked:
            for b_i in migrating_widgets:
                b_i.setEnabled(False)

    def set_state_to_add_new(self, predef_agent = None):
        self.setWindowTitle(unicode(u"Создание контакта"))
        self.my_mode = 0
        if predef_agent is not None:
            cp_indx = self.comboBox_company.findData(predef_agent.string_key(),40)
            self.comboBox_company.setCurrentIndex(cp_indx)
        self.cont_details_model.update_data([])
        self.checkBox_is_person.setCheckState(QtCore.Qt.Checked)
        self.lineEdit_name.setText("")
        self.lineEdit_job.setText("")
        self.plainTextEdit_additional_info.setPlainText = ""
        self.checkBox_SubsPrices.setCheckState(QtCore.Qt.Unchecked)
        self.checkBox_SubsLogistics.setCheckState(QtCore.Qt.Unchecked)
        self.checkBox_SubsPayments.setCheckState(QtCore.Qt.Unchecked)

    def set_state_to_edit(self, contact_entity):
        self.setWindowTitle(unicode(u"Изменение контакта"))
        self.my_mode = 1
        self.my_entity = contact_entity  # Используем только при "accept"
        self.cont_details_model.update_data(contact_entity.details)
        cp_indx = self.comboBox_company.findData(contact_entity.company.string_key(),40)
        self.comboBox_company.setCurrentIndex(cp_indx)
        if self.my_entity.is_person:
            self.checkBox_is_person.setCheckState(QtCore.Qt.Checked)
            self.lineEdit_name.setText(contact_entity.name)
            self.lineEdit_job.setText(contact_entity.job)
        else:
            self.checkBox_is_person.setCheckState(QtCore.Qt.Unchecked)
            self.lineEdit_name.setText("")
            self.lineEdit_job.setText("")
        if contact_entity.additional_info is not None:
            self.plainTextEdit_additional_info.setPlainText(contact_entity.additional_info)
        else:
            self.plainTextEdit_additional_info.setPlainText("")
        if contact_entity.subs_to_prices:
            self.checkBox_SubsPrices.setCheckState(QtCore.Qt.Checked)
        else:
            self.checkBox_SubsPrices.setCheckState(QtCore.Qt.Unchecked)
        if contact_entity.subs_to_logistics:
            self.checkBox_SubsLogistics.setCheckState(QtCore.Qt.Checked)
        else:
            self.checkBox_SubsLogistics.setCheckState(QtCore.Qt.Unchecked)
        if contact_entity.subs_to_payments:
            self.checkBox_SubsPayments.setCheckState(QtCore.Qt.Checked)
        else:
            self.checkBox_SubsPayments.setCheckState(QtCore.Qt.Unchecked)

    def add_details_cell_work(self):
        self.cont_details_model.insertNewDetail(u"Мобильный рабочий", u"+7 (XXX) XXX-XX-XX", True)

    def add_details_cell_personal(self):
        self.cont_details_model.insertNewDetail(u"Мобильный личный", u"+7 (XXX) XXX-XX-XX", True)

    def add_details_cell_personal(self):
        self.cont_details_model.insertNewDetail(u"Мобильный личный", u"+7 (...) ...-...-...", True)

    def add_details_phone(self):
        self.cont_details_model.insertNewDetail(u"Городской", u"(код города ...) ...-...-... (доб. ...)", True)

    def add_details_email(self):
        self.cont_details_model.insertNewDetail(u"E-mail", u"somebody@somewhere.com", True)

    def add_details_skype(self):
        self.cont_details_model.insertNewDetail(u"Skype", u"", True)

    def add_details_birthdate(self):
        self.cont_details_model.insertNewDetail(u"День рождения", u"DD.MM.YYYY", True)

    def add_details_website(self):
        self.cont_details_model.insertNewDetail(u"web-сайт", u"somewhere.com", True)

    def add_details_address_post(self):
        self.cont_details_model.insertNewDetail(u"Почтовый адрес", u"Индекс ..., г. ... , ул. ..., дом ...", True)

    def add_details_address_fact(self):
        self.cont_details_model.insertNewDetail(u"Физический адрес", u"Индекс ..., г. ... , ул. ..., дом ...", True)

    def add_details_any(self):
        self.cont_details_model.insertNewDetail(u"Тип контакта", u"Значение контакта", False)

    def delete_detail(self):
        self.cont_details_model.deleteRow(self.tableView_contact_info.selectionModel().selectedIndexes()[0])

    def accept(self):
        #Логика здесь
        is_var_ok = True
        if is_var_ok:
            if self.checkBox_is_person.checkState() == QtCore.Qt.Checked:
                is_person = True
                contact_name = unicode(self.lineEdit_name.text())
                contact_job = unicode(self.lineEdit_job.text())
                if contact_name == "":
                    QtGui.QMessageBox.information(self,unicode(u"Ошибка ввода"),unicode(u"Укажите имя человека"))
                    is_var_ok = False
            else:
                is_person = False
                contact_name = ""
                contact_job = ""
        if is_var_ok:
            row = self.comboBox_company.currentIndex()
            if row>=0:
                company_emp = self.comboBox_company.itemData(row, 35).toPyObject()
            else:
                QtGui.QMessageBox.information(self,unicode(u"Ошибка ввода"),unicode(u"Не выбрана компания"))
                is_var_ok = False
        if is_var_ok:
            contacts_list = self.cont_details_model.get_all_data()
            if len(contacts_list) == 0:
                QtGui.QMessageBox.information(self,unicode(u"Ошибка ввода"),unicode(u"Добавьте хоть один контакт"))
                is_var_ok = False
        if is_var_ok:
            cont_add_info = unicode(unicode_codec.fromUnicode(self.plainTextEdit_additional_info.toPlainText()))
            if self.checkBox_SubsPrices.checkState() == QtCore.Qt.Checked:
                is_subs_to_prices = True
            else:
                is_subs_to_prices = False
            if self.checkBox_SubsLogistics.checkState() == QtCore.Qt.Checked:
                is_subs_to_logistics = True
            else:
                is_subs_to_logistics = False
            if self.checkBox_SubsPayments.checkState() == QtCore.Qt.Checked:
                is_subs_to_payments = True
            else:
                is_subs_to_logistics = False
        if is_var_ok:
            #Собираем переменную
            if self.my_mode == 0:  #Создание новой
                self.my_entity = db_main.c_crm_contact()
            if self.my_mode == 1:  #Изменение существующей
                if company_emp <> self.my_entity.company:
                    a_msg = unicode(u"Изменился контрагент - уверены, что %s ?"%(company_emp.name))
                    a_reply = QtGui.QMessageBox.question(self, unicode(u'Подтвердите'), a_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
                    if a_reply == QtGui.QMessageBox.No:
                        is_var_ok = False
            if is_var_ok:
                self.my_entity.company = company_emp
                self.my_entity.is_person = is_person
                self.my_entity.name = contact_name
                self.my_entity.job = contact_job
                self.my_entity.additional_info = cont_add_info
                self.my_entity.subs_to_prices = is_subs_to_prices
                self.my_entity.subs_to_logistics = is_subs_to_logistics
                self.my_entity.subs_to_prices = is_subs_to_prices
                for cont_det in contacts_list:
                    new_type = cont_det[0]
                    new_value = cont_det[1]
                    new_is_fixed = cont_det[2]
                    old_rec_id = cont_det[3]
                    if old_rec_id is None:
                        self.my_entity.add_new_contact_detail(new_type, new_value, new_is_fixed)
                    else: #Если не найдёт такого rec_id, создаст новый
                        self.my_entity.change_existing_contact_detail(old_rec_id, new_type, new_value, new_is_fixed)
                super(gui_DialogCrm_EditContact, self).accept()

    def reject(self):
        super(gui_DialogCrm_EditContact, self).reject()

    def run_dialog(self):
        user_decision = self.exec_()  #0 или 1
        if user_decision == QtGui.QDialog.Accepted:
            return [user_decision, self.my_entity]
        elif user_decision == QtGui.QDialog.Rejected:
            return [user_decision, None]

class gui_DelegateSelectMaterial(QtGui.QStyledItemDelegate):
    """
    A delegate that places a fully functioning QComboBox in every
    cell of the column to which it's applied
    """
    def __init__(self, parent, data_model):
        QtGui.QStyledItemDelegate.__init__(self, parent)
        self.data_model = data_model

    def createEditor(self, parent, option, index):
        mat_cmbx = QtGui.QComboBox(parent)
        mat_cmbx.setModel(self.data_model)
        #TODO: выбрать элемент в создаваемом едиторе. Сложно блин.
        self.connect(mat_cmbx, QtCore.SIGNAL("currentIndexChanged(int)"), self, QtCore.SLOT("currentIndexChanged()"))
        return mat_cmbx

    def setEditorData(self, editor, index):
        #Что останется после выбора
        editor.blockSignals(True)
        #editor.setCurrentIndex(int(index.model().data(index, QtCore.Qt.DisplayRole)))
        editor.setCurrentIndex(int(index.row()))
        editor.blockSignals(False)

    def setModelData(self, editor, model, index):
        model.blockSignals(True)
        row_in_cmbx = editor.currentIndex()
        the_data = editor.itemData(row_in_cmbx, 35).toPyObject() #Материал будет
        model.setData(index, the_data, QtCore.Qt.EditRole)
        model.blockSignals(False)

    @QtCore.pyqtSlot()
    def currentIndexChanged(self):
        self.commitData.emit(self.sender())

class gui_Node_project(c_meganode.gui_Node):
    #С помощью этого отображаем проекты в дереве
    def set_data(self, a_project):
        self._data = a_project

    def typeInfo(self):
        return "PROJECT"

    def get_data(self):
        return self._data

    def get_dateFrom(self):
        return unicode(self._data.get_min_step_date().strftime("%d %b %y"))

    def get_dateTill(self):
        return unicode(self._data.get_max_step_date().strftime("%d %b %y"))

    def get_nearest_event_date(self):
        near_date = self._data.get_first_expected_event_date()
        ans =""
        if near_date is None:
            ans = "done"
        else:
            ans = unicode(near_date.strftime("%d %b %Y"))
        return ans

    def get_status(self):
        if self._data.is_completed:
            nice_status = unicode(u"Выполнен")
        else:
            nice_status = unicode(u"Не выполнен")
        return nice_status

class gui_Node_step(c_meganode.gui_Node):
    #С помощью этого отображаем этапы в дереве
    def set_data(self, a_step):
        self._data = a_step

    def get_data(self):
        return self._data

    def get_dateFrom(self):
        if self._data.is_scheduled:
            return unicode(self._data.planned_time_expected.strftime("%d %b"))

    def get_nearest_event_date(self):
        if self._data.is_scheduled:
            return unicode(self._data.planned_time_expected.strftime("  %d %b"))

    def get_status(self):
        db_main.the_session_handler.merge_object_to_session(self._data)
        if self._data.is_completed:
            nice_status = unicode(u"Выполнен")
        else:
            nice_status = unicode(u"Не выполнен")
        return nice_status

    def typeInfo(self):
        return "STEP"

class gui_project_tree_model(QtCore.QAbstractItemModel):
    #Проектам - самобытную логику.
    def __init__(self, parent=None):
        super(gui_project_tree_model, self).__init__(parent)
        rootNode = c_meganode.gui_Node("Projects")
        self._rootNode = rootNode
        self._nodes_list = []  #Just to keep links - gui nodes
        self.updateNodeTree()  #Загрузка из БД

    def updateNodeTree(self):
        #Удаляем все ноды и пишем их заново
        self.beginResetModel()
        self._rootNode._childrenNodes = []
        #Создаем закладки - по типам проекты разложим
        fold_clord = c_meganode.gui_Node(u"Заказы клиентов",self._rootNode)
        fold_supord = c_meganode.gui_Node(u"Заказы поставщикам",self._rootNode)
        fold_regsh = c_meganode.gui_Node(u"Процессы закупок на склад",self._rootNode)
        fold_regpay = c_meganode.gui_Node(u"Регулярные платежи",self._rootNode)
        fold_oth = c_meganode.gui_Node(u"Прочее",self._rootNode)
        self._nodes_list += [fold_clord, fold_supord, fold_regsh, fold_regpay, fold_oth]
        #Теперь считываем проекты
        for proj_i in db_main.get_proj_list():
            if proj_i.__class__.__name__ == "c_project_client_order":
                parent_node = fold_clord
                proj_node_i = gui_Node_project(unicode(proj_i.client_model.name + " : " + proj_i.AgreementName), parent_node)
            elif proj_i.__class__.__name__ == "c_project_supplier_order":
                parent_node = fold_supord
                proj_node_i = gui_Node_project(unicode(proj_i.AgreementName), parent_node)
            else:
                parent_node = fold_oth
                proj_node_i = gui_Node_project(unicode(proj_i.string_key()), parent_node)
            proj_node_i.set_data(proj_i)
            self._nodes_list += [proj_node_i]
            #Создаём GUI ноды для этапов проекта
            proj_nodes_dict = dict()  #временный словарик, чтобы наглядней переаттачить ноды
            proj_nodes_dict[proj_i.root_step.string_key()] = proj_node_i  #Подменяем root-ноду самим проектом
            for st_i in proj_i.iter_steps_depth():
                parent_gui_node = proj_nodes_dict[st_i.parent_step.string_key()]
                st_node_i = gui_Node_step(unicode(st_i.step_name), parent_gui_node)
                st_node_i.set_data(st_i)
                proj_nodes_dict[st_i.string_key()] = st_node_i
                self._nodes_list += [st_node_i]  #Просто для ссылки
        self.endResetModel()

    """INPUTS: QModelIndex"""
    """OUTPUT: int"""
    def rowCount(self, parent):
        if not parent.isValid():
            parentNode = self._rootNode
        else:
            parentNode = parent.internalPointer()
        return parentNode.childCount()

    """INPUTS: QModelIndex"""
    """OUTPUT: int"""
    def columnCount(self, parent):
        return 3

    """INPUTS: int, Qt::Orientation, int"""
    """OUTPUT: QVariant, strings are cast to QString which is a QVariant"""
    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if section == 0:
                return "Name"
            elif section == 1:
                return "Next event date"
            elif section == 2:
                return "Status"

    """INPUTS: QModelIndex"""
    """OUTPUT: int (flag)"""
    def flags(self, index):
        if index.column() == 2:
            node = self.getNode(index)
            if node.typeInfo() == "STEP":
                return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
            else:
                return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    """INPUTS: QModelIndex"""
    """OUTPUT: QModelIndex"""
    """Should return the parent of the node with the given QModelIndex"""
    def parent(self, index):
        node = self.getNode(index)
        parentNode = node.get_parentNode()
        if parentNode == self._rootNode:
            return QtCore.QModelIndex()
        return self.createIndex(parentNode.row(), 0, parentNode)

    """INPUTS: int, int, QModelIndex"""
    """OUTPUT: QModelIndex"""
    """Should return a QModelIndex that corresponds to the given row, column and parent node"""
    def index(self, row, column, parent):
        parentNode = self.getNode(parent)
        childItem = parentNode.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    """CUSTOM"""
    """INPUTS: QModelIndex"""
    def getNode(self, index):
        if index.isValid():
            node = index.internalPointer()
            if node:
                return node
        return self._rootNode

    """INPUTS: QModelIndex, int"""
    """OUTPUT: QVariant, strings are cast to QString which is a QVariant"""
    def data(self, index, role):
        if not index.isValid():
            return None
        node = index.internalPointer()
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            if index.column() == 0:
                return node.name()
            if index.column() == 1:
                if hasattr(node,"get_nearest_event_date"):
                    return node.get_nearest_event_date()
            if index.column() == 2:
                if hasattr(node,"get_status"):
                    return node.get_status()
        if role == 35: #А почему бы и нет? Получаю данную из строки
            if hasattr(node,"get_data"):
                return dict(data_type = node.typeInfo(), data_value = node.get_data())
            else:
                return None

class gui_Node_group_of_agents(c_meganode.gui_Node):
    def __init__(self, gr_name, parent):
        super(gui_Node_group_of_agents, self).__init__(gr_name, parent)

    def typeInfo(self):
        return "GROUP"

    def iter_all_agents_in_a_group(self):
        for n_i in self.iter_all_children():
            if hasattr(n_i, "get_agent"):
                yield n_i.get_agent()

class gui_Node_agent(c_meganode.gui_Node):
    def __init__(self, an_agent, parent):
        super(gui_Node_agent, self).__init__(an_agent.name, parent)
        self.agent = an_agent

    def get_agent(self):
        return self.agent

    def typeInfo(self):
        return "AGENT"

class gui_Node_client(gui_Node_agent):
    def typeInfo(self):
        return "CLIENT"

class gui_Node_supplier(gui_Node_agent):
    def typeInfo(self):
        return "SUPPLIER"

class gui_counterparty_tree_model(QtCore.QAbstractItemModel):
    def __init__(self,  parent = None):
        super(gui_counterparty_tree_model, self).__init__(parent)
        rootNode = c_meganode.gui_Node("Counterparties")
        self._rootNode = rootNode
        self._nodes_list = []  #Just to keep links - gui nodes
        self.update_counterparty_tree()  #Загрузка из БД

    def update_counterparty_tree(self):
        self.beginResetModel()
        self._rootNode._childrenNodes = []
        #Создаем закладки - по типам проекты разложим
        fold_active_clients = gui_Node_group_of_agents(u"Клиенты активные",self._rootNode)
        fold_nonactive_clients = gui_Node_group_of_agents(u"Клиенты не активные",self._rootNode)
        fold_suppliers = gui_Node_group_of_agents(u"Поставщики",self._rootNode)
        fold_oth = gui_Node_group_of_agents(u"Прочие",self._rootNode)
        self._nodes_list += [fold_active_clients, fold_nonactive_clients, fold_suppliers, fold_oth]
        #Теперь всех агентов
        for ag_i in db_main.get_agent_list():
            if ag_i.discriminator == "client":
                if len(ag_i.material_flows) > 0:
                    ag_node_i = gui_Node_client(ag_i, fold_active_clients)
                else:
                    ag_node_i = gui_Node_client(ag_i, fold_nonactive_clients)
            elif ag_i.discriminator == "supplier":
                ag_node_i = gui_Node_supplier(ag_i, fold_suppliers)
            elif ag_i.discriminator == "agent": #Base class
                ag_node_i = gui_Node_agent(ag_i, fold_oth)
            self._nodes_list += [ag_node_i]
        self.endResetModel()

    def rowCount(self, parent):
        if not parent.isValid():
            parentNode = self._rootNode
        else:
            parentNode = parent.internalPointer()
        return parentNode.childCount()

    def columnCount(self, parent):
        return 1

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if section == 0:
                return u"Контрагенты"

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def parent(self, index):
        node = self.getNode(index)
        parentNode = node.get_parentNode()
        if parentNode == self._rootNode:
            return QtCore.QModelIndex()
        return self.createIndex(parentNode.row(), 0, parentNode)

    def index(self, row, column, parent):
        parentNode = self.getNode(parent)
        childItem = parentNode.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def getNode(self, index):
        if index.isValid():
            node = index.internalPointer()
            if node:
                return node
        return self._rootNode

    def data(self, index, role):
        if not index.isValid():
            return None
        node = index.internalPointer()
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            if index.column() == 0:
                return node.name()
            if index.column() == 1:
                return ""
        if role == 55: #Для типа ноды
            return node
        if role == 35:
            if hasattr(node,"get_agent"):
                return node.get_agent()
            else:
                return None

class gui_client_material_flows_model(QtCore.QAbstractTableModel):
    def __init__(self,  parent = None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.__mat_flows = []

    def update_material_flow_table(self, client = None):
        self.beginResetModel()
        self.__mat_flows = []
        for m_f_i in db_main.get_mat_flows_list(client):
            self.__mat_flows += [m_f_i]
        self.endResetModel()

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                if section == 0:
                    return unicode(u"Материал")
                if section == 1:
                    return unicode(u"Объем потребления")
                if section == 2:
                    return unicode(u"Частота потребления (дни)")

    def rowCount(self, parent):
        return len(self.__mat_flows)

    def columnCount(self, parent):
        return 3

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            if index.column() == 0:
                return self.__mat_flows[row].material_type.material_type_name
            if index.column() == 1:
                mu = self.__mat_flows[row].material_type.measure_unit
                return unicode(simple_locale.number2string(self.__mat_flows[row].stats_mean_volume)) + " " + mu
            if index.column() == 2:
                return unicode(simple_locale.number2string(self.__mat_flows[row].stats_mean_timedelta))
        if role == 35: #Наша роль для передачи данных из таблицы
            row = index.row()
            if index.column() == 0:
                return self.__mat_flows[row].material_type
            if index.column() == 1:
                return self.__mat_flows[row].stats_mean_volume
            if index.column() == 2:
                return self.__prices[row].stats_mean_timedelta
        if role == 45:  #роль для чтения "всей строки"
            row = index.row()
            return self.__mat_flows[row]

    def setData(self, index, value, role = QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            row = index.row()
            column = index.column()
            if column == 1:
                try:
                    mat_fl = self.__mat_flows[row]
                    mat_fl.stats_mean_volume = convert.convert_formated_str_2_float(value)
                    db_main.the_session_handler.commit_session()
                    self.dataChanged.emit(index, index)
                    return True
                except ValueError:
                    return False #Тактично промолчим
            if column == 2:
                try:
                    mat_fl = self.__mat_flows[row]
                    mat_fl.stats_mean_timedelta = convert.convert_formated_str_2_float(value)
                    db_main.the_session_handler.commit_session()
                    self.dataChanged.emit(index, index)
                    return True
                except ValueError:
                    return False #Тактично промолчим
        return False

    def flags(self, index):
        if index.column() == 0:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        if index.column() == 1:
            #return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        if index.column() == 2:
            #return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def insertNewMatFl(self, new_mat_fl_entity, parent = QtCore.QModelIndex()):
        position = parent.row()-1
        self.beginInsertRows(parent, position, position)
        self.__mat_flows.insert(position, new_mat_fl_entity)
        self.endInsertRows()

    def changeExistingMatFl(self, an_index = QtCore.QModelIndex()):
        self.dataChanged.emit(an_index, an_index)

    def deleteRow(self, an_index):
        self.beginRemoveRows(an_index, an_index.row(),an_index.row())
        self.__mat_flows.pop(an_index.row())
        self.endRemoveRows()

class gui_client_sales_leads_model(QtCore.QAbstractTableModel):
    def __init__(self,  parent = None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._leads = []

    def update_table(self, client = None):
        self.beginResetModel()
        self._leads = client.sales_oppotunities
        self.endResetModel()

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                if section == 0:
                    return unicode(u"Материал")
                if section == 1:
                    return unicode(u"Ожидаемый объём (мес)")
                if section == 2:
                    return unicode(u"Ожидаемый старт продаж")

    def rowCount(self, parent):
        return len(self._leads)

    def columnCount(self, parent):
        return 3

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            if index.column() == 0:
                return unicode(self._leads[row].material_type.material_type_name)
            if index.column() == 1:
                lead_i = self._leads[row]
                mu = lead_i.material_type.measure_unit
                exp_vol = lead_i.expected_qtty * 30 / lead_i.expected_timedelta
                return unicode(simple_locale.number2string(exp_vol) + u" " + mu + u"/мес.")
            if index.column() == 2:
                lead_i = self._leads[row]
                d1_str = unicode(lead_i.expected_start_date_from.strftime("%x"))
                d2_str = unicode(lead_i.expected_start_date_till.strftime("%x"))
                return d1_str + u" - " + d2_str
        if role == 35: #Наша роль для передачи данных из таблицы
            row = index.row()
            if index.column() == 0:
                return self._leads[row].material_type
        if role == 45:  #роль для чтения "всей строки"
            row = index.row()
            return self._leads[row]

    def flags(self, index):
        if index.column() == 0:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        if index.column() == 1:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        if index.column() == 2:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def insertNew(self, new_lead_entity, parent = QtCore.QModelIndex()):
        # TODO: вот тут где-то сообщение неприятное вылазит
        position = parent.row()-1
        self.beginInsertRows(parent, position, position)
        self._leads.insert(position, new_lead_entity)
        self.endInsertRows()

    def changeExisting(self, an_index = QtCore.QModelIndex()):
        self.dataChanged.emit(an_index, an_index)

    def deleteRow(self, an_index):
        self.beginRemoveRows(an_index, an_index.row(),an_index.row())
        self._leads.pop(an_index.row())
        self.endRemoveRows()

class gui_client_prices_table_model(QtCore.QAbstractTableModel):
    #Каждая цена хитра - она может быть как на группу (material_type),
    #так и на номенклатуру непосредственно (material)
    def __init__(self,  parent = None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.__prices = []

    def update_prices_table(self, client = None):
        self.beginResetModel()
        self.__prices = []
        for pr_i in db_main.get_prices_list(client):
            self.__prices += [pr_i]
        self.endResetModel()

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                if section == 0:
                    return unicode(u"Материал")
                if section == 1:
                    return unicode(u"Отпускная цена")
                if section == 2:
                    return unicode(u"Валюта котировки")
                if section == 3:
                    return unicode(u"Условия платежа")

    def rowCount(self, parent):
        return len(self.__prices)

    def columnCount(self, parent):
        return 4

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            row = index.row()
            if index.column() == 0:
                if self.__prices[row].is_for_group:  #В эту категорию и None попадает - но его тут быть не должно
                    return self.__prices[row].material_type.material_type_name
                else:
                    return self.__prices[row].material.material_name
            if index.column() == 1:
                return unicode(simple_locale.number2string(self.__prices[row].price_value))
            if index.column() == 2:
                return unicode(self.__prices[row].payterm.ccy_quote.ccy_general_name)
            if index.column() == 3:
                return unicode(self.__prices[row].payterm.payterm_name)
        if role == 35: #Наша роль для передачи данных из таблицы
            row = index.row()
            if index.column() == 0:
                if self.__prices[row].is_for_group:
                    return self.__prices[row].material_type
                else:
                    return self.__prices[row].material
            if index.column() == 1:
                return self.__prices[row].price_value
            if index.column() == 2:
                return self.__prices[row].payterm.ccy_quote
            if index.column() == 3:
                return self.__prices[row].payterm
        if role == 45:  #роль для чтения "всей строки"
            row = index.row()
            return self.__prices[row]

    def setData(self, index, value, role = QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            row = index.row()
            column = index.column()
            if column == 1:
                #Чтобы цену можно было ручками править
                pr_i = self.__prices[row]
                try:
                    pr_i.price_value = convert.convert_formated_str_2_float(value)
                    db_main.the_session_handler.commit_session()
                    self.dataChanged.emit(index, index)
                    return True
                except ValueError:
                    return False
        return False

    def flags(self, index):
        if index.column() == 0:
            return QtCore.Qt.ItemIsEnabled
        if index.column() == 1:
            return QtCore.Qt.ItemIsEnabled
        if index.column() == 2:
            return QtCore.Qt.ItemIsEnabled
        if index.column() == 3:
            return QtCore.Qt.ItemIsEnabled

    def insertNewPrice(self, new_price_entity, parent = QtCore.QModelIndex()):
        #Вставляет в конец списка новую "пустую" цену
        position = parent.row()-1
        self.beginInsertRows(parent, position, position)
        self.__prices.insert(position, new_price_entity)
        self.endInsertRows()

    def changeExistingPrice(self, an_index = QtCore.QModelIndex()):
        self.dataChanged.emit(an_index, an_index)

    def deleteRow(self, an_index):
        self.beginRemoveRows(an_index, an_index.row(),an_index.row())
        self.__prices.pop(an_index.row())
        self.endRemoveRows()

class gui_supplier_prices_table_model(QtCore.QAbstractTableModel):
    #TODO: дублирование кода - можно сделать абстрактную табличку цен
    #Каждая цена хитра - она может быть как на группу (material_type),
    #так и на номенклатуру непосредственно (material)
    def __init__(self,  parent = None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.__prices = []

    def update_prices_table(self, supplier = None):
        self.beginResetModel()
        self.__prices = []
        for pr_i in db_main.get_prices_list(supplier):
            self.__prices += [pr_i]
        self.endResetModel()

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                if section == 0:
                    return unicode(u"Материал")
                if section == 1:
                    return unicode(u"Прайс поставщика")
                if section == 2:
                    return unicode(u"Валюта котировки")
                if section == 3:
                    return unicode(u"Условия платежа")

    def rowCount(self, parent):
        return len(self.__prices)

    def columnCount(self, parent):
        return 4

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            row = index.row()
            if index.column() == 0:
                if self.__prices[row].is_for_group:  #В эту категорию и None попадает - но его тут быть не должно
                    return self.__prices[row].material_type.material_type_name
                else:
                    return self.__prices[row].material.material_name
            if index.column() == 1:
                return unicode(simple_locale.number2string(self.__prices[row].price_value))
            if index.column() == 2:
                return unicode(self.__prices[row].payterm.ccy_quote.ccy_general_name)
            if index.column() == 3:
                return unicode(self.__prices[row].payterm.payterm_name)
        if role == 35: #Наша роль для передачи данных из таблицы
            row = index.row()
            if index.column() == 0:
                if self.__prices[row].is_for_group:
                    return self.__prices[row].material_type
                else:
                    return self.__prices[row].material
            if index.column() == 1:
                return self.__prices[row].price_value
            if index.column() == 2:
                return self.__prices[row].payterm.ccy_quote
            if index.column() == 3:
                return self.__prices[row].payterm
        if role == 45:  #роль для чтения "всей строки"
            row = index.row()
            return self.__prices[row]

    def setData(self, index, value, role = QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            row = index.row()
            column = index.column()
            if column == 1:
                #Чтобы цену можно было ручками править
                pr_i = self.__prices[row]
                try:
                    pr_i.price_value = convert.convert_formated_str_2_float(value)
                    db_main.the_session_handler.commit_session()
                    self.dataChanged.emit(index, index)
                    return True
                except ValueError:
                    return False
        return False

    def flags(self, index):
        if index.column() == 0:
            return QtCore.Qt.ItemIsEnabled
        if index.column() == 1:
            return QtCore.Qt.ItemIsEnabled
        if index.column() == 2:
            return QtCore.Qt.ItemIsEnabled
        if index.column() == 3:
            return QtCore.Qt.ItemIsEnabled

    def insertNewPrice(self, new_price_entity, parent = QtCore.QModelIndex()):
        #Вставляет в конец списка новую "пустую" цену
        position = parent.row()-1
        self.beginInsertRows(parent, position, position)
        self.__prices.insert(position, new_price_entity)
        self.endInsertRows()

    def changeExistingPrice(self, an_index = QtCore.QModelIndex()):
        self.dataChanged.emit(an_index, an_index)

    def deleteRow(self, an_index):
        self.beginRemoveRows(an_index, an_index.row(),an_index.row())
        self.__prices.pop(an_index.row())
        self.endRemoveRows()

class gui_payment_terms_list_model(QtCore.QAbstractListModel):
    def __init__(self,  parent = None):
        QtCore.QAbstractListModel.__init__(self, parent)
        self.__payment_terms = []
        self.update_list()

    def update_list(self):
        self.beginResetModel()
        self.__payment_terms = []
        for pay_term_i in db_main.get_payment_terms():
            self.__payment_terms += [pay_term_i]
        self.endResetModel()

    def rowCount(self, parent):
        return len(self.__payment_terms)

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            return unicode(self.__payment_terms[index.row()].payterm_name)
        if role == 35: #Наша роль для передачи данных
            return self.__payment_terms[index.row()]
        if role == 40: #Роль для поиска элемента в списке (возвращает ключ элемента)
            return self.__payment_terms[index.row()].string_key()

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

class gui_general_material_list_model(QtCore.QAbstractListModel):
    #Может быть группой, может быть номенклатурой
    def __init__(self, type = 0, parent = None, do_load = 1):
        QtCore.QAbstractListModel.__init__(self, parent)
        self._general_materials = []
        self._list_type = type #0 - material, 1 - material_type
        if do_load:
            self.update_list()

    def switch_to_materials(self):
        self._list_type = 0
        self.update_list()

    def switch_to_material_types(self):
        self._list_type = 1
        self.update_list()

    def check_type(self):
        if self._list_type == 0:
            return "materials"
        elif self._list_type == 1:
            return "groups"

    def update_list(self):
        self.beginResetModel()
        self._general_materials = []
        if self._list_type == 0:
            for mat_i in db_main.get_materials_list():
                self._general_materials += [mat_i]
        elif self._list_type == 1:
            for mt_i in db_main.get_material_types_list():
                self._general_materials += [mt_i]
        self.endResetModel()

    def rowCount(self, parent):
        return len(self._general_materials)

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            if self._list_type == 0:
                return unicode(self._general_materials[index.row()].material_name)
            elif self._list_type == 1:
                return unicode(self._general_materials[index.row()].material_type_name)
        if role == 35: #Наша роль для передачи данных
            return self._general_materials[index.row()]
        if role == 40: #Роль для поиска элемента в списке (возвращает ключ элемента)
            return self._general_materials[index.row()].string_key()

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

class gui_materials_list_model(QtCore.QAbstractListModel):
    def __init__(self,  parent = None, parent_material_type = None, do_update = 1):
        QtCore.QAbstractListModel.__init__(self, parent)
        self.__materials = []
        self.parent_material_type = parent_material_type
        if do_update:
            self.update_list()

    def set_parent_material_type(self, parent_material_type):
        self.parent_material_type = parent_material_type

    def update_list(self):
        self.beginResetModel()
        self.__materials = []
        if self.parent_material_type is None:
            for mat_i in db_main.get_materials_list():
                self.__materials += [mat_i]
        else:
            self.__materials = self.parent_material_type.materials
        self.endResetModel()

    def rowCount(self, parent):
        return len(self.__materials)

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            return unicode(self.__materials[index.row()].material_name)
        if role == 35: #Наша роль для передачи данных
            return self.__materials[index.row()]
        if role == 40: #Роль для поиска элемента в списке (возвращает ключ элемента)
            return self.__materials[index.row()].string_key()

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

class gui_mat_type_list_model(QtCore.QAbstractListModel):
    def __init__(self,  parent = None):
        QtCore.QAbstractListModel.__init__(self, parent)
        self.__mat_types = []
        self.update_list()

    def update_list(self):
        self.beginResetModel()
        self.__mat_types = []
        for mt_i in db_main.get_material_types_list():
            self.__mat_types += [mt_i]
        self.endResetModel()

    def rowCount(self, parent):
        return len(self.__mat_types)

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            return unicode(self.__mat_types[index.row()].material_type_name)
        if role == 35: #Наша роль для передачи данных
            return self.__mat_types[index.row()]
        if role == 40: #Роль для поиска элемента в списке (возвращает ключ элемента)
            return self.__mat_types[index.row()].string_key()

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

class gui_ccy_list_model(QtCore.QAbstractListModel):
    def __init__(self,  parent = None):
        QtCore.QAbstractListModel.__init__(self, parent)
        self.__ccy = []
        self.update_list()

    def update_list(self):
        self.beginResetModel()
        self.__ccy = []
        for ccy_i in db_main.get_ccy_list():
            self.__ccy += [ccy_i]
        self.endResetModel()

    def rowCount(self, parent):
        return len(self.__ccy)

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            return unicode(self.__ccy[index.row()].ccy_general_name)
        if role == 35: #Наша роль для передачи данных
            return self.__ccy[index.row()]
        if role == 40: #Роль для поиска элемента в списке (возвращает ключ элемента)
            return self.__ccy[index.row()].string_key()

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

class gui_matflow_matdist_model(QtCore.QAbstractTableModel):
    def __init__(self,  parent = None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.__probs = []
        self.prob_dict = utils.c_random_dict()

    def update_matdist_table(self, prob_dict):
        self.beginResetModel()
        self.__probs = []  #TODO ordered dict!
        self.prob_dict = prob_dict
        for material, prob in self.prob_dict.randomdict.iteritems():
            self.__probs += [[material, prob]]
        self.endResetModel()

    def reset_all(self):  #При создании нового, когда меняем группу - перезагрузка
        self.beginResetModel()
        self.__probs = []
        self.prob_dict.reset_me()
        self.endResetModel()

    def normalize_probs(self):
        self.prob_dict.finalize()
        self.update_matdist_table(self.prob_dict)

    def is_data_correct(self):
        #Это проверяется только при закрытии формы. Всё, в общем-то, runtime проверяется..
        return True

    def get_prob_dict(self):
        return self.prob_dict

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                if section == 0:
                    return unicode(u"Товар")
                if section == 1:
                    return unicode(u"Вероятность закупки")

    def rowCount(self, parent):
        return len(self.__probs)

    def columnCount(self, parent):
        return 2

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            if index.column() == 0:
                return unicode(self.__probs[row][0])
            if index.column() == 1:
                return unicode(simple_locale.number2string(round(self.__probs[row][1],2)))  #Проценты?
        if role == 35: #Наша роль для передачи данных из таблицы
            row = index.row()
            if index.column() == 0:
                return self.__probs[row][0]
            if index.column() == 1:
                return self.__probs[row][1]
        if role == 45:  #роль для чтения "всей строки"
            row = index.row()
            return self.__probs[row]

    def setData(self, index, value, role = QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            row = index.row()
            column = index.column()
            if column == 0:
                old_mat, old_prob = self.__probs.pop(row)
                #self.__probs[row][0] = value
                #self.__probs.pop(row)
                self.__probs.insert(row,[value, old_prob])
                self.prob_dict.delete_elem(old_mat)
                self.prob_dict.add_elem(value, old_prob)
                self.dataChanged.emit(index, index)
                return True
            if column == 1:  # Вероятность выбора
                try:
                    prob = float(convert.convert_formated_str_2_float(value))
                    self.__probs[row][1] = prob
                    self.prob_dict.randomdict[self.__probs[row][0]] = prob
                    self.dataChanged.emit(index, index)
                    return True
                except ValueError:
                    return False #Тактично промолчим
        return False

    def flags(self, index):
        if index.column() == 0:
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        if index.column() == 1:
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def insertNewMaterial(self, material, parent = QtCore.QModelIndex()):
        position = parent.row()-1
        self.beginInsertRows(parent, position, position)
        self.__probs.insert(position, [material, 0])
        self.prob_dict.add_elem(material, 0)
        self.endInsertRows()

    def changeExistingMatDist(self, an_index = QtCore.QModelIndex()):
        self.dataChanged.emit(an_index, an_index)

    def insertBlankLine(self, parent = QtCore.QModelIndex()):
        position = parent.row()-1
        self.beginInsertRows(parent, position, position)
        self.__probs.insert(position, ["", 0])
        self.prob_dict.add_elem("", 0)
        self.endInsertRows()

    def deleteRecord(self, an_index):
        self.beginRemoveRows(an_index, an_index.row(),an_index.row())
        material, prob = self.__probs.pop(an_index.row())
        self.prob_dict.randomdict.pop(material)
        self.endRemoveRows()

class gui_knbase_model(QtCore.QAbstractListModel):
    def __init__(self,  parent = None):
        QtCore.QAbstractListModel.__init__(self, parent)
        self.__records = []
        self.__filtered_records = []
        self.update_list()
        self.deep_filter_mode = False

    def update_list(self):
        self.beginResetModel()
        self.__records = []
        for rec_i in db_main.get_records_list():
            self.__records.append(rec_i)
        self.endResetModel()

    def rowCount(self, parent):
        if self.deep_filter_mode:
            return len(self.__filtered_records)
        else:
            return len(self.__records)

    def data(self, index, role):
        if self.deep_filter_mode:
                rec = self.__filtered_records[index.row()]
        else:
            rec = self.__records[index.row()]

        if role == QtCore.Qt.DisplayRole:
            d_str = rec.date_added.strftime("%d %b %Y")
            h_str = ""
            h_str = rec.hashtags_string
            s = u"[%s] %s \n %s"%(d_str, h_str, rec.headline)
            return unicode(s)
        # if role == QtCore.Qt.DecorationRole:
        #     how_old = abs((rec.date_added - datetime.datetime.today()).days)
        #     if how_old <= 3:
        #         return QtGui.QColor("cyan")
        #     elif how_old <= 10:
        #         return QtGui.QColor("green")
        #     elif how_old <= 30:
        #         return QtGui.QColor("darkCyan")
        #     else:
        #         return QtGui.QColor("darkGray")
        if role == 35: #Наша роль для передачи данных
            return rec

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def deleteRow(self, an_index):
        self.beginRemoveRows(an_index, an_index.row(),an_index.row())
        rec_i = self.__records.pop(an_index.row())
        self.endRemoveRows()

    def set_deep_filter_on_records(self, searched_text):
        self.beginResetModel()
        self.deep_filter_mode = True
        self.__filtered_records = []
        for rec_i in db_main.get_records_iter_deep_search(searched_text):
            self.__filtered_records += [rec_i]
        self.endResetModel()

    def turn_off_deep_filter(self):
        self.deep_filter_mode = False

class gui_knbase_hashtag_model(QtCore.QAbstractListModel):
    def __init__(self,  parent = None):
        QtCore.QAbstractListModel.__init__(self, parent)
        self.__hashtags = []
        self.update_list()

    def update_list(self):
        self.beginResetModel()
        self.__hashtags = []
        for ht_i in db_main.get_hashtags_list_iter():
            self.__hashtags += [ht_i]
        self.endResetModel()

    def rowCount(self, parent):
        return len(self.__hashtags)

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            ht_i = self.__hashtags[index.row()]
            return unicode(u"#" + ht_i.text)
        # elif role == QtCore.Qt.DecorationRole:
        #     ht_i = self.__hashtags[index.row()]
        #     how_freq = len(ht_i.records)
        #     if how_freq >= 200:
        #         return QtGui.QColor(0,255,255)
        #     elif how_freq >= 100:
        #         return QtGui.QColor(0,230,230)
        #     elif how_freq >= 80:
        #         return QtGui.QColor(0,210,210)
        #     elif how_freq >= 50:
        #         return QtGui.QColor(0,190,190)
        #     elif how_freq >= 30:
        #         return QtGui.QColor(0,170,170)
        #     elif how_freq >= 10:
        #         return QtGui.QColor(0,150,150)
        #     elif how_freq >= 5:
        #         return QtGui.QColor(0,120,120)
        #     else:
        #         return QtGui.QColor(255,255,255)
        elif role == 35: #Наша роль для передачи данных
            return self.__hashtags[index.row()]

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

class gui_contacts_model(QtCore.QAbstractListModel):
    def __init__(self,  parent = None):
        QtCore.QAbstractListModel.__init__(self, parent)
        self.__contacts = []
        self.update_list()

    def update_list(self):
        self.beginResetModel()
        self.__contacts = []
        for cnt_i in db_main.get_contacts_list_iter():
            self.__contacts += [cnt_i]
        self.endResetModel()

    def rowCount(self, parent):
        return len(self.__contacts)

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            cnt_i = self.__contacts[index.row()]
            return unicode(cnt_i.name + u" @ " + cnt_i.company.name)
        if role == 35: #Наша роль для передачи данных
            return self.__contacts[index.row()]

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

class gui_contacts_details_model(QtCore.QAbstractTableModel):
    def __init__(self,  parent = None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.__details = []

    def update_data(self,  details_list):
        self.beginResetModel()
        self.__details = []
        for d_i in details_list:
            self.__details += [[unicode(d_i.cont_type), unicode(d_i.cont_value), d_i.is_type_fixed, d_i.rec_id]]
        self.endResetModel()

    def get_all_data(self):
        return self.__details

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                if section == 0:
                    return unicode(u"Тип")
                if section == 1:
                    return unicode(u"Значение")

    def rowCount(self, parent):
        return len(self.__details)

    def columnCount(self, parent):
        return 2

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            row = index.row()
            if index.column() == 0:
                return self.__details[row][0]
            if index.column() == 1:
                return self.__details[row][1]
        if role == 35: #Наша роль для передачи данных из таблицы
            row = index.row()
            if index.column() == 0:
                return self.__details[row][0]
            if index.column() == 1:
                return self.__details[row][1]
            if index.column() == 2:
                return self.__details[row][2]
            if index.column() == 3:
                return self.__details[row][3]
        if role == 45:  #роль для чтения "всей строки"
            row = index.row()
            return self.__details[row]

    def setData(self, index, value, role = QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            row = index.row()
            column = index.column()
            if column == 0:
                if not(self.__details[row][2]):  #Если можно править
                    self.__details[row][0] = unicode(unicode_codec.fromUnicode(value.toString()))
                    self.dataChanged.emit(index, index)
                    return True
            if column == 1:
                self.__details[row][1] = unicode(unicode_codec.fromUnicode(value.toString()))
                self.dataChanged.emit(index, index)
                return True
        return False

    def flags(self, index):
        if index.column() == 0:
            if not(self.__details[index.row()][2]):  #Если можно править
                return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
            else:
                return QtCore.Qt.ItemIsEnabled
        if index.column() == 1:
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def insertNewDetail(self, cont_type, cont_value, is_fixed, parent = QtCore.QModelIndex()):
        #Вставляет в конец списка новую "пустую" цену
        position = parent.row()-1
        self.beginInsertRows(parent, position, position)
        self.__details += [[unicode(cont_type), unicode(cont_value), is_fixed, None]]
        self.endInsertRows()

    def changeExistingDetail(self, an_index = QtCore.QModelIndex()):
        self.dataChanged.emit(an_index, an_index)  #Вызывается вообще?..

    def deleteRow(self, an_index):
        self.beginRemoveRows(an_index, an_index.row(),an_index.row())
        self.__details.pop(an_index.row())
        self.endRemoveRows()

class gui_mainsim_varlist_model(QtCore.QAbstractListModel):
    def __init__(self,  parent = None):
        QtCore.QAbstractListModel.__init__(self, parent)
        self.my_list = []
        self.update_with_observations()

    def update_with_observations(self):
        self.beginResetModel()
        self.my_list = []
        for nam, rep_i in iter_dataframe_reports():
            self.my_list += [[nam, rep_i]]
        self.endResetModel()

    def rowCount(self, parent):
        return len(self.my_list)

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            return self.my_list[index.row()][0]
        if role == 35:
            return self.my_list[index.row()][1]

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

class gui_testsim_varlist_model(QtCore.QAbstractListModel):
    def __init__(self,  parent = None):
        QtCore.QAbstractListModel.__init__(self, parent)
        self.my_list = []

    def update_with_observations(self, sim_results):
        self.beginResetModel()
        self.my_list = []
        for [obs_name, var_name] in sim_results.get_available_names():
            # Как-то жестоко..
            self.my_list += [[obs_name + " : " + var_name, sim_results.get_dataframe_for_epochvar(obs_name, var_name)]]
        self.endResetModel()

    def rowCount(self, parent):
        return len(self.my_list)

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            return self.my_list[index.row()][0]
        if role == 35:
            return self.my_list[index.row()]

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

class gui_testsimlog_table_model(QtCore.QAbstractTableModel):
    def __init__(self,  parent = None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.logs = []

    def update_logs(self, start_date, log_list):
        self.beginResetModel()
        self.logs = []
        for item_i in log_list:
            real_timestamp = start_date + datetime.timedelta(days = item_i[0])
            sender_name = item_i[1]
            sender_message = item_i[2]
            log_i = [real_timestamp, sender_name, sender_message]
            self.logs += [log_i]
        self.endResetModel()

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                if section == 0:
                    return unicode(u"Дата")
                if section == 1:
                    return unicode(u"Элемент системы")
                if section == 2:
                    return unicode(u"Сообщение")

    def rowCount(self, parent):
        return len(self.logs)

    def columnCount(self, parent):
        return 3

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            if index.column() == 0:
                return unicode(self.logs[row][0].strftime("%W нед %y г" ))
            if index.column() == 1:
                return unicode(self.logs[row][1])
            if index.column() == 2:
                return unicode(self.logs[row][2])

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

class gui_agent_type_list_model(QtCore.QAbstractListModel):
    def __init__(self,  parent = None):
        QtCore.QAbstractListModel.__init__(self, parent)
        self.my_list = []
        self.update_list()

    def update_list(self):
        self.beginResetModel()
        self.my_list = []
        self.my_list += [[u"Клиент", db_main.c_client_model, 'agent']]
        self.my_list += [[u"Поставщик", db_main.c_supplier_model, 'supplier']]
        self.my_list += [[u"Прочие", db_main.c_agent, 'agent']]
        self.endResetModel()

    def rowCount(self, parent):
        return len(self.my_list)

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            return self.my_list[index.row()][0]
        if role == 35:
            return self.my_list[index.row()][1]
        if role == 40:
            return self.my_list[index.row()][2]

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

class gui_counterparty_list_model(QtCore.QAbstractListModel):
    def __init__(self,  parent = None, agent_discriminator='', materialgr_for_sorting=None, do_load=0):
        # agent_discriminator - дискриминатор агента. Если '', то все агенты
        # materialgr_for_sorting - сортировать по отношению к группе материалов
        QtCore.QAbstractListModel.__init__(self, parent)
        self._cps = []
        self.agent_discriminator = agent_discriminator
        self.materialgr_for_sorting = materialgr_for_sorting
        self.is_loaded = 0
        if do_load:
            self.update_list()

    def set_matgr_for_sorting(self, materialgr_for_sorting=None):
        self.materialgr_for_sorting = materialgr_for_sorting
        if self.materialgr_for_sorting is not None:
            # Do nothing otherwise
            if not(self.is_loaded):
                self.update_list()
            self.beginResetModel()
            self._apply_matgr_sorting()
            self.endResetModel()

    def update_list(self):
        self.beginResetModel()
        self._cps = []
        if self.agent_discriminator == '':
            for cp_i in db_main.get_agent_list():
                self._cps += [cp_i]
        if self.agent_discriminator == 'client':
            for cp_i in db_main.get_client_list():
                self._cps += [cp_i]
            if self.materialgr_for_sorting is not None:
                self._apply_matgr_sorting()
        if self.agent_discriminator == 'supplier':
            for cp_i in db_main.get_supplier_list():
                self._cps += [cp_i]
        self.endResetModel()
        self.is_loaded = 1

    def _apply_matgr_sorting(self):
        # Сортируем клиентов по объёму потребления группы товаров + лиды.
        decorated_list = []
        mat_gr = self.materialgr_for_sorting
        for i, cp_i in enumerate(self._cps):
            if cp_i.discriminator == 'client':
                cons = 0
                for matfl_i in cp_i.material_flows:
                    if matfl_i.material_type == mat_gr:
                        cons += matfl_i.stats_mean_volume
                for lead_i in cp_i.sales_oppotunities:
                    if lead_i.material_type == mat_gr:
                        cons += matfl_i.expected_qtty
                decorated_list += [(cons, i, cp_i)]
            else: # Такого пока не должно происходить
                decorated_list += [(0, i, cp_i)]
        decorated_list.sort(reverse=1)
        self._cps = [cp_i for cons, i, cp_i in decorated_list]

    def rowCount(self, parent):
        return len(self._cps)

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            return unicode(self._cps[index.row()].name)
        if role == 35: #Наша роль для передачи данных
            return self._cps[index.row()]
        if role == 40: #Роль для поиска элемента в списке (возвращает ключ элемента)
            return self._cps[index.row()].string_key()

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable