__author__ = 'User'

from PyQt4 import QtCore, QtGui
import sys
from db_mock import db_fake, db_filling_up

######################
# Model
######################


class ListModel(QtCore.QAbstractListModel):
    """
        :param datain: 1-dim list of items
    """
    def __init__(self, datain, parent=None, *args):
        super(ListModel, self).__init__()
        self.listdata = datain

    @property
    def listdata(self):
        return self._listdata

    @listdata.setter
    def listdata(self, value):
        if not isinstance(value, list):
            raise ValueError('wrong input data {}, ,must be list'.format(value))
        elif isinstance(value[0], list):
            raise ValueError('list {} must be 1-dimensional'.format(value))
        else:
            self._listdata = value

    def rowCount(self, *args, **kwargs):
        return len(self.listdata)

    def data(self, index, role=QtCore.Qt.DisplayRole):

        if index.isValid() and role == QtCore.Qt.DisplayRole:
            # print 'DisplayRole for {}'.format(self)
            return self.listdata[index.row()].__repr__()

        elif role == QtCore.Qt.UserRole:
            return self.listdata[index.row()]
        else:
            return QtCore.QVariant()


class TableModel(QtCore.QAbstractTableModel):
    """
        :param data: dictionary with structure {key1 : [val_1, ...  val_i], key2 : [val_1, ... val_i]}, ... key_i : [...]}
    """

    def __init__(self, data, headers=None, parent=None, *args):
        super(TableModel, self).__init__()
        self.mydata = data
        self.headers = headers
        self.mapped_list_fr_dict = []
        # TODO make sure any kind of input data could be mapped in [[] .. []] struct
        for k, v in self.mydata.iteritems():
            self.mapped_list_fr_dict.append([k, v])

    @property
    def mydata(self):
        return self._mydata

    @mydata.setter
    def mydata(self, value):
        if not isinstance(value, dict):
            raise ValueError('wrong input data {} ,must be dict'.format(value))
        else:
            self._mydata = value

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                for num, header in enumerate(self.headers):
                    if section == num:
                        return self.headers[num]

    def rowCount(self, *args, **kwargs):
        if isinstance(self.mydata, list):
            return len(self.mydata[0])
        if isinstance(self.mydata, dict):
            return len(self.mydata)

    def columnCount(self, *args, **kwargs):
        if isinstance(self.mydata, list):
            return len(self.mydata)
        if isinstance(self.mydata, dict):
            return len(self.mydata.values()[0])+1

    def data(self, index, role=QtCore.Qt.DisplayRole):
        row_i = index.row()
        col_i = index.column()

        if role == QtCore.Qt.DisplayRole:
            if col_i == 0:
                return self.mapped_list_fr_dict[row_i][col_i].__repr__()
            if col_i == 1:
                return self.mapped_list_fr_dict[row_i][col_i][0]
            if col_i == 2:
                return self.mapped_list_fr_dict[row_i][col_i-1][1]

    def setData(self, index, value, role=QtCore.Qt.DisplayRole):
        row_i = index.row()
        col_i = index.column()

        if role == QtCore.Qt.DisplayRole:
            if col_i == 0:
                self.mapped_list_fr_dict[row_i][col_i] = value.toPyObject()
                self.dataChanged.emit(index, index)
            elif col_i == 1:
                print value.toPyObject()
                self.mapped_list_fr_dict[row_i][col_i][0] = value.toPyObject()
                self.dataChanged.emit(index, index)
            elif col_i == 2:
                self.mapped_list_fr_dict[row_i][col_i-1][1] = value.toPyObject()
                self.dataChanged.emit(index, index)
            else:
                return QtCore.QVariant()

    def flags(self, index):
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable


class ComboDelegate(QtGui.QItemDelegate):
    """
        :param datamodel_with_col_list: list like [Abstract Data Model, int] or
                                                  [ [Abstract Data Model 1, int1], ... [Abstract Data Model i, inti] ]
        :param acolumn: int, which column this delegate is for
    """
    # TODO check if columns more than table model columns
    def __init__(self, datamodel_with_col_list, parent=None):
        super(ComboDelegate, self).__init__()
        self.data_col_list = datamodel_with_col_list

        if not isinstance(self.data_col_list[0], list):
            self.datamodel, self.acolumn = self.data_col_list

    def createEditor(self, parent, option, index):
        """
            Making inline widget for delegate
            checking for each column
        """
        if isinstance(self.data_col_list[0], list):
            for pair in self.data_col_list:
                print self.data_col_list
                if index.column() == pair[1]:
                    editor = QtGui.QComboBox(parent)
                    editor.setModel(pair[0])
                    return editor

        else:
            if index.column() == self.data_col_list[1]:
                editor = QtGui.QComboBox(parent)
                editor.setModel(self.data_col_list[0])
                return editor

        '''
        if self.acolumn is None:
            editor = QtGui.QComboBox(parent)
            editor.setModel(self.datamodel)
            return editor

        if index.column() == self.acolumn:
            editor = QtGui.QComboBox(parent)
            editor.setModel(self.datamodel)
            return editor

        if index.column() == 2:
            editor = QtGui.QSpinBox(parent)
            return editor
        # return
        '''

    def setEditorData(self, editor, index):
        """
            Called when double-clicking field
        """
        choice = index.model().data(index, QtCore.Qt.DisplayRole)
        pos = editor.findText(str(choice), QtCore.Qt.MatchFixedString)
        editor.setCurrentIndex(pos)

    def setModelData(self, editor, model, index):
        """
            Called when quit from Combobox
        """
        # grab data from selected position
        pos = editor.findText(editor.currentText(), QtCore.Qt.MatchFixedString)
        print editor.currentText()
        curData = editor.itemData(pos)
        print curData.toPyObject()
        model.setData(index, curData)


######################
# Main wrapper
######################


def add_tableview_to(window, model, delegates=None, layout=None):
    """
        Adding tableView on any QWidget window
        :param window: QWidget cls instance, wich we'll decorate
        :param model: QAbstractTableModel cls instance
        :param delegates: QItemDelegate cls instance, if exist make delegates for column
        :param layout: if exist, adding table to it

        :return: window, decorated window
    """
    table = QtGui.QTableView()
    table.setModel(model)
    if layout:
        layout.addWidget(table)
    else:
        window.layout().addWidget(table)

    if delegates is not None:
        if isinstance(delegates[0], list):
            list_of_props = delegates
            combodelegate = ComboDelegate(delegates, window)
            table.setItemDelegate(combodelegate)
        else:
            list_of_props, column = delegates
            combodelegate = ComboDelegate(delegates, window)
            table.setItemDelegate(combodelegate)

    # resizing columns

    table.setVisible(False)
    table.resizeColumnsToContents()
    table.setVisible(True)
    return window

######################
# Test Cases
######################


class MyWindow(QtGui.QWidget):

    def __init__(self):
        super(MyWindow, self).__init__()
        self.list_of_props = []
        self.list_of_props_col = 0
        self.all_props = []

        self.build_ui()

    def set_combo_props(self, list, column=None):
        self.list_of_props = list
        self.column = column
        self.combodelegate = ComboDelegate([self.list_of_props, self.column], self)
        self.table.setItemDelegate(self.combodelegate)

    def set_table(self, a_table):
        if not isinstance(a_table, TableModel):
            raise ValueError('wrong input data {} ,must be TableModel instance'.format(a_table))

        self.tableModel = a_table
        self.table = QtGui.QTableView()
        self.table.setModel(self.tableModel)

        self.layout().addWidget(self.table)

    def build_ui(self):
        self.setLayout(QtGui.QHBoxLayout())

        # self.layout().addWidget(self.table)


class MyWindow2(QtGui.QWidget):
    """ Some dlg window """
    def __init__(self):
        super(MyWindow2, self).__init__()
        self.build_ui()

    def build_ui(self):
        self.resize(500, 500)
        self.setLayout(QtGui.QHBoxLayout())


class MyWindow3(QtGui.QWidget):
    """ Some dlg window """
    def __init__(self):
        super(MyWindow3, self).__init__()
        self.build_ui()

    def build_ui(self):
        self.resize(500, 500)
        self.setLayout(QtGui.QHBoxLayout())


def main():
    # setting up data
    fake_database = db_fake()
    names = ['VVNG-ls', 'VVNG-pk', 'RST-pmn', 'SpecsuperCableLongNAme']
    db_filling_up(fake_database, cables=names)
    # result
    print fake_database.table_fin

    # setting up table model
    headers = ['Mark', 'Type', 'Diameter']
    some_table = TableModel(fake_database.table_fin, headers)

    # generating labels from existing some_table keys
    labels = fake_database.table_fin.keys()
    some_cable_list = ListModel(labels)

    # build ui
    global app
    app = QtGui.QApplication(sys.argv)

    # Test case #1
    w = MyWindow()
    w.set_table(some_table)
    w.set_combo_props(some_cable_list, 0)
    w.show()

    # Test case #2
    w2 = MyWindow2()
    listdelegate = [some_cable_list, 0]
    newW = add_tableview_to(w2, some_table, listdelegate )
    newW.setDisabled(True)
    w2.show()

    # Test case #4
    w4 = MyWindow2()
    listdelegate = [some_cable_list, 0]
    additional_list = ListModel(['bukvoed', 'supoed', 'hinkali'])
    additional_list2 = ListModel(['12mm', '14mm', '26mm'])
    listdelegate2 = [additional_list, 1]
    listdelegate3 = [additional_list2, 2]
    newW = add_tableview_to(w4, some_table, [listdelegate, listdelegate2, listdelegate3])
    w4.show()

    # Test case #3
    w3 = MyWindow3()
    w3.layout().addWidget(QtGui.QPushButton('Hello world'))
    w3.layout().addWidget(QtGui.QLabel('Greeter '))

    new_layout = QtGui.QHBoxLayout()
    some_widget = QtGui.QWidget()
    some_widget.setLayout(new_layout)
    w3.layout().addWidget(some_widget)

    listdelegate = [some_cable_list, 0]
    newW = add_tableview_to(w3, some_table, listdelegate, new_layout)
    w3.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()