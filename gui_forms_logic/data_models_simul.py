# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui

import datetime
from c_simulation_results_container import iter_dataframe_reports

class gui_mainsim_varlist_model(QtCore.QAbstractListModel):
    def __init__(self,  parent=None):
        QtCore.QAbstractListModel.__init__(self, parent)
        self.my_list = []
        self.update_with_observations()

    def update_with_observations(self):
        self.beginResetModel()
        self.my_list = []
        for nam, rep_i in iter_dataframe_reports():
            self.my_list += [[nam, rep_i]]
        self.endResetModel()

    def rowCount(self, parent):
        return len(self.my_list)

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            return self.my_list[index.row()][0]
        if role == 35:
            return self.my_list[index.row()][1]

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

class gui_testsim_varlist_model(QtCore.QAbstractListModel):
    def __init__(self,  parent=None):
        QtCore.QAbstractListModel.__init__(self, parent)
        self.my_list = []

    def update_with_observations(self, sim_results):
        self.beginResetModel()
        self.my_list = []
        for [obs_name, var_name] in sim_results.get_available_names():
            # Как-то жестоко..
            self.my_list += [[obs_name + " : " + var_name, sim_results.get_dataframe_for_epochvar(obs_name, var_name)]]
        self.endResetModel()

    def rowCount(self, parent):
        return len(self.my_list)

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            return self.my_list[index.row()][0]
        if role == 35:
            return self.my_list[index.row()]

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

class gui_testsimlog_table_model(QtCore.QAbstractTableModel):
    def __init__(self,  parent = None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.logs = []

    def update_logs(self, start_date, log_list):
        self.beginResetModel()
        self.logs = []
        for item_i in log_list:
            real_timestamp = start_date + datetime.timedelta(days=item_i[0])
            sender_name = item_i[1]
            sender_message = item_i[2]
            log_i = [real_timestamp, sender_name, sender_message]
            self.logs += [log_i]
        self.endResetModel()

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                if section == 0:
                    return unicode(u"Дата")
                if section == 1:
                    return unicode(u"Элемент системы")
                if section == 2:
                    return unicode(u"Сообщение")

    def rowCount(self, parent):
        return len(self.logs)

    def columnCount(self, parent):
        return 3

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            if index.column() == 0:
                return unicode(self.logs[row][0].strftime("%W нед %y г"))
            if index.column() == 1:
                return unicode(self.logs[row][1])
            if index.column() == 2:
                return unicode(self.logs[row][2])

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
