# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
import db_main
import simple_locale

from ui.ui_DialogCrm_EditContact import Ui_DialogCrm_EditContact
from gui_forms_logic.data_models import cDataModel_CounterpartyList, CDataModel_ContactDetailsTable

unicode_codec = QtCore.QTextCodec.codecForName(simple_locale.ultimate_encoding)

class gui_DialogCrm_EditContact(QtGui.QDialog, Ui_DialogCrm_EditContact):
    def __init__(self, parent=None):
        super(gui_DialogCrm_EditContact, self).__init__(parent)
        self.setupUi(self) #Метод от QtDesigner
        self.my_entity = None
        self.cp_list_model = cDataModel_CounterpartyList()
        self.cont_details_model = CDataModel_ContactDetailsTable()
        self.comboBox_company.setModel(self.cp_list_model)
        self.tableView_contact_info.setModel(self.cont_details_model)
        self.my_mode = 0 # 0 - new, 1 - edit
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

    # def add_details_cell_personal(self):
    #     self.cont_details_model.insertNewDetail(u"Мобильный личный", u"+7 (...) ...-...-...", True)

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
                    QtGui.QMessageBox.information(self, unicode(u"Ошибка ввода"), unicode(u"Укажите имя человека"))
                    is_var_ok = False
            else:
                is_person = False
                contact_name = ""
                contact_job = ""
        if is_var_ok:
            row = self.comboBox_company.currentIndex()
            if row >= 0:
                company_emp = self.comboBox_company.itemData(row, 35).toPyObject()
            else:
                QtGui.QMessageBox.information(self, unicode(u"Ошибка ввода"), unicode(u"Не выбрана компания"))
                is_var_ok = False
        if is_var_ok:
            contacts_list = self.cont_details_model.get_all_data()
            if len(contacts_list) == 0:
                QtGui.QMessageBox.information(self, unicode(u"Ошибка ввода"), unicode(u"Добавьте хоть один контакт"))
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
                if company_emp != self.my_entity.company:
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
