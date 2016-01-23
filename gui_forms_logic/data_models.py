# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui

import db_main
import utils

import simple_locale
import convert

from gui_forms_logic.data_model import DynamicTableWidget

unicode_codec = QtCore.QTextCodec.codecForName(simple_locale.ultimate_encoding)

# TODO: make a model based on SQLAlchemy table easy way

class cDataModel_CounterpartyList(QtCore.QAbstractListModel):
    def __init__(self,  parent = None):
        QtCore.QAbstractListModel.__init__(self, parent)
        self._data_rows = []
        self.update_list()

    def update_list(self):
        self.beginResetModel()
        self._data_rows = []
        for agent_i in db_main.get_client_list():
            self._data_rows += [agent_i]
        for agent_i in db_main.get_supplier_list():
            self._data_rows += [agent_i]
        self.endResetModel()

    def rowCount(self, parent):
        return len(self._data_rows)

    def data(self, index, role):
        this_item = self._data_rows[index.row()]
        if role == QtCore.Qt.DisplayRole:
            return unicode(this_item.name)
        if role == QtCore.Qt.ForegroundRole:
            if this_item.discriminator == 'supplier':
                brush = QtGui.QBrush()
                brush.setColor(QtGui.QColor("orange"))
                return brush
            elif this_item.discriminator == 'client':
                brush = QtGui.QBrush()
                brush.setColor(QtGui.QColor("green"))
                return brush
        if role == 35: #Наша роль для передачи данных
            return this_item
        if role == 40: #Роль для поиска элемента в списке (возвращает ключ элемента)
            return this_item.string_key()

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

class cDataModel_CounterpartySpecialList(QtCore.QAbstractListModel):
    # TODO: join two Counterparty models
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

class cDataModel_GeneralMaterialList(QtCore.QAbstractListModel):
    #Может быть группой, может быть номенклатурой
    def __init__(self, type=0, parent=None, do_load=1):
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

class cDataModel_FilteredMaterialList(QtCore.QAbstractListModel):
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


class cDataModel_MatDistTable(QtCore.QAbstractTableModel):
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
                return unicode(simple_locale.number2string(round(self.__probs[row][1], 2)))  #Проценты?
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
                self.__probs.insert(row, [value, old_prob])
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

class cDataModel_MatDistTable2(DynamicTableWidget.TableModel):

    def __init__(self, data, headers=None, parent=None, *args):
        DynamicTableWidget.TableModel.__init__(self, data, headers, parent, *args)
        self.__probs = []
        self.prob_dict = utils.c_random_dict()


class cDataModel_PaymentTermsList(QtCore.QAbstractListModel):
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

class CDataModel_ContactDetailsTable(QtCore.QAbstractTableModel):
    def __init__(self,  parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.__details = []

    def update_data(self, details_list):
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

    def setData(self, index, value, role=QtCore.Qt.EditRole):
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

    def insertNewDetail(self, cont_type, cont_value, is_fixed, parent=QtCore.QModelIndex()):
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

class cDataModel_HashtagList(QtCore.QAbstractListModel):
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