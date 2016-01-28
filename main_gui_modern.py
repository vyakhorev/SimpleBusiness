# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
import simple_locale
from datetime import datetime, timedelta

from gui_forms_logic.plot_window.matflow_plotting import Spreading, PlotViewerDialog
from gui_forms_logic.plot_window.matflow_plotting import get_shipments_prediction_areas

from ui.ui_ModernMainWindow_v2 import Ui_MainWindowModern

# dialogs
from gui_forms_logic.dlgs.dlg_edit_contact import gui_DialogCrm_EditContact
from gui_forms_logic.dlgs.dlg_edit_price import gui_Dialog_EditPrice
from gui_forms_logic.dlgs.dlg_edit_matflow2 import gui_Dialog_EditMatFlow
from gui_forms_logic.dlgs.dlg_sales_opportunity import gui_Dialog_EditSalesOpportunity
from gui_forms_logic.dlgs.dlg_edit_kn_base_record import gui_DialogCrm_EditSimpleRecord

# Import custom gui logic
from gui_forms_logic.data_models import cDataModel_CounterpartyList, cDataModel_HashtagList
from gui_forms_logic.record_mediators import cMedPrice, cMedMatFlow, cMedContact,\
        cMedKnBaseRecord, cMedSalesLead, cSimpleMediator
from gui_forms_logic.frame_builder import LabelFrame, RecFrame

import db_main
import gl_shared

import file_reports

# import threading

# TabNums = {"CPs":0, "KnBase":1}

# Constants #
# ----------#
# Turning on/off styles
STYLES = False
STYLE_URL = None
# How many lines to load first time
RECORDS_NUM = 5
# TODO move this to ini and settings..
LD = [640, 360]
HD = [1280, 720]
UHD = [1920, 1080]


class gui_MainWindow(QtGui.QMainWindow, Ui_MainWindowModern):

    sig_cp_record_added = QtCore.pyqtSignal(str)
    sig_cp_record_deleted = QtCore.pyqtSignal(str)
    sig_cp_record_edited = QtCore.pyqtSignal(str)

    sig_cp_record_massively_updated = QtCore.pyqtSignal()

    sig_knbase_record_added = QtCore.pyqtSignal(str)
    sig_knbase_record_deleted = QtCore.pyqtSignal(str)
    sig_knbase_record_edited = QtCore.pyqtSignal(str)

    def __init__(self, app, parent=None):
        super(gui_MainWindow, self).__init__(parent)
        self.app = app
        self.setupUi(self)
        self.resize(*HD)

        # Loading stylesheets
        if STYLES:
            style_sheet_src = QtCore.QFile('C:\Ilua\SimpleBusiness\SimpleBusiness\ui\Stylesheets\scheme.qss')
            style_sheet_src.open(QtCore.QIODevice.ReadOnly)
            if style_sheet_src.isOpen():
                self.setStyleSheet(QtCore.QVariant(style_sheet_src.readAll()).toString())
            style_sheet_src.close()

        ############
        # Menu
        ############

        self.action_Refresh.triggered.connect(self.refresh_active_tab)
        self.action_ReportPrices.triggered.connect(self.report_sale_prices_all)
        self.action_ReportInvoicePrices.triggered.connect(self.report_invoce_prices_all)
        self.action_ReportSalesForecast.triggered.connect(self.report_sales_forecast)

        ############
        # Counterparty tab
        ############
        self.current_cp = None
        # Left-side logic

        self.data_model_counterparties = cDataModel_CounterpartyList()
        self.data_model_counterparties_proxy = QtGui.QSortFilterProxyModel()
        self.data_model_counterparties_proxy.setSourceModel(self.data_model_counterparties)
        self.data_model_counterparties_proxy.setDynamicSortFilter(True)
        self.data_model_counterparties_proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

        self.listView_ClientList.setModel(self.data_model_counterparties_proxy)
        self.lineEdit_ClientFilter.textChanged.connect(self.data_model_counterparties_proxy.setFilterRegExp)
        self.listView_ClientList.selectionModel().currentChanged.connect(self.click_on_CP)

        # Right-side logic
        # self.mediators_frame_list = []
        self.mediators_frame_list = {}

        # Placing QScrollArea
        self.scroll_area_cp_frames = QtGui.QScrollArea()
        self.scroll_area_cp_frames.setWidgetResizable(True)
        self.scroll_area_cp_frames.setFocusPolicy(QtCore.Qt.NoFocus)
        self.scroll_area_cp_frames.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        # adding Scrollbar to QScrollArea
        self.scr_bar = QtGui.QScrollBar()
        self.scroll_area_cp_frames.setVerticalScrollBar(self.scr_bar)
        # put QScrollArea in main window
        self.horizontalLayout_2.addWidget(self.scroll_area_cp_frames)

        # inserting vertical layout at right
        self.mediators_list_layout = QtGui.QVBoxLayout()
        self.Base_widget = QtGui.QWidget()
        self.Base_widget.setLayout(self.mediators_list_layout)
        # setting Widget for QScrollArea
        self.scroll_area_cp_frames.setWidget(self.Base_widget)

        # (((o))) connect signals to methods
        # TODO implement scroll event
        # self.scr_bar.valueChanged.connect(self.scrolled)

        # Dialog names (use methods to get them!
        self._DlgEditContact = None
        self._DlgEditSimpleRecord = None
        self._DlgEditSalesOpportunity = None
        self._DlgEditPrice = None
        self._DlgEditMatFlow = None

        # Connect signals that would be raised by widget logics
        self.sig_cp_record_added.connect(self.handle_cp_new_record)
        self.sig_cp_record_deleted.connect(self.handle_cp_delete_record)
        self.sig_cp_record_edited.connect(self.handle_cp_edit_record)
        self.sig_cp_record_massively_updated.connect(self.handle_cp_massively_updated)

        ############
        # Knowledge base tab
        ############
        self.crm_records_dispenser = None #Holds state of the iterator over the records
        self.current_tag = None

        # Basic signals and models
        self.pushButton_KnBaseEmptyNote.clicked.connect(self.dlg_add_knbase_record)
        self.pushButton_LastRecords.clicked.connect(self.reset_news_filters)
        self.pushButton_SearchKnBase.clicked.connect(self.do_deep_search)
        self.pushButton_RenameHashtag.clicked.connect(self.rename_hashtag)
        self.pushButton_DeleteHashtag.clicked.connect(self.delete_hastag)

        self.data_model_hashtags = cDataModel_HashtagList()
        self.data_model_hashtags_proxy = QtGui.QSortFilterProxyModel()
        self.data_model_hashtags_proxy.setSourceModel(self.data_model_hashtags)
        self.data_model_hashtags_proxy.setDynamicSortFilter(True)
        self.data_model_hashtags_proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

        self.listView_Hashtags.setModel(self.data_model_hashtags_proxy)
        self.lineEdit_KnBase_Search.textChanged.connect(self.new_crm_search_text_input)
        self.listView_Hashtags.selectionModel().currentChanged.connect(self.click_on_hashtag)

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

        # Connect signals that would be raised by widget logics
        self.sig_knbase_record_added.connect(self.handle_knbase_new_record)
        self.sig_knbase_record_deleted.connect(self.handle_knbase_delete_record)
        self.sig_knbase_record_edited.connect(self.handle_knbase_edit_record)

        # routines
        self.run_setup_routines()


    def run_setup_routines(self):
        # Clean old temp_files
        file_reports.clean_old_temp_files()

    ###############################
    # handle red X button closing
    ###############################
    def closeEvent(self, event):
        """
            Here will be automation right before application close
        """
        event.accept()



    #################
    # Вкладка с контрагентами
    #################

    def click_on_CP(self, index_to, index_from):
        # Check if old mediators exist and delete
        if len(self.mediators_frame_list) != 0:
            self.delete_widgets(self.mediators_list_layout)

        cp_i = index_to.data(35).toPyObject()
        self.current_cp = cp_i
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
        header.add_call('report_prices_cp', u'Excel', cp)
        header.add_call('report_print_offer', u'Offer (doc)', cp)
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
            header.add_call('estimate_group_mat_flows', u'По статистике', cp)
            header.add_call('dlg_add_matflow', u'+Добавить', cp)
            yield header
            for mf_i in db_main.get_mat_flows_list(cp):
                new_med = cMedMatFlow(self, mf_i)
                new_med.add_call('show_plot_for_price', u'График', mf_i)
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
        self.mediators_frame_list[mediator.get_key()] = new_frame
        self.mediators_list_layout.addWidget(new_frame)

    @staticmethod
    def delete_widgets(layout):
        """
            Deleting all widgets from any layout
        """
        for wg_i in reversed(xrange(layout.count())):
            item = layout.takeAt(wg_i)

            try:
                item.widget().clear_active_buttons()

            except AttributeError:
                pass
                # print('Frame hasnt active buttons')
            # print('going to remove {}'.format(item))
            layout.removeItem(item)
            item.widget().deleteLater()

    def redraw_mediators(self, cp):
        """
            Clear and redraw mediators for current counterparty
        """
        self.delete_widgets(self.mediators_list_layout)
        for med_i in self._iter_cp_mediator(cp):
            self.make_frame_from_mediator(med_i)

    # Signals with counterparty tab
    @QtCore.pyqtSlot(str)
    def handle_cp_new_record(self, rec_key):
        self.redraw_mediators(self.current_cp)

    @QtCore.pyqtSlot(str)
    def handle_cp_delete_record(self, rec_key):
        self.redraw_mediators(self.current_cp)

    @QtCore.pyqtSlot(str)
    def handle_cp_edit_record(self, rec_key):
        self.redraw_mediators(self.current_cp)

    @QtCore.pyqtSlot()
    def handle_cp_massively_updated(self):
        self.redraw_mediators(self.current_cp)

    #################
    # Вкладка с заметками
    #################

    def reset_news_filters(self):
        """
        По кнопке убираем фильтр поиска и отображаем только свежие
        """
        self.current_tag = None
        self.lineEdit_KnBase_Search.clear()
        rec_iter = db_main.get_dynamic_crm_records_iterator() #records <-> crm news records

        self.rebuild_crm_scrl_area_from_iterator(rec_iter)

    @QtCore.pyqtSlot(str)
    def new_crm_search_text_input(self, new_text):
        """
        Вызывается при вводе нового текста в строку поиска
        Args:
            new_text: текст из поля ввода
        """
        # Вот это нужно чтобы список тегов слева пофильтровать
        self.data_model_hashtags_proxy.setFilterRegExp(QtCore.QString(new_text))

    @QtCore.pyqtSlot()
    def do_deep_search(self):
        self.current_tag = None
        search_string = unicode(self.lineEdit_KnBase_Search.text())
        self.rebuild_crm_scrl_area_from_iterator(db_main.get_dynamic_crm_records_iterator_search(search_string))

    def click_on_hashtag(self, index_to, index_from):
        """
        Вызывается при клике на хештэг
        """
        tag_i = index_to.data(35).toPyObject()
        if tag_i is None:
            return
        if self.current_tag is None: self.current_tag = tag_i
        self.current_tag = tag_i
        self.rebuild_crm_scrl_area_from_iterator(db_main.get_dynamic_crm_records_iterator_by_hashtag(tag_i))

    def rebuild_crm_scrl_area_from_iterator(self, new_iterator):
        # Стираем старые виджеты
        self.delete_widgets(self.mediators_list_layout_KnBase)
        # Делаем диспенсер для новых записей (будут дальше в медиаторы и фреймы трансформироваться)
        self.crm_records_dispenser = cIteratorDispenser(new_iterator)
        # Добавляем RECORDS_NUM первых записей
        self.add_crm_records_to_area(autoload=True)

    def scrolled_KnBase(self):
        """
            Slot, activated by scrolling records  Qscrollarea
        """
        # Допечатываем ещё виджетов (Один штук)
        if self.crm_records_dispenser is None:
            return

        if self.scr_bar_KnBaseRecords.value() >= self.scr_bar_KnBaseRecords.maximum():
            self.add_crm_records_to_area(autoload=True)

    def add_crm_records_to_area(self, autoload = False):
        """
            Допечатывает виджетов в скрул арею, создавая медиаторы из self.crm_records_dispenser.
        """
        if autoload:
            self.got_records = self.crm_records_dispenser.give_next(RECORDS_NUM)
        else:
            self.got_records = self.crm_records_dispenser.give_next(1)

        for rec_i in self.got_records:
            # Создаем медиатор из записи (тут только заметки пока..)
            new_mediator = cMedKnBaseRecord(self, rec_i)
            new_mediator.add_call('dlg_pin_knbase_record', u'Закладка', rec_i)
            new_mediator.add_call('dlg_edit_knbase_record', u'Изменить', rec_i)
            new_mediator.add_call('dlg_delete_knbase_record', u'Удалить', rec_i)

            # Создаем фрейм
            new_frame = RecFrame(new_mediator, self)
            self.mediators_frame_list_KnBase.append(new_frame) # Это излишний вызов - может, пригодится..
            self.mediators_list_layout_KnBase.addWidget(new_frame) # Шмагия

    @QtCore.pyqtSlot(str)
    def handle_knbase_new_record(self, rec_key):
        print("new record handler triggered " + str(rec_key))

    @QtCore.pyqtSlot(str)
    def handle_knbase_delete_record(self, rec_key):
        print("delete record handler triggered " + str(rec_key))

    @QtCore.pyqtSlot(str)
    def handle_knbase_edit_record(self, rec_key):
        print("edit record handler triggered " + str(rec_key))

    def rename_hashtag(self):
        ht_i = self._get_selected_hashtag()
        if ht_i is None:
            return

        is_reserved = db_main.check_if_hashtag_from_system(ht_i.text)
        if is_reserved:
            QtGui.QMessageBox.information(self, u'Внимание',
                                          u'Имя зарезервировано клиентом или товаром, не могу переименовать',
                                          QtGui.QMessageBox.Ok)
            return

        new_name, is_ok = QtGui.QInputDialog.getText(self, u"Новое имя для #"+ht_i.text,
                                                     u'Заменить  #' + ht_i.text + u'  на:',
                                                     QtGui.QLineEdit.Normal, ht_i.text)
        new_name = unicode(new_name)
        if not is_ok:
            return

        does_exist = db_main.check_if_hashtag_name_exists(new_name)
        if does_exist:
            a_reply = QtGui.QMessageBox.question(self, u'Подтвердите',
                                                 u'Хештег ' + new_name + u' уже есть, объединяю?',
                                             QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
            if a_reply != QtGui.QMessageBox.Yes:
                return

        db_main.rename_hashtag_usages(old_hashtag_name=ht_i.text, new_hashtag_name=new_name)

    def delete_hastag(self):
        ht_i = self._get_selected_hashtag()
        if ht_i is None:
            return
        a_reply = QtGui.QMessageBox.question(self, u'Подтвердите',
                                             u"Удалить хештег #" + unicode(ht_i.text) + u' ?',
                                             QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if a_reply != QtGui.QMessageBox.Yes:
            return

        is_reserved = db_main.check_if_hashtag_from_system(ht_i.text)
        if is_reserved:
            QtGui.QMessageBox.information(self, u'Внимание',
                                          u'Имя зарезервировано клиентом или товаром, не могу удалить',
                                          QtGui.QMessageBox.Ok)
            return

        db_main.delete_hashtag_usage(ht_i.text)

    def _get_selected_hashtag(self):
        indeces = self.listView_Hashtags.selectedIndexes()
        if len(indeces) == 0:
            return None
        # 35 - это роль модели данных
        selected_item = indeces[0].data(35).toPyObject()
        return selected_item

    ###################
    # Ctrl+R handle
    ###################
    def refresh_active_tab(self):
        self.data_model_counterparties.beginResetModel()
        self.data_model_counterparties.update_list()
        self.data_model_counterparties.endResetModel()
        self.data_model_hashtags.update_list()

        if not self.current_cp is None:
            self.redraw_mediators(self.current_cp)

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
            # Сигнал!
            self.sig_cp_record_added.emit(a_price.string_key())
            # TODO: заметка

    def dlg_edit_price(self, price_instance):
        if price_instance is None:
            raise BaseException("No price selected!")
        edit_dialog = self.get_DlgEditPrice()
        edit_dialog.set_state_to_edit(price_instance)
        is_ok, a_price = edit_dialog.run_dialog()
        if is_ok == 1: # a_price = price_instance
            # Записали в базу данных
            db_main.the_session_handler.commit_session()
            # Сигнал!
            self.sig_cp_record_edited.emit(a_price.string_key())
            # TODO: заметка

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
            # Сигнал!
            self.sig_cp_record_deleted.emit(k)
            # TODO: заметка

    # ПОТОКИ СНАБЖЕНИЯ (MATFLOW)

    def show_plot_for_price(self, matflow_instance):
        import numpy as np
        current_date = datetime.today()
        history = db_main.get_shipments_history(matflow_instance.client_model, matflow_instance.material_type)
        tmp_lst = []

        for date_bought, qtty_bought in history:
            daysfromstart = (date_bought-current_date).days
            tmp_lst.append([daysfromstart, qtty_bought, 0, 0])
        history_array = np.array(tmp_lst)
        nd = matflow_instance.next_expected_order_date
        next_event_date = datetime(year=nd.year, month=nd.month, day=nd.day)

        Edt = matflow_instance.stats_mean_timedelta
        Ev = matflow_instance.stats_mean_volume
        Ddt = matflow_instance.stats_std_timedelta
        Dv = matflow_instance.stats_std_volume

        predictions = get_shipments_prediction_areas(Edt, Ev, Ddt, Dv, next_event_date, current_date, 360)

        data = {}
        if len(history_array) > 0:
            alldata = np.concatenate((history_array, predictions), axis=0)
        else:
            alldata = predictions

        data[unicode(matflow_instance.material_type) + u" by " + unicode(matflow_instance.client_model)] = alldata

        # print data
        wind = None
        wind = PlotViewerDialog(self)
        wind.plot(data, current_date=current_date)
        # wind.plot(data)
        wind.show()

    def dlg_add_matflow(self, agent):
        # Походу, старый вариант диалога.. Надо поискать новый или пофиксить.
        if agent is None:
            raise BaseException("No agent selected!")
        if agent.discriminator != "client":
            raise BaseException("Wrong agent type!")
        edit_dialog = self.get_DlgEditMatFlow()
        edit_dialog.set_state_to_add_new(agent)
        is_ok, a_mf, delete_list = edit_dialog.run_dialog() #delete list всегда пуст
        if is_ok == 1:
            #Записали в базу данных
            db_main.the_session_handler.add_object_to_session(a_mf)
            db_main.the_session_handler.commit_session()
            # Сигнал!
            self.sig_cp_record_added.emit(a_mf.string_key())
            #Создаём заметку
            htmltext_template = db_main.crm_template_new_budget_for_new_matflow(a_mf)
            self.dlg_add_knbase_record(htmltext=htmltext_template, header=u"Бюджет продаж - новая линия сбыта")

    def dlg_edit_matflow(self, matflow_instance):
        if matflow_instance is None:
            raise BaseException("No material flow selected!")
        old_volume = matflow_instance.stats_mean_volume
        old_freq = matflow_instance.stats_mean_timedelta
        edit_dialog = self.get_DlgEditMatFlow()
        edit_dialog.set_state_to_edit(matflow_instance)
        is_ok, a_mf, delete_list  = edit_dialog.run_dialog()
        if is_ok == 1:  # a_mf = matflow_instance
            # Пометим объекты на удаление
            for obj_i in delete_list:
                db_main.the_session_handler.active_session.delete(obj_i)
            # Записали в базу данных удаления и изменения
            db_main.the_session_handler.commit_session()
            # Не забыли обновить табличку
            self.sig_cp_record_edited.emit(a_mf.string_key())
            # Заметка
            htmltext_template = db_main.crm_template_change_volume_in_budget(a_mf, old_volume, old_freq)
            self.dlg_add_knbase_record(htmltext=htmltext_template, header=u"Бюджет продаж - уточнение")

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

    def estimate_group_mat_flows(self, agent):
        if agent is None:
            raise BaseException("No agent selected!")
        if agent.discriminator != "client":
            raise BaseException("Wrong agent type!")
        a_msg = u"Будет произведена переоценка потребления всех материалов по клиенту " + unicode(agent.name) +\
                u", действие нельзя отменить - подтверждаете операцию?"
        a_reply = QtGui.QMessageBox.question(self, unicode(u'Подтвердите'), a_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if a_reply == QtGui.QMessageBox.Yes:
            agent.update_stats_on_material_flows(db_main.estimate_shipment_stats(agent))
            for mf_i in agent.material_flows:
                db_main.the_session_handler.merge_object_to_session(mf_i)
            db_main.the_session_handler.commit_session()
            # Сигнал!
            self.sig_cp_record_massively_updated.emit()
            #Создаём заметку в базе (предлагаем создать)
            htmltext_template = db_main.crm_template_new_budget(agent)
            htmltext_template += u" статистика потребления"
            self.dlg_add_knbase_record(htmltext=htmltext_template, header=u"Бюджет продаж - статистика")

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
            # Сигнал
            self.sig_cp_record_added.emit(new_lead.string_key())
            # Заметка
            htmltext_template, text_header = db_main.crm_template_new_sales_lead(new_lead)
            self.dlg_add_knbase_record(htmltext=htmltext_template, header=text_header)

    def dlg_edit_lead(self, a_lead):
        if a_lead is None:
            raise BaseException("No sales opportunity selected!")
        old_lead = a_lead.get_dummy_copy()
        edit_dialog = self.get_DlgEditSalesOpportunity()
        edit_dialog.set_state_to_edit(a_lead)
        is_ok, new_lead = edit_dialog.run_dialog() #new_lead = a_lead
        if is_ok == 1:
            # Записали в базу данных (нужен ли мердж?..)
            db_main.the_session_handler.commit_session()
            # Сигнал
            self.sig_cp_record_edited.emit(a_lead.string_key())
            # Заметка
            htmltext_template, text_header = db_main.crm_template_change_sales_lead(old_lead, new_lead)
            self.dlg_add_knbase_record(htmltext=htmltext_template, header=text_header)

    def dlg_delete_lead(self, a_lead):
        if a_lead is None:
            raise BaseException("No sales opportunity selected!")
        a_msg = unicode(u"Подтверждаете забвение возможности по товару %s? Или, может, сроки перенесете?") %(unicode(a_lead.material_type.material_type_name))
        a_reply = QtGui.QMessageBox.question(self, unicode(u'Подтвердите'), a_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if a_reply == QtGui.QMessageBox.Yes:
            k = a_lead.string_key()
            db_main.the_session_handler.delete_concrete_object(a_lead)
            # Сигнал
            self.sig_cp_record_deleted.emit(k)

    # ЗАМЕТКИ

    def dlg_pin_knbase_record(self, a_rec):
        if a_rec is None:
            raise BaseException("No knbase record selected!")
        pin_dialog = QtGui.QDialog(self)
        some_text_view = QtGui.QTextBrowser()
        some_text_view.setText('im hehe')
        base_layout = QtGui.QVBoxLayout()
        some_text_view.setHtml(a_rec.long_html_text)
        pin_dialog.setLayout(base_layout)
        pin_dialog.layout().addWidget(some_text_view)
        pin_dialog.resize(*LD)
        # preset_tags = a_rec.get_tags_text()

        pin_dialog.show()


    def dlg_add_knbase_record(self, hashtags_list=[], htmltext='', header=''):
        edit_dialog = self.get_DlgEditSimpleRecord()
        edit_dialog.set_state_to_add_new([], htmltext, header)
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

    # ОТЧЕТЫ

    def report_prices_cp(self, cp):
        file_reports.report_on_prices(cp)

    def report_print_offer(self, cp):
        file_reports.print_offer(cp)

    def report_sale_prices_all(self):
        print('reporting!')

    def report_invoce_prices_all(self):
        print('reporting!')

    def report_sales_forecast(self):
        print('reporting!')

class cIteratorDispenser():
    '''
    Выдает содержимое итератора порциями. Можно потом усложнить до формирования нормальных запросов..
    '''
    def __init__(self, some_iterator):
        self.my_iterator = some_iterator
        self.finished = False

    def give_next(self, how_much=1):
        '''
        Args:
            how_much: сколько элементов хочется взять
        Returns: лист с элементами
        '''
        ans = []
        if self.finished: return ans
        for k in xrange(0,how_much):
            # FIXME: how to load exactly one record per time?
            try:
                ans+=[next(self.my_iterator)]
            except StopIteration:
                self.finished = True
                return ans
        return ans

