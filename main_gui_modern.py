# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
import simple_locale

from ui.ui_ModernMainWindow_v2 import Ui_MainWindowModern

# dialogs
from gui_forms_logic.dlgs.dlg_edit_contact import gui_DialogCrm_EditContact
from gui_forms_logic.dlgs.dlg_edit_price import gui_Dialog_EditPrice

# Import custom gui logic
from gui_forms_logic.data_models import cDataModel_CounterpartyList
from gui_forms_logic.record_mediators import cMedPrice, cMedMatFlow, cMedContact, cSimpleMediator
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
        self._DlgEditSalesOppotunity = None
        self._DlgEditPrice = None
        self._DlgEditMatFlow = None

        # Connect signals that would be raised by widget logics
        self.sig_cp_record_added.connect(self.handle_cp_new_record)
        self.sig_cp_record_deleted.connect(self.handle_cp_delete_record)
        self.sig_cp_record_edited.connect(self.handle_cp_edit_record)

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
        header.set_label(u'Контакты')
        header.add_call('add_crm_contact', u'+Добавить')
        yield header
        for cnt_i in db_main.get_contacts_list(cp):
            new_med = cMedContact(self, cnt_i)
            new_med.add_call('edit_crm_contact', u'Изменить', cnt_i)
            new_med.add_call('delete_crm_contact', u'Удалить', cnt_i)
            yield new_med

        # Цены (как покупателю, так и от поставщика)
        header = cSimpleMediator(self)
        header.set_label(u'Цены')
        header.add_call('dlg_add_price', u'+Добавить')
        yield header
        for pr_i in db_main.get_prices_list(cp):
            new_med = cMedPrice(self, pr_i)
            new_med.add_call('dlg_edit_price', u'Изменить', pr_i)
            new_med.add_call('dlg_delete_price', u'Удалить', pr_i)
            yield new_med

        # Список линий снабжения
        if cp.discriminator == 'client':
            header = cSimpleMediator(self)
            header.set_label(u'Потоки снабжения')
            header.add_call('dlg_add_matflow', u'+Добавить')
            yield header
            for mf_i in db_main.get_mat_flows_list(cp):
                print(mf_i)
                new_med = cMedMatFlow(self, mf_i)
                new_med.add_call('dlg_edit_matflow', u'Изменить', mf_i)
                new_med.add_call('dlg_delete_matflow', u'Удалить', mf_i)
                yield new_med

    def make_frame_from_mediator(self, mediator):
        """
            Automatically building gui for each mediator
        :param mediator: incoming mediator class instance
        :return: None
        """
        #self.scroll_area.

        if mediator.label != '':
            new_frame = LabelFrame(mediator, self)
            self.mediators_frame_list.append(new_frame)
            self.mediators_list_layout.addWidget(new_frame)

        else:
            new_frame_2 = RecFrame(mediator, self)
            self.mediators_frame_list.append(new_frame_2)
            self.mediators_list_layout.addWidget(new_frame_2)

    # Signals with counterparty tab
    @QtCore.pyqtSlot(str)
    def handle_cp_new_record(self, rec_key):
        print("new record handler triggered " + str(rec_key))

    @QtCore.pyqtSlot(str)
    def handle_cp_delete_record(self, rec_key):
        print("delete record handler triggered " + str(rec_key))

    @QtCore.pyqtSlot(str)
    def handle_cp_edit_record(self, rec_key):
        print("edit record handler triggered " + str(rec_key))

    ###################
    # Управление диалоговыми окнами
    ###################

    # LAZY открытие

    # def get_DlgEditSimpleRecord(self):
    #     if self._DlgEditSimpleRecord is None:
    #         self._DlgEditSimpleRecord = gui_DialogCrm_EditSimpleRecord(self)
    #     return self._DlgEditSimpleRecord

    def get_DlgEditContact(self):
        if self._DlgEditContact is None:
            self._DlgEditContact = gui_DialogCrm_EditContact(self)
        return self._DlgEditContact

    # def get_DlgEditCPdata(self):
    #     if self._DlgEditCPdata is None:
    #         self._DlgEditCPdata = gui_DialogCrm_EditCounterpartyData(self)
    #     return self._DlgEditCPdata
    #
    # def get_DlgEditSalesOppotunity(self):
    #     if self._DlgEditSalesOppotunity is None:
    #         self._DlgEditSalesOppotunity = gui_Dialog_EditSalesOppotunity(self)
    #     return self._DlgEditSalesOppotunity
    #
    # def get_DlgEditPrice(self):
    #     if self._DlgEditPrice  is None:
    #         self._DlgEditPrice = gui_Dialog_EditPrice(self)
    #     return self._DlgEditPrice
    #
    # def get_DlgEditMatFlow(self):
    #     if self._DlgEditMatFlow  is None:
    #         self._DlgEditMatFlow = gui_Dialog_EditMatFlow(self)
    #     return self._DlgEditMatFlow

    # КОНТАКТЫ

    def add_crm_contact(self):
        edit_dialog = self.get_DlgEditContact()
        edit_dialog.set_state_to_add_new()
        ans = edit_dialog.run_dialog()
        if ans[0] == 1:
            db_main.the_session_handler.add_object_to_session(ans[1])
            db_main.the_session_handler.commit_session()
            self.sig_cp_record_added.emit(ans[1].string_key())

    def edit_crm_contact(self, selected_contact):
        edit_dialog = self.get_DlgEditContact()
        if selected_contact is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Вы не выбрали контакт для редактирования"))
            return

        edit_dialog.set_state_to_edit(selected_contact)
        ans = edit_dialog.run_dialog()
        if ans[0] == 1:
            db_main.the_session_handler.commit_session()
            self.sig_cp_record_edited.emit(ans[1].string_key())

    def delete_crm_contact(self, selected_contact):
        if selected_contact is None:
            QtGui.QMessageBox.information(self,unicode(u"Не понимаю"),unicode(u"Вы не выбрали контакт для удаления"))
            return

        a_msg = unicode(u"Подтверждаете удаление: ") + unicode(selected_contact.name +
                                    " @ " + selected_contact.company.name) + unicode(u" ?")
        a_reply = QtGui.QMessageBox.question(self, unicode(u'Подтвердите'), a_msg,
                                             QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if a_reply == QtGui.QMessageBox.Yes:
            db_main.the_session_handler.delete_concrete_object(selected_contact)
            self.sig_cp_record_deleted.emit(selected_contact.string_key())

    # ЦЕНЫ

    def dlg_add_price(self):
        self.sig_cp_record_added.emit("test_key")

    def dlg_edit_price(self, price_instance):
        self.sig_cp_record_edited.emit(price_instance.string_key())

    def dlg_delete_price(self, price_instance):
        self.sig_cp_record_deleted.emit(price_instance.string_key())

    def dlg_add_matflow(self):
        self.sig_cp_record_added.emit("test_key")

    def dlg_edit_matflow(self, matflow_instance):
        self.sig_cp_record_edited.emit(matflow_instance.string_key())

    def dlg_delete_matflow(self, matflow_instance):
        self.sig_cp_record_deleted.emit(matflow_instance.string_key())


