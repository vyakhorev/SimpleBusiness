# -*- coding: utf-8 -*-
__author__ = 'User'
from PyQt4 import QtCore, QtGui


class LabelFrame(QtGui.QFrame):
    """
        Frame for upper labeled colon
    """
    def __init__(self, mediator, parent = None):
        QtGui.QFrame.__init__(self)

        # Adjusting Frame bounding sizes
        self.setFrameStyle(QtGui.QFrame.Raised)
        self.setLayout(QtGui.QHBoxLayout())
        self.layout().setContentsMargins(2, 2, 2, 2)
        self.layout().setSpacing(0)

        self.med_title = QtGui.QLabel(unicode(mediator.label))
        self.layout().addWidget(self.med_title)

        # buttons layout
        self.button_hor_layout = QtGui.QHBoxLayout()
        for button_cal_i in mediator.iter_button_calls():
            button = QtGui.QPushButton(unicode(button_cal_i.label_name))
            button.clicked.connect(button_cal_i)
            button.setMaximumWidth(140)
            self.button_hor_layout.addWidget(button)
            widget = QtGui.QWidget()
            widget.setLayout(self.button_hor_layout)

             # adding buttons to QHBoxLayout
            self.layout().addWidget(widget)


class RecFrame(QtGui.QFrame):
    """
        Frame for concrete record
    """
    # Store activated frames
    active_buttons = []

    def __init__(self, mediator, parent = None):
        QtGui.QFrame.__init__(self)
        self.record = None

        # Adjusting Frame bounding sizes
        self.setFrameStyle(QtGui.QFrame.Raised)
        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setContentsMargins(2, 2, 2, 2)
        self.layout().setSpacing(0)

        self.fields_and_html_frame = QtGui.QFrame()
        self.field_and_html_layout = QtGui.QHBoxLayout()
        # ----------------------------
        # |label value |             |
        # |label value |    Html     |
        # ----------------------------
        if mediator.get_HTML() != "":
            # To make this field nicely resiseble, we can use either
            # QLabel
            # Or something like this:
            # font = textEdit.document().defaultFont()    # or another font if you change it
            # fontMetrics = QtGui.QFontMetrics(font)      # a QFontMetrics based on our font
            # textSize = fontMetrics.size(0, text)
            #
            # textWidth = textSize.width() + 30       # constant may need to be tweaked
            # textHeight = textSize.height() + 30     # constant may need to be tweaked
            #
            # textEdit.setMinimumSize(textWidth, textHeight)  # good if you want to insert this into a layout
            # textEdit.resize(textWidth, textHeight)          # good if you want this to be standalone


            #self.html_field = QtGui.QTextBrowser()

            self.html_field = QtGui.QLabel()
            #self.html_field.setReadOnly(1)
            self.html_field.setWordWrap(True)
            # TODO detect minimum html text height
            # self.html_field.setMinimumHeight(100)
            # self.html_field.setMaximumHeight(150)
            #self.html_field.setHtml(mediator.get_HTML())
            self.html_field.setText(mediator.get_HTML())
            # self.html_field.setHtml('Blah Blah')
            self.field_and_html_layout.addWidget(self.html_field)
            self.html_field.setAlignment(QtCore.Qt.AlignTop)

        self.fields_and_html_frame.setLayout(self.field_and_html_layout)
        self.layout().addWidget(self.fields_and_html_frame)

        self.fields_frame = QtGui.QFrame()
        self.fields_frame_layout = QtGui.QVBoxLayout()
        # self.fields_frame_layout.setAlignment(QtCore.Qt.AlignTop)
        # |label value |
        # |label value |
        self.fields_frame_layout.setSpacing(0)
        self.fields_frame_layout.setContentsMargins(1, 1, 1, 1)
        self.fields_frame.setLayout(self.fields_frame_layout)

        for field_i in mediator.iter_fields():
            one_field = QtGui.QWidget()
            one_field_layout = QtGui.QHBoxLayout()
            one_field_layout.setSpacing(0)
            one_field_layout.setContentsMargins(1, 1, 1, 1)
            # |label value |
            one_field_label = QtGui.QLabel(unicode(field_i.field_repr))
            one_field_value = QtGui.QLineEdit(unicode(field_i.field_value))
            one_field_layout.addWidget(one_field_label)
            one_field_layout.addWidget(one_field_value)

            one_field.setLayout(one_field_layout)

            temp_widget = QtGui.QWidget()
            temp_layout = QtGui.QVBoxLayout()
            temp_widget.setLayout(temp_layout)
            temp_layout.addWidget(one_field)
            one_field_layout.setSpacing(0)
            one_field_layout.setContentsMargins(1, 1, 1, 1)
            one_field_layout.setAlignment(QtCore.Qt.AlignTop)
            self.fields_frame_layout.addWidget(temp_widget)

        self.field_and_html_layout.insertWidget(0, self.fields_frame)
        # self.field_and_html_layout.setAlignment(QtCore.Qt.AlignTop)

        # buttons layout
        self.button_hor_layout = QtGui.QHBoxLayout()
        for button_cal_i in mediator.iter_button_calls():
            button = QtGui.QPushButton(unicode(button_cal_i.label_name))
            button.setMaximumWidth(140)
            button.clicked.connect(button_cal_i)
            self.button_hor_layout.setAlignment(QtCore.Qt.AlignRight)
            self.button_hor_layout.addWidget(button)
            widget = QtGui.QWidget()
            widget.setLayout(self.button_hor_layout)

            self.layout().addWidget(widget)
