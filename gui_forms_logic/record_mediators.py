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
        self.gui_key = None
        self.color_warning = '' # '' - OK, 'warn' - yellow, 'alert' - red

    def get_warning_mark(self):
        return self.color_warning

    def get_key(self):
        return self.gui_key

    def set_key(self, some_key):
        self.gui_key = some_key

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
        self.set_key(self.record.string_key())
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

    def _reset_fields(self):
        super(cMedPrice, self)._reset_fields()
        price_value = unicode(self.record.price_value) + " " + unicode(self.record.payterm.ccy_quote)

        if self.record.is_for_group:
            item_name = unicode(self.record.material_type)
            price_value += " / " + self.record.material_type.measure_unit
        else:
            item_name = unicode(self.record.material)
            price_value += " / " + self.record.material.measure_unit

        self.add_field(item_name, 'item_name', u'Товар', 'string')
        self.add_field(price_value, 'price_value', u'Цена', 'string')

    def _build_HTML(self):
        # Важные условия - со склада ли цена или нет
        delivery_terms = u''
        if self.record.discriminator == 'sell_price':
            if self.record.is_per_order_only:
                delivery_terms += u'Только <b>под заказ</b>'
            else:
                delivery_terms += u'Для срочных заказов <b>со склада</b>'
        elif self.record.discriminator == 'buy_price':
            delivery_terms += u'<b>' + self.record.incoterms_place + u'</b>'
            if self.record.is_only_for_sp_client:
                delivery_terms += u' только для <b>' + unicode(self.record.for_client) + u'</b>'

        # Условия платежа
        payterm = self.record.payterm
        if payterm.ccy_quote <> payterm.ccy_pay:
            ccy = u"%s (у.е.)"%(payterm.ccy_quote)
            if payterm.fixation_at_shipment:
                ccy += u" фиксация при отгрузке"
            else:
                ccy += u" курс по оплате"
        else:
            ccy = u"%s"%(payterm.ccy_quote)
        prepaym = ""
        for t, p in payterm.payterm_stages.get_prepayments():
            if t < 0:
                prepaym += u"аванс %d%%; "%(int(p))
            elif t == 0:
                prepaym += u"предоплата %d%%; "%(int(p))
        postpaym = ""
        for t, p in payterm.payterm_stages.get_postpayments():
            prepaym += u"оплата %d%% через %d дней; "%(int(p), int(t))
        payterm_desc = u"Расчеты в %s; %s %s"%(ccy, prepaym, postpaym)

        if self.record.is_agent_scheme:
            payterm_desc = u'<b>Агентская</b> схема, ' + payterm_desc

        # Неформальные условия
        nonformal = ""
        if not(self.record.nonformal_conditions is None):
            nonformal = self.record.nonformal_conditions

        self.html_text = delivery_terms + u"<br>" + payterm_desc + u"<br>" + nonformal

class cMedMatFlow(cAbstRecordMediator):
    def _reset_fields(self):
        '''
        Заполняет поля по объекту (перетирает, если уже что-то было)
        '''
        super(cMedMatFlow, self)._reset_fields()
        if self.record.stats_mean_volume == 0:
            return

        cons_vol = str(round(self.record.stats_mean_volume,0)) + u' ' + self.record.material_type.measure_unit
        cons_vol += u' +/-' + str(round(self.record.stats_std_volume/100.0, 0))
        cons_freq = u'каждые ' + str(round(self.record.stats_mean_timedelta,0)) + u' дней'
        cons_freq += u' +/-' + str(round(self.record.stats_std_timedelta, 0))

        self.add_field(self.record.material_type, 'material_type', u'Товар', 'string')
        self.add_field(cons_vol, 'stats_mean_volume', u'Объем потребления', 'string')
        self.add_field(cons_freq, 'stats_mean_timedelta', u'Частота потребления', 'string')

    def _build_HTML(self):
        s = u''
        if self.record.stats_mean_volume == 0:
            s += unicode(self.record.material_type) + u' - поставки прекращены'
            self.html_text = s
            return

        if not(self.record.next_expected_shipment_date is None):
            next_date = self.record.next_expected_shipment_date
            s += u'Следующий заказ ожидается (дата отгрузки)' + next_date.strftime('%d %b %y')
        else:
            s += u'Дата ожидаемой отгрузки не задана'

        s+= u'<br>'

        if not(self.record.last_shipment_date is None):
            s+= u'Дата последней отгрузки ' + self.record.last_shipment_date.strftime('%d %b %y')
            s+= u'<br>'

        if self.record.economy_orders_share == 1.0:
            s+= u'Только <b>под заказ</b>'
        elif self.record.economy_orders_share == 0.0:
            s+= u'Только <b>со склада</b>'
        elif self.record.economy_orders_share is None:
            pass
        else:
            econ_shar = self.record.economy_orders_share*100.
            wh_shar = 100. - econ_shar
            s+= u'Часть заказов <b>со склада</b> (%.0f%%), остальное <b>напрямую</b> (%.0f%%)' % (wh_shar, econ_shar)

        self.html_text = s

class cMedSalesLead(cAbstRecordMediator):
    def _reset_fields(self):
        '''
        Заполняет поля по объекту (перетирает, если уже что-то было)
        '''
        super(cMedSalesLead, self)._reset_fields()
        self.add_field(self.record.material_type, 'material_type', u'Товар', 'string')
        self.add_field(self.record.expected_qtty, 'expected_qtty', u'Ожидаемый объём', 'float')
        self.add_field(self.record.expected_timedelta, 'expected_timedelta', u'Ожидаемая частота', 'float')

    def _build_HTML(self):
        s = u'Вероятность успеха: <b>' + str(self.record.success_prob) + u'</b><br>'
        s+= u'Уверенность: <b>' + str(self.record.sure_level) + u'</b><br>'
        s+= u'Начало продаж: <b>' + self.record.expected_start_date_from.strftime('%d %b %y') + u" - "
        s+= self.record.expected_start_date_till.strftime('%d %b %y') + u'</b><br>'
        if self.record.instock_promise:
            s+= u'Обещаем держать на складе'
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

class cMedKnBaseRecord(cAbstRecordMediator):
    # Полей нет
    def _build_HTML(self):
        s = u""
        s += self.record.date_added.strftime('%d %b %y') + u" <u>" + self.record.headline + u'</u><br>'
        s += u'<i>' + self.record.hashtags_string + u'</i><br>'
        s += self.record.long_html_text
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