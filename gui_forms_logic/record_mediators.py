# -*- coding: utf-8 -*-

"""
    Класс представляет собой обёртку вызовов и полей одной или нескольких записей базы данных.
    Используется для представления записи / записей в GUI.
    Для действий над записями интерактивного рода надо сделать метод в главном окне, передать
    его название и ссылку на главное окно (parent_window) медиатору.
"""

import collections


############
# Basic
############

class cSimpleMediator(object):
    def __init__(self, parent_window):
        '''
        Args:
            parent_window: Вызывающее окно (для интерактивности)

        self.fields: поля для отображения виджета
        self.button_calls: отложенные вызовы (их можно потом вызвать)
        '''
        self.parent_window = parent_window
        self.label = ""
        self.html_text = ""
        self.fields = collections.OrderedDict()
        self.button_calls = collections.OrderedDict()

    def set_label(self, label):
        self.label = label

    def get_HTML(self):
        return self.html_text

    def add_field(self, field_value, field_name, field_repr, field_type=""):
        self.fields[field_name] = cField(field_value, field_name, field_repr, field_type)

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

class cAbstRecordMediator(cSimpleMediator):
    def __init__(self, parent_window, record=None):
        '''
        Args:
            parent_window: Вызывающее окно (для интерактивности)
            record: Запись базы данных
        '''
        super(cAbstRecordMediator, self).__init__(parent_window)
        self.record = None
        if not(record is None):
            self.set_record(record)

    def set_record(self, record):
        self.record = record
        self._reset_fields()

    def _reset_fields(self):
        '''
        Перезаполняет поля по объекту
        '''
        if self.record is None:
            raise BaseException("Unable to use _reset_fields() with no active record!")
        self._build_HTML()

    def _build_HTML(self):
        pass

############
# Records
############

class cMedPrice(cAbstRecordMediator):
    # HTML нет
    def _reset_fields(self):
        super(cMedPrice, self)._reset_fields()
        self.add_field(self.record.price_value, 'price_value', u'Цена', 'float')
        if self.record.is_for_group:
            item_name = unicode(self.record.material_type)
        else:
            item_name = unicode(self.record.material)
        self.add_field(item_name, 'item_name', u'Товар', 'string')

class cMedMatFlow(cAbstRecordMediator):
    def _reset_fields(self):
        '''
        Заполняет поля по объекту (перетирает, если уже что-то было)
        '''
        super(cMedMatFlow, self)._reset_fields()
        self.add_field(self.record.material_type, 'material_type', u'Товар', 'string')
        self.add_field(self.record.stats_mean_volume, 'stats_mean_volume', u'Объем потребления', 'float')
        self.add_field(self.record.stats_mean_timedelta, 'stats_mean_timedelta', u'Частота потребления', 'float')

    def _build_HTML(self):
        s = u'Распределение <b>вероятностей</b>:<br>'
        for md_i in self.record.material_dist:
            s += md_i.material.material_name + u' : ' + unicode(md_i.choice_prob) + '<br>'
        self.html_text = s

class cMedContact(cAbstRecordMediator):
    # Полей нет
    def _build_HTML(self):
        s = u""
        if self.record.is_person:
            s += u"<b>" + unicode(self.record.name) + u"</b>" + u", " + unicode(self.record.job) + u"<br>"
        else:
            s += u"<b>" + u"общий контакт" + u"</b>" + u"<br>"
        if self.record.additional_info is not None:
            s += self.record.additional_info + u"<br>"
        for d_i in self.record.details:
            s += unicode(d_i) + u"<br>"
        self.html_text = s

############
# Interface
############

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

    def __call__(self, *args, **kwargs):
        # А зафиг мне тут арги и кварги?
        self.do_call()

    def get_call_label(self):
        return self.label_name

    def do_call(self):
        getattr(self.instance, self.method_name)(*self.args, **self.kwargs)