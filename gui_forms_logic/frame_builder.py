# -*- coding: utf-8 -*-
__author__ = 'User'
from PyQt4 import QtCore, QtGui
from custom_qt_objects import GrowingTextBrowser, FlowLayout

COLOR_DEBUG = False
inside_widgets = []

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
        if COLOR_DEBUG:
            self.setStyleSheet("background-color:lightgrey;")

        self.med_title = QtGui.QLabel(unicode(mediator.label))

        # TODO move to Qss
        a_font = QtGui.QFont("Courier", 12)
        a_font.setBold(True)

        self.med_title.setFont(a_font)
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


# TODO make base class for frame
class RecFrame(QtGui.QFrame):
    """
        Frame for concrete record
    """
    # Store activated fields
    active_buttons_field = []

    def __init__(self, mediator, parent = None):
        QtGui.QFrame.__init__(self)
        self.record = None

        self.inside_widgets = []

        # Adjusting Frame bounding sizes
        self.setFrameStyle(QtGui.QFrame.Raised)
        self.setLayout(QtGui.QVBoxLayout())
        #   Margins
        self.layout().setContentsMargins(2, 2, 2, 2)
        self.layout().setSpacing(0)
        #   =========================

        self.setObjectName('Ramka')
        self.setStyleSheet('#Ramka{border: 1px solid grey;}')

        if COLOR_DEBUG:
            self.setStyleSheet("background-color:lightgreen;")

        self.fields_and_html_frame = QtGui.QFrame()
        self.field_and_html_layout = QtGui.QHBoxLayout()

        #   Margins
        self.field_and_html_layout.setContentsMargins(2, 2, 2, 2)
        #   =========================
        if COLOR_DEBUG:
            self.fields_and_html_frame.setStyleSheet("background-color:cyan;")
        # ----------------------------
        # |label value |             |
        # |label value |    Html     |
        # ----------------------------
        if mediator.get_HTML() != "":
            self.html_field = GrowingTextBrowser(self)
            self.html_field.setReadOnly(1)
            self.html_field.setParent(self)

            self.sheet_text = mediator.get_HTML()
            self.html_field.setHtml(self.sheet_text)

            self.field_and_html_layout.addWidget(self.html_field)
            self.html_field.setAlignment(QtCore.Qt.AlignTop)


        self.fields_and_html_frame.setLayout(self.field_and_html_layout)
        self.layout().addWidget(self.fields_and_html_frame)

        self.fields_frame = QtGui.QFrame()
        self.fields_frame_layout = QtGui.QVBoxLayout()
        # self.fields_frame_layout = FlowLayout()


        if COLOR_DEBUG:
            self.fields_frame.setStyleSheet("background-color:pink;")

        #   Margins
        self.fields_frame_layout.setAlignment(QtCore.Qt.AlignTop)
        self.fields_frame_layout.setContentsMargins(1, 1, 1, 1)
        self.fields_frame_layout.setSpacing(0)
        #   =========================

        # |label value |
        # |label value |
        self.fields_frame.setLayout(self.fields_frame_layout)

        for field_i in mediator.iter_fields():
            one_field = QtGui.QWidget()
            one_field_layout = QtGui.QHBoxLayout()
            #   Margins
            one_field_layout.setSpacing(0)
            one_field_layout.setContentsMargins(1, 1, 1, 1)
            #   =========================
            # |label value |
            one_field_label = QtGui.QLabel(unicode(field_i.field_repr))
            one_field_value = QtGui.QLineEdit(unicode(field_i.field_value))
            one_field_layout.addWidget(one_field_label)
            one_field_layout.addWidget(one_field_value)

            one_field_label.setFont(QtGui.QFont("Helvetica", italic=True))

            one_field_label.setMaximumWidth(150)
            one_field_value.setMaximumWidth(150)

            one_field.setLayout(one_field_layout)

            if COLOR_DEBUG:
                one_field.setStyleSheet("background-color:lightblue;")

            temp_widget = QtGui.QWidget()
            # temp_layout = QtGui.QVBoxLayout()
            temp_layout = QtGui.QGridLayout()
            temp_widget.setLayout(temp_layout)
            temp_layout.addWidget(one_field)
            #   Margins
            one_field_layout.setSpacing(0)
            one_field_layout.setContentsMargins(1, 1, 1, 1)
            temp_layout.setSpacing(0)
            temp_layout.setContentsMargins(2, 2, 2, 2)
            #   =========================
            if COLOR_DEBUG:
                temp_widget.setStyleSheet("background-color:red;")
            one_field_layout.setAlignment(QtCore.Qt.AlignTop)
            self.fields_frame_layout.addWidget(one_field)

            self.field_and_html_layout.insertWidget(0, self.fields_frame)

        # buttons layout
        #                                      -
        #                 [edit] [delete]      -
        # --------------------------------------
        self.button_hor_layout = QtGui.QHBoxLayout()
        for button_cal_i in mediator.iter_button_calls():
            button = QtGui.QPushButton(unicode(button_cal_i.label_name))
            button.setMaximumWidth(140)
            button.clicked.connect(button_cal_i)
            self.button_hor_layout.setAlignment(QtCore.Qt.AlignRight)
            self.button_hor_layout.addWidget(button)
            self.buttons_field_widget = QtGui.QWidget()

            #   Margins
            self.button_hor_layout.setContentsMargins(1, 1, 1, 1)
            self.buttons_field_widget.setContentsMargins(1, 1, 1, 1)
            #   =========================
            if COLOR_DEBUG:
                self.buttons_field_widget.setStyleSheet("background-color:orange;")
            self.buttons_field_widget.setLayout(self.button_hor_layout)

            self.buttons_field_widget.setMaximumHeight(0)
            self.layout().addWidget(self.buttons_field_widget)

        # Grabbing all widgets together
        # Its need for setting signals on each child element of Frame
        self.inside_widgets = []
        for ch_i in self.findChildren(QtGui.QWidget):
            self.inside_widgets.append(ch_i)

        for ch_i in self.inside_widgets:
            ch_i.mouseDoubleClickEvent = self.show_buttons

    @classmethod
    def clear_active_buttons(cls):
        cls.active_buttons_field = []

    def show_buttons(self, event):
        """
            Activating buttons field on clicked widget, hiding others
        """
        if len(self.active_buttons_field) > 0:
            for f_i in self.active_buttons_field:
                f_i.setMaximumHeight(0)
                self.active_buttons_field.remove(f_i)

        self.buttons_field_widget.setMaximumHeight(50)
        self.active_buttons_field.append(self.buttons_field_widget)

    # TODO Make this by Qss hover pseudo states
    def enterEvent(self, *args, **kwargs):
        self.setStyleSheet("#Ramka{background-color:lightblue;border: 1px dashed grey;}")

    def leaveEvent(self, *args, **kwargs):
        self.setStyleSheet("#Ramka{background-color:None;border: 1px solid grey;}")