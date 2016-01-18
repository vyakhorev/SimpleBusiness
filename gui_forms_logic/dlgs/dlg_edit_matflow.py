# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui

import simple_locale
import utils
import db_main
import convert

from ui.ui_Dialog_EditMatFlow import Ui_Dialog_EditMatFlow
from gui_forms_logic.data_models import cDataModel_GeneralMaterialList, cDataModel_MatDistTable, \
    cDataModel_FilteredMaterialList, cDataModel_MatDistTable2
from gui_forms_logic.delegates import gui_DelegateSelectMaterial
from gui_forms_logic.data_model import DynamicTableWidget

class gui_Dialog_EditMatFlow(QtGui.QDialog, Ui_Dialog_EditMatFlow):
    def __init__(self, parent=None):
        super(gui_Dialog_EditMatFlow, self).__init__(parent)
        self.setupUi(self) #Метод от QtDesigner
        self.my_mf_entity = None
        self.my_mode = 0   #1 - edit, 0 - new
        self.var_is_correct = False
        self.general_materials_model = cDataModel_GeneralMaterialList()
        self.general_materials_model.switch_to_material_types()
        self.comboBox_material_type.setModel(self.general_materials_model)
        self.matdist_model = cDataModel_MatDistTable()
        self.tableView_materials_and_probs.setModel(self.matdist_model)
        self.cmbx_in_table_model = cDataModel_FilteredMaterialList(parent=self, do_update=0)
        # self.tableView_materials_and_probs.setItemDelegateForColumn(0, gui_DelegateSelectMaterial(self, self.cmbx_in_table_model))
        self.connect(self.pushButton_EstimateStatistics, QtCore.SIGNAL("clicked()"), self.reestimate_from_statistics)
        self.connect(self.pushButton_normalize_probs, QtCore.SIGNAL("clicked()"), self.matdist_model.normalize_probs)
        self.connect(self.comboBox_material_type, QtCore.SIGNAL("currentIndexChanged(int)"), self.material_type_selected)
        self.connect(self.pushButton_add_material, QtCore.SIGNAL("clicked()"), self.add_material)
        self.connect(self.pushButton_delete_material, QtCore.SIGNAL("clicked()"), self.remove_material)
        self.connect(self.pushButton_down_025, QtCore.SIGNAL("clicked()"), self.put_volume_down_025)
        self.connect(self.pushButton_up_025, QtCore.SIGNAL("clicked()"), self.put_volume_up_025)
        #TODO: add table with delegates to layout

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

        print('rows')
        self.material_column = {}
        self.material_list = []

        if not(self.my_mf_entity is None):
            # Here is the list to fill the rows (data for table)
            for md_i in self.my_mf_entity.material_dist:
                self.material_column[md_i.material] = [md_i.choice_prob]
                # print(unicode(md_i.material) + " " + str(md_i.choice_prob))
            # Here is the list to fill the combobox
            # material_group is selected in comboBox_material_type
            material_group = self.my_mf_entity.material_type
            # So here is the list for combobox in the table:
            for mat_i in material_group.materials:
                self.material_list.append(mat_i)
                # print(unicode(mat_i))

            print self.material_column
            print self.material_list

            headers = [unicode('Товар'), unicode('Вероятность закупки')]
            # self.matflow_tablemodel = DynamicTableWidget.TableModel(self.material_column, headers)
            self.matflow_tablemodel = cDataModel_MatDistTable2(self.material_column, headers)
            self.probs_column = DynamicTableWidget.ListModel(self.material_list)
            self.probs_column_delegate = [self.probs_column, 0]

            DynamicTableWidget.add_tableview_to(self, self.matflow_tablemodel,
                                                delegates=self.probs_column_delegate,
                                                tableview=self.tableView_materials_and_probs)


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
            # TODO: here I need probs in a nice way
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
