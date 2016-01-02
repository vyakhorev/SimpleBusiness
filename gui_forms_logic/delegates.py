# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui

class gui_DelegateSelectMaterial(QtGui.QStyledItemDelegate):
    """
    A delegate that places a fully functioning QComboBox in every
    cell of the column to which it's applied
    """
    def __init__(self, parent, data_model):
        QtGui.QStyledItemDelegate.__init__(self, parent)
        self.data_model = data_model

    def createEditor(self, parent, option, index):
        mat_cmbx = QtGui.QComboBox(parent)
        mat_cmbx.setModel(self.data_model)
        #TODO: выбрать элемент в создаваемом едиторе. Сложно блин.
        self.connect(mat_cmbx, QtCore.SIGNAL("currentIndexChanged(int)"), self, QtCore.SLOT("currentIndexChanged()"))
        return mat_cmbx

    def setEditorData(self, editor, index):
        #Что останется после выбора
        editor.blockSignals(True)
        #editor.setCurrentIndex(int(index.model().data(index, QtCore.Qt.DisplayRole)))
        editor.setCurrentIndex(int(index.row()))
        editor.blockSignals(False)

    def setModelData(self, editor, model, index):
        model.blockSignals(True)
        row_in_cmbx = editor.currentIndex()
        the_data = editor.itemData(row_in_cmbx, 35).toPyObject() #Материал будет
        model.setData(index, the_data, QtCore.Qt.EditRole)
        model.blockSignals(False)

    @QtCore.pyqtSlot()
    def currentIndexChanged(self):
        self.commitData.emit(self.sender())
