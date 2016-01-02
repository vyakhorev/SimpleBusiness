# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui

import datetime
import simple_locale
import db_main
import convert

from ui.ui_Dialog_EditSalesOppotunity import Ui_Dialog_EditSalesOppotunity
from gui_forms_logic.data_models import cDataModel_GeneralMaterialList

from gui_forms_logic.misc import qtdate_pack, qtdate_unpack

class gui_Dialog_EditSalesOpportunity(QtGui.QDialog, Ui_Dialog_EditSalesOppotunity):
    def __init__(self, parent=None):
        super(gui_Dialog_EditSalesOpportunity, self).__init__(parent)
        self.setupUi(self) #Метод от QtDesigner
        self.my_lead_entity = None
        self.client_model = None
        self.my_mode = 0   #1 - edit, 0 - new
        self.var_is_correct = False
        self.general_materials_model = cDataModel_GeneralMaterialList()
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
            super(gui_Dialog_EditSalesOpportunity, self).accept()

    def reject(self):
        if self.my_mode == 0: #if new, not from database
            self.my_lead_entity = None
        super(gui_Dialog_EditSalesOpportunity, self).reject()

    def run_dialog(self):
        user_decision = self.exec_()  #0 или 1
        if user_decision == QtGui.QDialog.Accepted:
            return [user_decision, self.my_lead_entity]
        elif user_decision == QtGui.QDialog.Rejected:
            return [user_decision, None]
