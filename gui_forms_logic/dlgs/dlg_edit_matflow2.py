# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui

import simple_locale

from ui.ui_Dialog_EditMatFlow import Ui_Dialog_EditMatFlow
from gui_forms_logic.data_models import cDataModel_GeneralMaterialList, cDataModel_MatDistTable2

from gui_forms_logic.data_model import DynamicTableWidget

class gui_Dialog_EditMatFlow(QtGui.QDialog, Ui_Dialog_EditMatFlow):
    def __init__(self, parent=None):
        super(gui_Dialog_EditMatFlow, self).__init__(parent)
        self.setupUi(self) #Метод от QtDesigner
        self.my_mf_entity = None
        self.my_mode = 0   #1 - edit, 0 - new

        # Combobox выбора материала
        self.general_materials_model = cDataModel_GeneralMaterialList()
        self.general_materials_model.switch_to_material_types()
        self.comboBox_material_type.setModel(self.general_materials_model)

        # Обновление при смене материала в главном Combo Box
        self.connect(self.comboBox_material_type, QtCore.SIGNAL("currentIndexChanged(int)"), self._material_type_selected)

        # Модель данных таблички
        headers = [unicode('Товар'), unicode('Вероятность закупки')]
        self.matflow_tablemodel = cDataModel_MatDistTable2({}, headers)

        # self.probs_column  -  это цифры или материалы???
        self.probs_column = DynamicTableWidget.ListModel([])
        self.probs_column_delegate = [self.probs_column, 0]
        DynamicTableWidget.add_tableview_to(self, self.matflow_tablemodel,
                                            delegates=self.probs_column_delegate,
                                            tableview=self.tableView_materials_and_probs)

        # Добавление строк в табличку
        self.pushButton_add_material.clicked.connect(self._add_material)
        self.pushButton_delete_material.clicked.connect(self._remove_material)

        # Нормализация вероятностей
        self.pushButton_normalize_probs.clicked.connect(self._normalize_probs)

    # Exposed methods

    def set_state_to_add_new(self, client_model):
        # Глобальные аттрибуты
        self.my_mode = 0
        self.my_mf_entity = None
        self.client_model = client_model
        # Формочку приводим в порядок
        self.setWindowTitle(unicode(u"Добавление линии снабжения для ") + unicode(self.client_model.name))
        # Сбрасываем модели данных (грубо)
        self._refresh_table_model_with_new_data({})
        self._refresh_delegate_with_new_data([])
        # reset columns width
        # self._reset_table_view()
        # Сбрасываем прочие виджеты
        self.comboBox_material_type.setCurrentIndex(-1)
        self.comboBox_material_type.setEnabled(True)
        zer = simple_locale.number2string(0.)
        self.lineEdit_cons_volume_mean.setText(zer)
        self.lineEdit_cons_period_mean.setText(zer)
        self.lineEdit_cons_vol_dev.setText(zer)
        self.lineEdit_cons_period_std.setText(zer)

    def set_state_to_edit(self, mf_entity):
        # Глобальные аттрибуты
        self.my_mode = 1
        self.my_mf_entity = mf_entity
        self.client_model = mf_entity.client_model
        # Формочку приводим в порядок
        self.setWindowTitle(unicode(u"Изменение линии снабжения для ") + unicode(self.client_model.name))
        # Заполняем модель
        self._refresh_table_model_with_matflow(self.my_mf_entity)
        self._refresh_delegate_with_material_type(self.my_mf_entity.material_type)
        # reset columns width
        self._reset_table_view()
        # Перезаполняем прочие виджеты
        ## Находим индекс элемента (чтобы в комбобоксе то что надо выбрать).
        ## 40 - роль для поиска по ключу, ключ - строка, уникальная глобально - string_key()
        indx = self.comboBox_material_type.findData(self.my_mf_entity.material_type.string_key(), 40)
        self.comboBox_material_type.setCurrentIndex(indx)
        self.comboBox_material_type.setEnabled(False)
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

    def run_dialog(self):
        user_decision = self.exec_()  #0 или 1
        if user_decision == QtGui.QDialog.Accepted:
            return [user_decision, self.my_mf_entity]
        elif user_decision == QtGui.QDialog.Rejected:
            return [user_decision, None]

    def accept(self):
        # Сделаю после того, как модель устаканится
        super(gui_Dialog_EditMatFlow, self).reject()

    def reject(self):
        if self.my_mode == 0: #if new, not from database
            self.my_mf_entity = None
        super(gui_Dialog_EditMatFlow, self).reject()

    # table and delegate operations

    def _refresh_delegate_with_material_type(self, material_type):
        # Перезаполняет делегат по группе товаров
        new_list = []
        for mat_i in material_type.materials:
            new_list += [mat_i]
        self._refresh_delegate_with_new_data(new_list)

    def _refresh_delegate_with_new_data(self, new_data):
        # В нескольких местах использую
        # new_dat - это list
        self.probs_column.refill_data(new_data)

    def _reset_table_view(self):
        self.tableView_materials_and_probs.setVisible(False)
        self.tableView_materials_and_probs.resizeColumnsToContents()
        self.tableView_materials_and_probs.setVisible(True)

    @staticmethod
    def repr_len(element):
        # getting length of element repr
        return len(element.__repr__())

    def _add_material(self):
        self.matflow_tablemodel.add_blank_row()

        # get max length item from potential items and set column width
        max_element = max(self._get_material_type().materials, key=self.repr_len)
        length = len(max_element.__repr__())
        self.tableView_materials_and_probs.setColumnWidth(0, length*6)

    def _remove_material(self):
        ind = self.tableView_materials_and_probs.currentIndex()
        self.matflow_tablemodel.remove_row(ind)

    def _normalize_probs(self):
        self.matflow_tablemodel.normalize(column=1)

    def _refresh_table_model_with_matflow(self, matflow):
        # Обновляет табличку по matflow
        new_data = {}
        for md_i in matflow.material_dist:
            new_data[md_i.material] = [md_i.choice_prob]
        self._refresh_table_model_with_new_data(new_data)

    def _refresh_table_model_with_new_data(self, new_data):
        # В нескольких местах использую
        # new_dat - это dict..
        self.matflow_tablemodel.refill_data(new_data)

    # Widget signal handlers

    def _material_type_selected(self, new_index):
        if self.my_mode == 1:
            # Оказывается, по умолчанию вызывается..
            # raise BaseException("This widget should be blocked in this mode!")
            return
        if new_index == 0:
            return
        new_mat_type = self.comboBox_material_type.itemData(new_index, 35).toPyObject()
        self._refresh_table_model_with_new_data({})
        self._refresh_delegate_with_material_type(new_mat_type)

    # general internal methods

    def _get_material_type(self):
        row = self.comboBox_material_type.currentIndex()
        if row>=0:
            # 35 - это роль модели данных
            selected_item = self.comboBox_material_type.itemData(row, 35).toPyObject()
            return selected_item