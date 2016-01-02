# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui

import db_main

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
                brush.setColor(QtGui.QColor("red"))
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
