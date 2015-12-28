# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui

import db_main

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