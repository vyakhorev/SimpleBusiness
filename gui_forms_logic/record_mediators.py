# -*- coding: utf-8 -*-

"""
    Класс представляет собой обёртку вызовов и полей одной или нескольких записей базы данных.
    Используется для представления записи / записей в GUI.
    Для действий над записями интерактивного рода надо сделать метод в главном окне, передать
    его название и ссылку на главное окно (parent_window) медиатору.
"""

import db_main

class cMediator(object):
    pass

class cMedSellPrice(cMediator):
    rec_type = "SellPrice"

    def __init__(self, parent_window, record = None):
        self.parent_window = parent_window
        self.record = None
        if not(record is None):
            self.set_record(record)
        self.fields = []
        self.button_calls = []

    def set_record(self, record):
        self.record = record
        self.fields += [cField(self.record.price_value,'float')]
        if self.record.is_for_group:
            item_name = unicode(self.record.material_type)
        else:
            item_name = unicode(self.record.material)
        self.fields += [cField(item_name,'string')]

    def iter_fields(self):



    def iter_button_calls(self):


class cField(object):
    def __init__(self, field_value, field_type):
        self.field_value = field_value
        self.field_type = field_type