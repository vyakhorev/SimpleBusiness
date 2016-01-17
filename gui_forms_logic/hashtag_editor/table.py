# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore

class ui_EditorHtmlTableSettings(QtGui.QDialog):
    def __init__(self,parent, text_editor):
        QtGui.QDialog.__init__(self, parent)
        self.parent = parent
        self.initUI()
        self.text_editor = text_editor
 
    def initUI(self):
        # Rows
        rowsLabel = QtGui.QLabel(u"Рядов",self)
        self.rows = QtGui.QSpinBox(self)
        # Columns
        colsLabel = QtGui.QLabel(u"Столбцов",self)
        self.cols = QtGui.QSpinBox(self)
        # # Cell spacing (distance between cells)
        # spaceLabel = QtGui.QLabel("Cell spacing",self)
        # self.space = QtGui.QSpinBox(self)
        # # Cell padding (distance between cell and inner text)
        # padLabel = QtGui.QLabel("Cell padding",self)
        # self.pad = QtGui.QSpinBox(self)
        # self.pad.setValue(10)
        # Button
        insertButton = QtGui.QPushButton(u"Вставить",self)
        insertButton.clicked.connect(self.insert)
        # Layout
        layout = QtGui.QGridLayout()
        layout.addWidget(rowsLabel,0,0)
        layout.addWidget(self.rows,0,1)
        layout.addWidget(colsLabel,1,0)
        layout.addWidget(self.cols,1,1)
        #layout.addWidget(padLabel,2,0)
        #layout.addWidget(self.pad,2,1)
        #layout.addWidget(spaceLabel,3,0)
        #layout.addWidget(self.space,3,1)
        layout.addWidget(insertButton,2,0,1,2)
        self.setWindowTitle(u"Вставка таблицы")
        self.setGeometry(300,300,200,100)
        self.setLayout(layout)

    def insert(self):
        cursor = self.text_editor.textCursor()
        # Get the configurations
        rows = self.rows.value()
        cols = self.cols.value()
        if not rows or not cols:
            popup = QtGui.QMessageBox(QtGui.QMessageBox.Warning,u"Ошибка", u"Все числа должны быть больше нуля!",
                                      QtGui.QMessageBox.Ok,self)
            popup.show()

        else:
            #padding = self.pad.value()
            #space = self.space.value()
            padding = 10
            space = 0.1
            # Set the padding and spacing
            fmt = QtGui.QTextTableFormat()
            fmt.setCellPadding(padding)
            fmt.setCellSpacing(space)
            # Inser the new table
            cursor.insertTable(rows,cols,fmt)
            self.close()
