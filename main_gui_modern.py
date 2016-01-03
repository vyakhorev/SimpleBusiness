# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
import simple_locale

from ui.ui_ModernMainWindow_v2 import Ui_MainWindowModern

# dialogs
from gui_forms_logic.dlgs.dlg_edit_contact import gui_DialogCrm_EditContact
from gui_forms_logic.dlgs.dlg_edit_price import gui_Dialog_EditPrice
from gui_forms_logic.dlgs.dlg_edit_matflow import gui_Dialog_EditMatFlow
from gui_forms_logic.dlgs.dlg_sales_opportunity import gui_Dialog_EditSalesOpportunity
from gui_forms_logic.dlgs.dlg_edit_kn_base_record import gui_DialogCrm_EditSimpleRecord

# Import custom gui logic
from gui_forms_logic.data_models import cDataModel_CounterpartyList
from gui_forms_logic.record_mediators import cMedPrice, cMedMatFlow, cMedContact,\
        cMedKnBaseRecord, cMedSalesLead, cSimpleMediator
from gui_forms_logic.frame_builder import LabelFrame, RecFrame


import db_main
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

    sig_cp_record_added = QtCore.pyqtSignal(str)
    sig_cp_record_deleted = QtCore.pyqtSignal(str)
    sig_cp_record_edited = QtCore.pyqtSignal(str)

    sig_knbase_record_added = QtCore.pyqtSignal(str)
    sig_knbase_record_deleted = QtCore.pyqtSignal(str)
    sig_knbase_record_edited = QtCore.pyqtSignal(str)

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

        # Dialog names (use methods to get them!
        self._DlgEditContact = None
        self._DlgEditSimpleRecord = None
        self._DlgEditCPdata = None
        self._DlgEditSalesOpportunity = None
        self._DlgEditPrice = None
        self._DlgEditMatFlow = None

        # Connect signals that would be raised by widget logics
        self.sig_cp_record_added.connect(self.handle_cp_new_record)
        self.sig_cp_record_deleted.connect(self.handle_cp_delete_record)
        self.sig_cp_record_edited.connect(self.handle_cp_edit_record)

        ############
        # Knowledge base tab
        ############

        # Setup knbase scroll
        self.mediators_frame_list_KnBase = []

        self.scrollArea_KnBaseRecords.setWidgetResizable(True)
        self.scrollArea_KnBaseRecords.setFocusPolicy(QtCore.Qt.NoFocus)
        self.scrollArea_KnBaseRecords.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scr_bar_KnBaseRecords = QtGui.QScrollBar()
        self.scrollArea_KnBaseRecords.setVerticalScrollBar(self.scr_bar_KnBaseRecords)

        self.mediators_list_layout_KnBase = QtGui.QVBoxLayout()
        self.base_widget_KnBase = QtGui.QWidget()
        self.base_widget_KnBase.setLayout(self.mediators_list_layout_KnBase)
        self.scrollArea_KnBaseRecords.setWidget(self.base_widget_KnBase)

        self.scr_bar_KnBaseRecords.valueChanged.connect(self.scrolled_KnBase)

        # Setup signals
        self.pushButton_KnBaseEmptyNote.clicked.connect(self.dlg_add_knbase_record)

        # Connect signals that would be raised by widget logics
        self.sig_knbase_record_added.connect(self.handle_knbase_new_record)
        self.sig_knbase_record_deleted.connect(self.handle_knbase_delete_record)
        self.sig_knbase_record_edited.connect(self.handle_knbase_edit_record)

    #################
    # Вкладка с контрагентами
    #################

    def click_on_CP(self, index_to, index_from):
        cp_i = index_to.data(35).toPyObject()
        if cp_i is None:
            return
        for med_i in self._iter_cp_mediator(cp_i):
            # Идём по очереди по представителям данных
            self.make_frame_from_mediator(med_i)

    def _iter_cp_mediator(self, cp):
        '''
        Передаем сюда любого контрагента, получаем в ответ список связанных записей (медиаторов).
        Их можно потом построить при помощи Frame. Фактически, тут к записи привязываются вызовы
        и поля, которые можно потом аккуратно вывести и на gui автоматом.
        Args:
            cp: Контрагент
        Returns: лист медиаторов разного рода для записей, связанных с контрагентом
        '''

        # Контакты
        header = cSimpleMediator(self)
        header.set_key('Contacts')
        header.set_label(u'Контакты')
        header.add_call('dlg_add_crm_contact', u'+Добавить', cp)
        yield header
        for cnt_i in db_main.get_contacts_list(cp):
            new_med = cMedContact(self, cnt_i)
            new_med.add_call('dlg_edit_crm_contact', u'Изменить', cnt_i)
            new_med.add_call('dlg_delete_crm_contact', u'Удалить', cnt_i)
            yield new_med

        # Цены (как покупателю, так и от поставщика)
        header = cSimpleMediator(self)
        header.set_key('Prices')
        header.set_label(u'Цены')
        header.add_call('dlg_add_price', u'+Добавить', cp)
        yield header
        for pr_i in db_main.get_prices_list(cp):
            new_med = cMedPrice(self, pr_i)
            new_med.add_call('dlg_edit_price', u'Изменить', pr_i)
            new_med.add_call('dlg_delete_price', u'Удалить', pr_i)
            yield new_med

        # Список линий снабжения и лиды
        if cp.discriminator == 'client':
            header = cSimpleMediator(self)
            header.set_key('MatFlows')
            header.set_label(u'Потоки снабжения')
            header.add_call('dlg_add_matflow', u'+Добавить', cp)
            yield header
            for mf_i in db_main.get_mat_flows_list(cp):
                new_med = cMedMatFlow(self, mf_i)
                new_med.add_call('dlg_edit_matflow', u'Изменить', mf_i)
                new_med.add_call('dlg_delete_matflow', u'Удалить', mf_i)
                yield new_med

            header = cSimpleMediator(self)
            header.set_key('SalesLeads')
            header.set_label(u'Лиды')
            header.add_call('dlg_add_lead', u'+Добавить', cp)
            yield header
            for lead_i in cp.sales_oppotunities:
                new_med = cMedSalesLead(self, lead_i)
                new_med.add_call('dlg_edit_lead', u'Изменить', lead_i)
                new_med.add_call('dlg_delete_lead', u'Удалить', lead_i)
                yield new_med

    def make_frame_from_mediator(self, mediator):
        """
            Automatically building gui for each mediator
        :param mediator: incoming mediator class instance
        :return: None
        """
        #self.scroll_area.

        # У каждого mediator есть метод get_key() - возвращает ключ, уникальный для группы.
        # (при желании, можно сделать уникальный глобально). Этот же ключ передаётся в
        # handle_cp_new_record, handle_cp_delete_record, handle_cp_edit_record
        # В этих 3х методах можно сделать обновление виджета в ScrollArea

        if mediator.label != '':
            new_frame = LabelFrame(mediator, self)
        else:
            new_frame = RecFrame(mediator, self)

        self.mediators_frame_list.append(new_frame)
        self.mediators_list_layout.addWidget(new_frame)

    @QtCore.pyqtSlot(str)
    def handle_cp_new_record(self, rec_key):
        print("new record handler triggered " + str(rec_key))

    @QtCore.pyqtSlot(str)
    def handle_cp_delete_record(self, rec_key):
        print("delete record handler triggered " + str(rec_key))

    @QtCore.pyqtSlot(str)
    def handle_cp_edit_record(self, rec_key):
        print("edit record handler triggered " + str(rec_key))

    #################
    # Вкладка с заметками
    #################

    @QtCore.pyqtSlot(str)
    def handle_knbase_new_record(self, rec_key):
        print("new record handler triggered " + str(rec_key))

    @QtCore.pyqtSlot(str)
    def handle_knbase_delete_record(self, rec_key):
        print("delete record handler triggered " + str(rec_key))

    @QtCore.pyqtSlot(str)
    def handle_knbase_edit_record(self, rec_key):
        print("edit record handler triggered " + str(rec_key))


    def print_to_area(self, records_iterator):
        """
        Args:
            records_iterator: Some iterator over records (should do query with every next() call)
        """
        for rec_i in records_iterator:
            new_mediator = cMedKnBaseRecord(self, rec_i)
            new_mediator.add_call('dlg_edit_knbase_record', u'Изменить', rec_i)
            new_mediator.add_call('dlg_delete_knbase_record', u'Удалить', rec_i)

            new_frame = RecFrame(new_mediator, self)
            self.mediators_frame_list_KnBase.append(new_frame)
            self.mediators_list_layout_KnBase.append(new_frame)

    def scrolled_KnBase(self):
        print("scrooled!")

    ###################
    # Управление диалоговыми окнами
    ###################

    # LAZY открытие

    def get_DlgEditSimpleRecord(self):
        if self._DlgEditSimpleRecord is None:
            self._DlgEditSimpleRecord = gui_DialogCrm_EditSimpleRecord(self)
        return self._DlgEditSimpleRecord

    def get_DlgEditContact(self):
        if self._DlgEditContact is None:
            self._DlgEditContact = gui_DialogCrm_EditContact(self)
        return self._DlgEditContact

    # def get_DlgEditCPdata(self):
    #     if self._DlgEditCPdata is None:
    #         self._DlgEditCPdata = gui_DialogCrm_EditCounterpartyData(self)
    #     return self._DlgEditCPdata

    def get_DlgEditSalesOpportunity(self):
        if self._DlgEditSalesOpportunity is None:
            self._DlgEditSalesOpportunity = gui_Dialog_EditSalesOpportunity(self)
        return self._DlgEditSalesOpportunity

    def get_DlgEditPrice(self):
        if self._DlgEditPrice  is None:
            self._DlgEditPrice = gui_Dialog_EditPrice(self)
        return self._DlgEditPrice

    def get_DlgEditMatFlow(self):
        if self._DlgEditMatFlow  is None:
            self._DlgEditMatFlow = gui_Dialog_EditMatFlow(self)
        return self._DlgEditMatFlow

    # КОНТАКТЫ

    def dlg_add_crm_contact(self, agent):
        if agent is None:
            raise BaseException("No agent selected!")
        edit_dialog = self.get_DlgEditContact()
        edit_dialog.set_state_to_add_new(agent)
        is_ok, a_contact = edit_dialog.run_dialog()
        if is_ok == 1:
            db_main.the_session_handler.add_object_to_session(a_contact)
            db_main.the_session_handler.commit_session()
            self.sig_cp_record_added.emit(a_contact.string_key())

    def dlg_edit_crm_contact(self, selected_contact):
        if selected_contact is None:
            raise BaseException("No contact selected!")
        edit_dialog = self.get_DlgEditContact()
        edit_dialog.set_state_to_edit(selected_contact)
        is_ok, a_contact = edit_dialog.run_dialog()
        if is_ok == 1: # a_contact = selected_contact
            db_main.the_session_handler.commit_session()
            self.sig_cp_record_edited.emit(a_contact.string_key())

    def dlg_delete_crm_contact(self, selected_contact):
        if selected_contact is None:
            raise BaseException("No contact selected!")
        a_msg = unicode(u"Подтверждаете удаление: ") + unicode(selected_contact.name +
                                    " @ " + selected_contact.company.name) + unicode(u" ?")
        a_reply = QtGui.QMessageBox.question(self, unicode(u'Подтвердите'), a_msg,
                                             QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if a_reply == QtGui.QMessageBox.Yes:
            k = selected_contact.string_key()
            db_main.the_session_handler.delete_concrete_object(selected_contact)
            self.sig_cp_record_deleted.emit(k)

    # ЦЕНЫ

    def dlg_add_price(self, agent):
        if agent is None:
            raise BaseException("No agent selected!")
        edit_dialog = self.get_DlgEditPrice()
        edit_dialog.set_state_to_add_new(agent)
        is_ok, a_price = edit_dialog.run_dialog()
        if is_ok == 1:
            #Записали в базу данных
            db_main.the_session_handler.add_object_to_session(a_price)
            db_main.the_session_handler.commit_session()
            self.sig_cp_record_added.emit(a_price.string_key())

    def dlg_edit_price(self, price_instance):
        if price_instance is None:
            raise BaseException("No price selected!")
        edit_dialog = self.get_DlgEditPrice()
        edit_dialog.set_state_to_edit(price_instance)
        is_ok, a_price = edit_dialog.run_dialog()
        if is_ok == 1: # a_price = price_instance
            #Записали в базу данных
            db_main.the_session_handler.commit_session()
            #Не забыли обновить табличку
            self.sig_cp_record_edited.emit(a_price.string_key())

    def dlg_delete_price(self, price_instance):
        if price_instance is None:
            raise BaseException("No price selected!")
        a_msg = unicode(u"Подтверждаете удаление цены на ")
        if price_instance.is_for_group:
            a_msg +=  unicode(price_instance.material_type.material_type_name)
        else:
            a_msg +=  unicode(price_instance.material.material_name)
        a_msg += unicode(u" ?")
        a_reply = QtGui.QMessageBox.question(self, unicode(u'Подтвердите'), a_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if a_reply == QtGui.QMessageBox.Yes:
            k = price_instance.string_key()
            db_main.the_session_handler.delete_concrete_object(price_instance)
            self.sig_cp_record_deleted.emit(k)

    # ПОТОКИ СНАБЖЕНИЯ (MATFLOW)

    def dlg_add_matflow(self, agent):
        if agent is None:
            raise BaseException("No agent selected!")
        if agent.discriminator != "client":
            raise BaseException("Wrong agent type!")
        edit_dialog = self.get_DlgEditMatFlow()
        edit_dialog.set_state_to_add_new(agent)
        is_ok, a_mf = edit_dialog.run_dialog()
        if is_ok == 1:
            #Записали в базу данных
            db_main.the_session_handler.add_object_to_session(a_mf)
            db_main.the_session_handler.commit_session()
            self.sig_cp_record_added.emit(a_mf.string_key())
            # TODO: заметка! (уже сделано было раньше)

    def dlg_edit_matflow(self, matflow_instance):
        if matflow_instance is None:
            raise BaseException("No material flow selected!")
        old_volume = matflow_instance.stats_mean_volume
        old_freq = matflow_instance.stats_mean_timedelta
        edit_dialog = self.get_DlgEditMatFlow()
        edit_dialog.set_state_to_edit(matflow_instance)
        is_ok, a_mf  = edit_dialog.run_dialog()
        if is_ok == 1:  # a_mf = matflow_instance
            #Записали в базу данных
            db_main.the_session_handler.commit_session()
            #Не забыли обновить табличку
            self.sig_cp_record_edited.emit(a_mf.string_key())
            # TODO: заметка! (уже сделано было раньше)

    def dlg_delete_matflow(self, matflow_instance):
        if matflow_instance is None:
            raise BaseException("No material flow selected!")
        a_msg = unicode(u"Подтверждаете удаление потока снабжения по ")
        a_msg += unicode(matflow_instance.material_type.material_type_name)
        a_msg += unicode(u" ?")
        a_reply = QtGui.QMessageBox.question(self, unicode(u'Подтвердите'), a_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if a_reply == QtGui.QMessageBox.Yes:
            k = matflow_instance.string_key()
            db_main.the_session_handler.delete_concrete_object(matflow_instance)
            self.sig_cp_record_deleted.emit(k)
            #TODO: заметка!

    # ЛИДЫ (OPPORTUNITY)

    def dlg_add_lead(self, agent):
        if agent is None:
            raise BaseException("No agent selected!")
        if agent.discriminator != "client":
            raise BaseException("Wrong agent type!")
        edit_dialog = self.get_DlgEditSalesOpportunity()
        edit_dialog.set_state_to_add_new(agent) #Тут должно быть сбрасывание полей
        is_ok, new_lead = edit_dialog.run_dialog()
        if is_ok == 1:
            #Записали в базу данных
            db_main.the_session_handler.add_object_to_session(new_lead)
            db_main.the_session_handler.commit_session()
            self.sig_cp_record_added.emit(new_lead.string_key())

    def dlg_edit_lead(self, a_lead):
        if a_lead is None:
            raise BaseException("No sales opportunity selected!")
        old_lead = a_lead.get_dummy_copy()
        edit_dialog = self.get_DlgEditSalesOpportunity()
        edit_dialog.set_state_to_edit(a_lead)
        is_ok, new_lead = edit_dialog.run_dialog() #new_lead = a_lead
        if is_ok == 1:
            #Записали в базу данных
            db_main.the_session_handler.commit_session()
            #Не забыли обновить табличку
            self.sig_cp_record_edited.emit(a_lead.string_key())

    def dlg_delete_lead(self, a_lead):
        if sales_opportunity is None:
            raise BaseException("No sales opportunity selected!")
        a_msg = unicode(u"Подтверждаете забвение возможности по товару %s? Или, может, сроки перенесете?") %(unicode(a_lead.material_type.material_type_name))
        a_reply = QtGui.QMessageBox.question(self, unicode(u'Подтвердите'), a_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if a_reply == QtGui.QMessageBox.Yes:
            k = a_lead.string_key()
            db_main.the_session_handler.delete_concrete_object(a_lead)
            self.sig_cp_record_deleted.emit(k)

    # ЗАМЕТКИ В БАЗЕ ЗНАНИЙ

    def dlg_add_knbase_record(self):
        edit_dialog = self.get_DlgEditSimpleRecord()
        edit_dialog.set_state_to_add_new()
        is_ok, new_rec = edit_dialog.run_dialog()
        if is_ok == 1:
            db_main.the_session_handler.add_object_to_session(new_rec)
            db_main.the_session_handler.commit_session()
            # try_send_email_about_new_record(new_rec)
            self.sig_knbase_record_added.emit(new_rec.string_key())

    def dlg_edit_knbase_record(self, a_rec):
        if a_rec is None:
            raise BaseException("No knbase record selected!")
        edit_dialog = self.get_DlgEditSimpleRecord()
        edit_dialog.set_state_to_edit(a_rec)
        is_ok, new_rec = edit_dialog.run_dialog()
        if is_ok == 1:
            db_main.the_session_handler.merge_object_to_session(new_rec)  #На всякий случай
            db_main.the_session_handler.commit_session()
            self.sig_knbase_record_added.emit(new_rec.string_key())

    def dlg_delete_knbase_record(self, a_rec):
        if a_rec is None:
            raise BaseException("No knbase record selected!")
        a_msg = unicode(u"Подтверждаете удаление: ")
        a_msg += unicode(a_rec.headline)
        a_msg += unicode(u" ?")
        a_reply = QtGui.QMessageBox.question(self, unicode(u'Подтвердите'), a_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if a_reply == QtGui.QMessageBox.Yes:
            k = a_rec.string_key()
            db_main.the_session_handler.delete_concrete_object(a_rec)
            self.sig_knbase_record_added.emit(k)



