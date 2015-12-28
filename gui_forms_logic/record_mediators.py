# -*- coding: utf-8 -*-

"""
    Класс представляет собой обёртку вызовов и полей одной или нескольких записей базы данных.
    Используется для представления записи / записей в GUI.
    Для действий над записями интерактивного рода надо сделать метод в главном окне, передать
    его название и ссылку на главное окно (parent_window) медиатору.
"""

import db_main
import collections

class cMediator(object):
    pass

class cMedSellPrice(cMediator):
    rec_type = "SellPrice"

    def __init__(self, parent_window, record = None):
        '''
        Args:
            parent_window: Вызывающее окно (для интерактивности)
            record: Запись базы данных
        '''
        self.parent_window = parent_window
        self.fields = collections.OrderedDict()
        self.button_calls = collections.OrderedDict()
        self.record = None
        if not(record is None):
            self.set_record(record)

    def set_record(self, record):
        self.record = record
        self._reset_fields()

    def _reset_fields(self):
        '''
        Заполняет поля по объекту
        '''
        if self.record is None:
            raise BaseException("Unable to use _reset_fields() with no active record!")
        self.fields['Price'] = cField(self.record.price_value, 'Price', u'Цена', 'float')
        if self.record.is_for_group:
            item_name = unicode(self.record.material_type)
        else:
            item_name = unicode(self.record.material)
        self.fields['Item_name'] = cField(item_name, 'Item_name', u'Товар', 'string')

    def add_call(self, method_name, label_name, *args, **kwargs):
        '''
        Запоминает название метода родительского окна (или объекта - тут не обязательно Qt),
        помогая привязать его к кнопке автоматом.
        Потом можно запустить cCall как do_call (или self.do_call(method_name) )
        Args:
            method_name: имя метода в родительском окне (должно существовать на момент вызова)
            label_name: как отобразить на форме
            *args: что передать вызову
            **kwargs: что передать вызову
        '''
        if not hasattr(self.parent_window, method_name):
            raise BaseException('Method name ' + method_name + ' is not found in self.parent_window')
        self.button_calls[method_name] = cCall(self.parent_window, method_name, label_name, args, kwargs)

    def do_call(self, method_name):
        '''
        Вызывает выполнение обработки (метода родительской формы) по имени. То же самое,
        что и по итератору получить, а потом вызвать.
        Args:
            method_name: имя метода родительской формы
        '''
        self.button_calls[method_name].do_call()

    def iter_fields(self):
        for f_i in self.fields.itervalues():
            yield f_i

    def iter_button_calls(self):
        for g_i in self.button_calls.itervalues():
            yield g_i

class cField(object):
    def __init__(self, field_value, field_name, field_repr, field_type=""):
        # TODO: check types here, not during construction
        # Maybe I need to give links to fields instead of cloning..
        # Anyway, this class may help for input check (if we start editing
        # things right on the widget.. one day..)
        self.field_value = field_value
        self.field_type = field_type
        self.field_name = field_name
        self.field_repr = field_repr

    def __repr__(self):
        return "field: " + self.field_name + " = " + str(self.field_value)

class cCall(object):
    '''
    Отложенный вызов метода (вместе с лейблом кнопки для gui)
    '''
    def __init__(self, instance, method_name, label_name, args, kwargs):
        self.instance = instance
        self.method_name = method_name
        self.label_name = label_name
        self.args = args
        self.kwargs = kwargs

    def __repr__(self):
        return "a call " + str(self.method_name) + " for " + str(self.instance)

    def do_call(self):
        getattr(self.instance, self.method_name)(*self.args, **self.kwargs)