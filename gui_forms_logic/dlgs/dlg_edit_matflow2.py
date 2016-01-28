# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui

import simple_locale, convert, db_main, utils
import numpy as np
from datetime import datetime, timedelta

from ui.ui_Dialog_EditMatFlow import Ui_Dialog_EditMatFlow
from gui_forms_logic.data_models import cDataModel_GeneralMaterialList, cDataModel_MatDistTable2

from gui_forms_logic.data_model import DynamicTableWidget

from gui_forms_logic.plot_window.matflow_plotting import Spreading, PlotViewerDialog
from gui_forms_logic.plot_window.matflow_plotting import get_shipments_prediction_areas

from gui_forms_logic.misc import qtdate_pack, qtdate_unpack

class gui_Dialog_EditMatFlow(QtGui.QDialog, Ui_Dialog_EditMatFlow):
    def __init__(self, parent=None):
        super(gui_Dialog_EditMatFlow, self).__init__(parent)
        self.setupUi(self) #Метод от QtDesigner
        self.my_mf_entity = None
        self.my_mode = 0   #1 - edit, 0 - new
        self.data_to_delete = []

        # Combobox выбора материала
        self.general_materials_model = cDataModel_GeneralMaterialList()
        self.general_materials_model.switch_to_material_types()
        self.comboBox_material_type.setModel(self.general_materials_model)

        # Обновление при смене материала в главном Combo Box
        self.connect(self.comboBox_material_type, QtCore.SIGNAL("currentIndexChanged(int)"),
                     self._material_type_selected)

        # Кнопка графика
        self.graph_button = QtGui.QPushButton(unicode('График'))
        self.horizontalLayout_6.insertWidget(1, self.graph_button)

        # Метод для кнопки - "График"
        self.graph_button.clicked.connect(self.showplot)

        # Модель данных таблички
        headers = [u'Спецификация товара', u'Вероятность выбора']
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

        # Удобства
        self.pushButton_down_025.clicked.connect(self._put_volume_down_025)
        self.pushButton_up_025.clicked.connect(self._put_volume_up_025)
        self.pushButton_EstimateStatistics.clicked.connect(self._do_estimate_from_statistics)

    # Exposed methods

    def set_state_to_add_new(self, client_model):
        # Глобальные аттрибуты
        self.my_mode = 0
        self.my_mf_entity = None
        self.client_model = client_model
        self.data_to_delete = []
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
        self.dateEdit_NextExpectedOrder.setDate(datetime.today())
        self.label_MeasUnit.setText(u"")

    def set_state_to_edit(self, mf_entity):
        # Глобальные аттрибуты
        self.my_mode = 1
        self.my_mf_entity = mf_entity
        self.client_model = mf_entity.client_model
        self.data_to_delete = []
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
        if self.my_mf_entity.next_expected_order_date is None:
            self.dateEdit_NextExpectedOrder.setDate(qtdate_pack(datetime.today()))
        self.label_MeasUnit.setText(self.my_mf_entity.material_type.measure_unit)
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
            return [user_decision, self.my_mf_entity, self.data_to_delete]
        elif user_decision == QtGui.QDialog.Rejected:
            return [user_decision, None, []]

    def accept(self):
        # Check if the data is correct
        self.var_is_correct = True
        if self.var_is_correct:
            material_type = self._inp_erh(self._get_material_type(),unicode(u"материал"))
        if self.var_is_correct:
            cons_expectation =  self._inp_erh(self._get_cons_volume_mean_value(),unicode(u"объём потребления"))
        if self.var_is_correct:
            cons_deviation = self._inp_erh(self._get_cons_volume_stdev_value(),unicode(u"отклонение объёмов"))
            if cons_deviation <= 1:
                self.var_is_correct = False
                QtGui.QMessageBox.information(self,unicode(u"Ошибка ввода"),unicode(u"Слишком малое отклонение объёмов"))
            if cons_deviation >= 300:
                self.var_is_correct = False
                QtGui.QMessageBox.information(self,unicode(u"Ошибка ввода"),unicode(u"Слишком большое отклонение объёмов"))
        if self.var_is_correct:
            periodicy_expectation = self._inp_erh(self._get_periodicy_expectation_value(),unicode(u"регулярность заказа"))
        if self.var_is_correct:
            periodicy_std = self._inp_erh(self._get_periodicy_stdev_value(),unicode(u"задержки заказа"))
        if self.var_is_correct:
            try:
                self._normalize_probs()
            except ZeroDivisionError:
                self.var_is_correct = False
                QtGui.QMessageBox.information(self,unicode(u"Ошибка ввода"),
                                              unicode(u"Хотя бы одна вероятность должна быть больше нуля"))
        if self.var_is_correct:
            next_date_prediction = self._get_next_date_prediction()
        if self.var_is_correct:
            # Напоследок, принимаем даныне из таблички
            prob_rows = self.matflow_tablemodel.get_mapped_data(list)
            if len(prob_rows) == 0:
                self.var_is_correct = False
                QtGui.QMessageBox.information(self,unicode(u"Ошибка ввода"),
                                              unicode(u"Должен быть хотя бы один товар в табличке"))
        if not self.var_is_correct:
            return

        # Перерабатываем
        if self.my_mode == 0: #Новый добавляем
            self.my_mf_entity = db_main.c_material_flow()
            self.my_mf_entity.client_model = self.client_model
            self.my_mf_entity.material_type = material_type
        self.my_mf_entity.are_materials_equal = self._get_are_materials_substitude()
        self.my_mf_entity.put_supplier_order_if_not_available = self._get_is_direct_order()
        self.my_mf_entity.stats_mean_timedelta = periodicy_expectation
        self.my_mf_entity.stats_std_timedelta = periodicy_std
        self.my_mf_entity.stats_mean_volume = cons_expectation
        # Проценты только после заполнения объёма
        self.my_mf_entity.set_volume_std_from_proc(cons_deviation)

        self.my_mf_entity.next_expected_order_date = next_date_prediction

        # Сверяем табличку вероятностей выбора товара
        mat_dict = {}
        for mat_i, prob_i in prob_rows:
            if mat_dict.has_key(mat_i):
                mat_dict[mat_i] += prob_i
            else:
                mat_dict[mat_i] = prob_i
        for md_i in self.my_mf_entity.material_dist:
            if mat_dict.has_key(md_i.material):
                md_i.choice_prob = mat_dict.pop(md_i.material)
            else:
                # Товара больше нет на форме. Пометим на удаление.
                self.data_to_delete += [md_i]
        for mat_i, prob_i in mat_dict.iteritems(): # Оставшихся не было. Добавим.
            new_md_i = db_main.c_material_flow_matdist(material = mat_i, choice_prob = prob_i)
            self.my_mf_entity.material_dist += [new_md_i]
        super(gui_Dialog_EditMatFlow, self).accept()

    def reject(self):
        # Удаляем лишние ссылки
        self.my_mf_entity = None
        self.client_model = None
        self.data_to_delete = []
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

    # More complex signal handlers

    def _material_type_selected(self, new_index):
        if self.my_mode == 1:
            return  # В этом режиме виджет заблокирован
        if new_index <= 0:
            return
        new_mat_type = self.comboBox_material_type.itemData(new_index, 35).toPyObject()
        self.label_MeasUnit.setText(new_mat_type.measure_unit)
        self._refresh_delegate_with_material_type(new_mat_type)
        ans = QtGui.QMessageBox.question(self,
                                         self.client_model.name + u" - " + new_mat_type.material_type_name,
                                         u"Оценить потребление товаров по статистике?",
                                         QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if ans == QtGui.QMessageBox.Yes:
            self._do_estimate_from_statistics()
        else:
            # Заполним табличку данными по умолчанию
            fresh_table = {}
            for mat_i in new_mat_type.materials:
                fresh_table[mat_i] = [1.0]
            self._refresh_table_model_with_new_data(fresh_table)
            self._normalize_probs()

    # general internal methods

    def _get_material_type(self):
        row = self.comboBox_material_type.currentIndex()
        if row>=0:
            # 35 - это роль модели данных
            selected_item = self.comboBox_material_type.itemData(row, 35).toPyObject()
            return selected_item

    # Удобства пользователя
    def _put_volume_down_025(self):
        self._change_volume(-0.25)

    def _put_volume_up_025(self):
        self._change_volume(0.25)

    def _change_volume(self, level):
        old_volume = self._get_cons_volume_mean_value()
        old_freq = self._get_periodicy_expectation_value()
        old_freq_std = self._get_periodicy_stdev_value()
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

    def _do_estimate_from_statistics(self):
        mt = self._get_material_type()
        if mt is None:
            return
        mfd = db_main.estimate_shipment_stats(self.client_model, mt)[0]  #там лист просто возвращается
        self.lineEdit_cons_volume_mean.setText(simple_locale.number2string(mfd["qtty_exp"]))
        self.lineEdit_cons_period_mean.setText(simple_locale.number2string(mfd["timedelta_exp"]))
        if mfd["qtty_exp"] > 0:
            cons_volume_std_prc = round(mfd["qtty_std"] / mfd["qtty_exp"] * 100, 2)
        else:
            cons_volume_std_prc = 0
        self.lineEdit_cons_vol_dev.setText(simple_locale.number2string(cons_volume_std_prc))
        self.lineEdit_cons_period_std.setText(simple_locale.number2string(mfd["timedelta_std"]))
        # Дату либо последняя + дельта, либо сегодня.
        next_order_date = mfd["last_shipment_date"] + datetime.timedelta(days=mfd["timedelta_exp"])
        self.dateEdit_NextExpectedOrder.setDate(qtdate_pack(next_order_date))
        # Табличку обновляем
        dict_for_model = {}
        for mat_i, prob_i in mfd["mat_dist"].return_table():
            dict_for_model[mat_i] = [prob_i]
        if len(dict_for_model) == 0:
            # Не было потрбления
            for mat_i in mt.materials:
                dict_for_model[mat_i] = [1.0]
        self._refresh_table_model_with_new_data(dict_for_model)
        self._normalize_probs()

    # internal data checkers and getters
    def _inp_erh(self,inp,a_message):
        if inp is None:
            QtGui.QMessageBox.information(self,unicode(u"Ошибка ввода"),
                                          unicode(u"Неверно указана графа: ") + a_message)
            self.var_is_correct = False
            return None
        else:
            return inp

    def _get_material_type(self):
        row = self.comboBox_material_type.currentIndex()
        if row>=0:
            # 35 - это роль модели данных (ниже в этом модуле)
            selected_item = self.comboBox_material_type.itemData(row, 35).toPyObject()
            return selected_item

    def _get_cons_volume_mean_value(self):
        try:
            return convert.convert_formated_str_2_float(self.lineEdit_cons_volume_mean.text())
        except ValueError:
            # a_title = unicode(u"Ошибка ввода")
            # a_message = unicode(u"Неверно указан ожидаемый объём потребления")
            # QtGui.QMessageBox.information(self,a_title,a_message)
            self.var_is_correct = False
            return None

    def _get_cons_volume_stdev_value(self):
        try:
            return convert.convert_formated_str_2_float(self.lineEdit_cons_vol_dev.text())
        except ValueError:
            self.var_is_correct = False
            return None

    def _get_periodicy_expectation_value(self):
        try:
            return convert.convert_formated_str_2_float(self.lineEdit_cons_period_mean.text())
        except ValueError:
            self.var_is_correct = False
            return None

    def _get_periodicy_stdev_value(self):
        try:
            return convert.convert_formated_str_2_float(self.lineEdit_cons_period_std.text())
        except ValueError:
            self.var_is_correct = False
            return None

    def _get_are_materials_substitude(self):
        if self.checkBox_are_materials_substitude.checkState() == QtCore.Qt.Checked:
            return True
        elif self.checkBox_are_materials_substitude.checkState() == QtCore.Qt.Unchecked:
            return False

    def _get_is_direct_order(self):
        if self.checkBox_direct_order.checkState() == QtCore.Qt.Checked:
            return True
        elif self.checkBox_direct_order.checkState() == QtCore.Qt.Unchecked:
            return False

    def _get_next_date_prediction(self):
        try:
            return qtdate_unpack(self.dateEdit_NextExpectedOrder.date())
        except ValueError:
            self.var_is_correct = False
            return None


    def showplot(self):
        mat_type = self._get_material_type()
        current_date = datetime.today()

        history = db_main.get_shipments_history(self.client_model, mat_type)
        tmp_lst = []
        for date_bought, qtty_bought in history:
            daysfromstart = (date_bought-current_date).days
            tmp_lst.append([daysfromstart,qtty_bought,0,0])
        history_array = np.array(tmp_lst)

        nd = self._get_next_date_prediction()
        next_event_date = datetime(year=nd.year, month=nd.month, day=nd.day)

        Edt = self._get_periodicy_expectation_value()
        Ev = self._get_cons_volume_mean_value()
        Ddt = self._get_periodicy_stdev_value()
        Dv = self._get_cons_volume_stdev_value()/100. * Ev

        predictions = get_shipments_prediction_areas(Edt, Ev, Ddt, Dv, next_event_date, current_date, 360)

        data = {}
        if len(history_array) > 0:
            alldata = np.concatenate((history_array, predictions), axis=0)
        else:
            alldata = predictions

        data[unicode(mat_type) + u" by " + unicode(self.client_model)] = alldata

        # print data
        wind = None
        wind = PlotViewerDialog(self)
        wind.plot(data, current_date=current_date)
        # wind.plot(data)
        wind.show()