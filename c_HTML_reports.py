# -*- coding: utf-8 -*-

"""
Created on Thu May 29 10:40:16 2014

Модуль HTML-отчетов для отображения разных штук в интерфейсе и в печатных отчетах
Начальные условия, результаты симуляций.

Играюсь с фабрикой. Так можно сделать и общий отчет по всем объектам гибко..

Вроде намудрил, а вроде, и ничего лишнего, и украсить можно легко..

@author: Алексей
"""

import Philippe_HTML  #Построитель табличек найденный вы интернете
import pandas
import simple_locale
import utils


class c_report_filler():
    #Даем сюда объекты, получаем заполненный и готовый к работе инстанс c_base_HTML_report
    def __init__(self):
        #На соответствие справочнику проверяеются все объекты, добавленные сюды
        self.wrappers = [c_wh_wrapper, c_bank_account_wrapper, c_simul_dataframe_wrapper]  #Здесь у нас классы
        self.wrappers += [c_client_model_wrapper, c_supplier_model_wrapper, c_proj_cl_ord_wrapper, c_proj_supp_ord_wrapper]
        self.wrappers += [c_step_payment_in_wrapper, c_step_payment_out_wrapper]
        self.wrappers += [c_step_shipment_in_wrapper, c_step_shipment_out_wrapper]
        self.wrappers += [c_crm_hashtag_wrapper, c_crm_contact_wrapper]

    def __get_wrapper(self, an_object):
        #Возвращает инстанс
        i = 0
        wr_i = self.wrappers[i]
        a_wrapper = wr_i()
        while not(a_wrapper.check_comp(an_object)):
            i += 1
            a_wrapper = None #Раз в цикле, то wraper оказался бесполезным
            if i>=len(self.wrappers):
                wr_i = c_none_wrapper  #Вернет всегда 1 на проверке выше
                a_wrapper = wr_i()
            else:
                wr_i = self.wrappers[i]
                a_wrapper = wr_i()
        a_wrapper.set_object(an_object)
        return a_wrapper

    def get_report_for_object(self, *args):
        #На входе - набор объектов в порядке очередности отображения
        #На выходе - инстанс репорта c_base_HTML_report с методом get_HTML_report
        new_report = c_base_HTML_report()
        for obj_i in args:
            if obj_i.__class__ == list or obj_i.__class__ == set or obj_i.__class__ == tuple:     #Чтобы листы и наборы можно было передавать
                for obj_j in obj_i:                         #Не делаю проверку на итерируемость специально - вдруг дадут итерируемый спец. объект?..
                    wr_i = self.__get_wrapper(obj_j)
                    new_report.add_report_piece(wr_i)
            else:
                wr_i = self.__get_wrapper(obj_i)
                new_report.add_report_piece(wr_i)
        return new_report

class c_base_HTML_report():
    #Позволяет сделать репорт сразу по нескольким объектам - фасад, так сказать
    def __init__(self):
        self.reports = set()  #Wrapers - ниже

    def add_report_piece(self, rep_i):
        #Отчет просто последовательно исполняет rep_i
        #Критерии ниже достаточны для работы класса:
        if hasattr(rep_i,"get_html") and hasattr(rep_i,"get_status"):
            self.reports.add(rep_i)
        else:
            #Делаем пустой wrapper с текстом ошибки
            empty_wr = c_none_wrapper()
            empty_wr.set_object(rep_i)
            empty_wr.add_message("Error - not a wrapper")
            self.reports.add(empty_wr)

    def get_name(self):
        #Вот это бредовенько
        s = ""
        for r_i in self.reports:
            s += r_i.get_name()
        return s

    def get_html(self):
        #Самый главный метод - построение отчета.
        HTML_report = ""
        for rep_i in self.reports:
            HTML_report += rep_i.get_html()
            HTML_report += "<br><br>"
        return HTML_report

    def get_dataframe_to_plot(self):
        #Не всегда оно есть
        df_list =[]
        var_names = []
        for rep_i in self.reports:
            if hasattr(rep_i, "get_dataframe_to_plot"):
                df_list.append(rep_i.get_dataframe_to_plot())
                var_names.append(rep_i.get_name())
        df = pandas.concat(df_list, axis=1, join='outer')
#        df.columns = var_names
        return df


#Форматирование
def table_to_HTML_decorator(fn):
    #Делает из таблиц(ы) HTML-текст. Учитывая, что есть
    #модуль хороший, декоратор лишь доп. красоту наводить может
    def decorated(*args, **kwargs):
        f = fn(*args, **kwargs)
        #Добавить обработку нескольких таблиц и добавление заголовка..
        beautiful_HTML = ""
        for t_i in f:
            beautiful_HTML += str(t_i) + "<br><br>"
        return beautiful_HTML
    return decorated

#def __text_to_HTML_decorator(fn):
#    #Можно тут курсив добавить
#    def decorated(*args, **kwargs):
#        f = fn(*args, **kwargs)
#        beautiful_HTML = f
#        return beautiful_HTML
#    return decorated

#Куча классов. Каждый получает объект, проверяет его на соответствие подразумеваемому
#классу и дает 

class c_abst_wrapper():
    def __init__(self):
        self.messages = []

    def set_object(self,an_object):
        if not(self.check_comp(an_object)):
            raise ValueError
        self.data_object = an_object

    def check_comp(self, an_object):
        ans = False
        if an_object.__class__.__name__ == self.obj_class_name:
            ans = True
        return ans

    def add_message(self, message_text):
        self.messages.append(message_text)

    def get_html(self):
        return "HTML text here"

    def get_name(self):
        return "string here"

    def get_status(self):
        return "do I use statuses?.."

class c_none_wrapper(c_abst_wrapper):
    obj_class_name = "any"
    #Подбирается в случае, если никто не подошел
    def check_comp(self, an_object):
        return 1

    def get_html(self):
        html_text = str(self.data_object)
        for str_i in self.messages:
            html_text += str_i + "<br>"
        return html_text

    def get_name(self):
        return self.data_object.__class__.__name__

class c_wh_wrapper(c_abst_wrapper):
    obj_class_name = "c_warehouse"
    def get_html(self):
        html_text = unicode(u"Остатки на складах: <br>")
        html_text += self.__get_table_warehouse(self.data_object)
        for str_i in self.messages:
            html_text += str_i + "<br>"
        return html_text

    def get_name(self):
        return "The Warehouse"

    def get_status(self):
        return "empty status"

    @table_to_HTML_decorator
    def __get_table_warehouse(self, a_warehouse):
        #Строит табличку - объект Table внешнего модуля
        a_table = Philippe_HTML.Table()
        a_table.header_row = [unicode(u"Материал"), unicode(u"Склад"), unicode(u"Количество"), unicode(u"Себестоимость"), unicode(u"Цена по себестоимости")]
        for posit_i in a_warehouse.positions:
            pr = 0
            if (posit_i.qtty > 0):
                pr = posit_i.cost / posit_i.qtty
            s_pr = unicode(simple_locale.number2string(pr))
            s_cst = unicode(simple_locale.number2string(posit_i.cost))
            s_qtty = unicode(simple_locale.number2string(posit_i.qtty))
            new_row = [unicode(posit_i.material.material_name), unicode(posit_i.vault.vault_name), s_qtty, s_cst, s_pr]
            a_table.rows.append(new_row)
        return [a_table]

class c_bank_account_wrapper(c_abst_wrapper):
    obj_class_name = "c_bank_account"

    def get_html(self):
        html_text = unicode(u"Остатки на расчетных счетах:") + "<br>"
        html_text += self.__get_table_bank_account(self.data_object)
        for str_i in self.messages:
            html_text += str_i + "<br>"
        return html_text

    def get_name(self):
        return "The Bank account"

    def get_status(self):
        return "empty status"

    @table_to_HTML_decorator
    def __get_table_bank_account(self, a_bank_account):
        #Строит табличку - объект Table внешнего модуля
        a_table = Philippe_HTML.Table()
        a_table.header_row = [unicode(u"Валюта"), unicode(u"Остаток")]
        for it_i in a_bank_account.money.iteritems():
            k_i = it_i[0]
            pos_i = it_i[1]
            s_amount = unicode(simple_locale.number2string(pos_i["amount"]))
            a_table.rows.append([unicode(str(k_i)), s_amount])
        return [a_table]

class c_simul_dataframe_wrapper(c_abst_wrapper):
    obj_class_name = "cb_simul_dataframe"

    def get_html(self):
        html_text = unicode(u"Отчет по симуляции:") + "<br>"
        html_text += self.get_name() + "<br>" + "<br>"
        html_text += self.data_object.data_frame.to_html()  #Плин - а тут форматирование так просто цифоркам не подменишь..
        return html_text

    def get_dataframe_to_plot(self):
        return self.data_object.data_frame

    def get_name(self):
        return self.data_object.data_frame_type + " - " + self.data_object.observer_name + " : " + self.data_object.var_name

    def get_status(self):
        return "empty status"

class c_client_model_wrapper(c_abst_wrapper):
    obj_class_name = "c_client_model"

    def get_html(self):
        html_text = unicode(self.data_object.name) + "<br><br>"
        html_text += u"<b>Цены:</b>" + "<br>"
        html_text += self.__get_table_prices() + "<br>"
        html_text += u"<b>Потребление:</b>" + "<br>"
        html_text += self.__get_table_mat_flows() + "<br>"
        html_text += unicode(u"Фактические отгрузки:") + "<br>"
        html_text += self.__get_table_fact_shipments()
        return html_text

    @table_to_HTML_decorator
    def __get_table_fact_shipments(self):
        #Строит табличку - объект Table внешнего модуля
        a_table = Philippe_HTML.Table()
        a_table.header_row = [unicode(u"Дата"), unicode(u"Товар"), unicode(u"Количество")]
        for f_sh_i in self.data_object.fact_shipments:
            c1 = unicode(f_sh_i.ship_date.strftime("%d %b %y"))
            c2 = unicode(f_sh_i.material.material_name)
            c3 = unicode(simple_locale.number2string(f_sh_i.ship_qtty))
            a_table.rows.append([c1, c2, c3])
        return [a_table]

    @table_to_HTML_decorator
    def __get_table_prices(self):
        #Строит табличку - объект Table внешнего модуля
        a_table = Philippe_HTML.Table()
        a_table.header_row = [unicode(u"Материал"), unicode(u"Цена"), unicode(u"Условия платежа"), unicode(u"Особые условия")]
        for pr_i in self.data_object.sell_prices:
            if pr_i.is_for_group:
                c1 = unicode(pr_i.material_type.material_type_name)
            else:
                c1 = unicode(pr_i.material.material_name)
            c2 = unicode(simple_locale.number2string(pr_i.price_value)) + " " + unicode(pr_i.payterm.ccy_quote.ccy_general_name)
            c3 = unicode(pr_i.payterm.payterm_name)
            if pr_i.nonformal_conditions is not None:
                c4 = unicode(pr_i.nonformal_conditions)
            else:
                c4 = ""
            a_table.rows.append([c1, c2, c3, c4])
        return [a_table]

    @table_to_HTML_decorator
    def __get_table_mat_flows(self):
        #Строит табличку - объект Table внешнего модуля
        a_table = Philippe_HTML.Table()
        a_table.header_row = [unicode(u"Материал"), unicode(u"Объём"), unicode(u"Регулярность")]
        for mf_i in self.data_object.material_flows:
            if mf_i.stats_mean_volume > 0:
                c1 = mf_i.material_type.material_type_name
                c2 = u"<b> %d </b> +/- %d"%(mf_i.stats_mean_volume, mf_i.stats_std_volume)
                c3 = u"<b> каждые %d дней </b> +/- %d дн."%(mf_i.stats_mean_timedelta, mf_i.stats_std_timedelta)
                a_table.rows.append([c1,c2,c3])
        return [a_table]

    def get_name(self):
        return self.data_object.name

    def get_status(self):
        return self.data_object.name

class c_supplier_model_wrapper(c_abst_wrapper):
    obj_class_name = "c_supplier_model"

    def get_html(self):
        html_text = unicode(self.data_object.name) + "<br>"
        html_text += u"<b>Прайсы:</b>"
        html_text += self.__get_table_prices()
        return html_text

    @table_to_HTML_decorator
    def __get_table_prices(self):
        #Строит табличку - объект Table внешнего модуля
        a_table = Philippe_HTML.Table()
        a_table.header_row = [unicode(u"Материал"), unicode(u"Прайс"), unicode(u"Условия платежа"), unicode(u"Особые условия")]
        for pr_i in self.data_object.buy_prices:
            if pr_i.is_for_group:
                c1 = unicode(pr_i.material_type.material_type_name)
            else:
                c1 = unicode(pr_i.material.material_name)
            c2 = unicode(simple_locale.number2string(pr_i.price_value)) + " " + unicode(pr_i.payterm.ccy_quote.ccy_name)
            c3 = unicode(pr_i.payterm.payterm_name)
            if pr_i.nonformal_conditions is not None:
                c4 = unicode(pr_i.nonformal_conditions)
            else:
                c4 = ""
            a_table.rows.append([c1, c2, c3, c4])
        return [a_table]

    def get_name(self):
        return self.data_object.name

    def get_status(self):
        return self.data_object.name

class c_proj_abst_wrapper(c_abst_wrapper):
    @table_to_HTML_decorator
    def get_steps_table(self):
        a_table = Philippe_HTML.Table()
        a_table.header_row = [unicode(u"Этап"), unicode(u"Статус"), unicode(u"Ожидаемая дата выполнения"), unicode(u"Возможные задержки (дней)")]
        for st_i in self.data_object.iter_steps_depth():
            c1 = unicode(st_i.step_name)
            if st_i.is_completed:
                c2 = unicode(u"Выполнен")
                c3 = unicode(u"")
                c4 = unicode(u"")
            else:
                c2 = unicode(u"В процессе")
                if st_i.is_scheduled:
                    c3 = unicode(st_i.planned_time_expected.strftime("%d %b %y"))
                    c4 = unicode(simple_locale.number2string(st_i.planned_time_possible_delay))
                else:
                    c3 = u"без плана"
                    c4 = u""
            a_table.rows.append([c1, c2, c3, c4])
        return [a_table]

    @table_to_HTML_decorator
    def get_table_order(self):
        #Строит табличку - объект Table внешнего модуля
        a_table = Philippe_HTML.Table()
        a_table.header_row = [unicode(u"Товар"), unicode(u"Количество"), unicode(u"Единица измерения"), unicode(u"Цена (без НДС)")]
        for pos_i in self.data_object.goods:
            c1 = unicode(pos_i.material.material_name)
            c2 = unicode(simple_locale.number2string(pos_i.qtty))
            c3 = unicode("n/a") #TODO
            c4 = unicode(simple_locale.number2string(pos_i.price))
            a_table.rows.append([c1, c2, c3, c4])
        return [a_table]

class c_proj_cl_ord_wrapper(c_proj_abst_wrapper):
    obj_class_name = "c_project_client_order"

    def get_html(self):
        html_text = unicode(u"Заказ от " + self.data_object.client_model.name) + "<br>"
        html_text += unicode(u"Спецификация : " + self.data_object.AgreementName + u" от " + self.data_object.DocDate.strftime("%d %b %y")) + "<br>"
        html_text += unicode(u"Условия оплаты : " + self.data_object.payment_terms.payterm_name) + "<br>"
        html_text += unicode(u"Поступило предоплат : " + simple_locale.number2string(self.data_object.MadePrepayments)) + "<br>"
        html_text += unicode(u"Поступило постоплат : " + simple_locale.number2string(self.data_object.MadePostpayments)) + "<br>"
        html_text += unicode(u"Всего заказано : ")  + "<br>"
        html_text += unicode(self.get_table_order())
        html_text += unicode(u"График выполнения : ")  + "<br>"
        html_text += unicode(self.get_steps_table())
        return html_text

class c_proj_supp_ord_wrapper(c_proj_abst_wrapper):
    obj_class_name = "c_project_supplier_order"

    def get_html(self):
        html_text = unicode(u"Закупка у " + self.data_object.supplier_model.name) + "<br>"
        html_text += unicode(u"Аддендум : " + self.data_object.AgreementName + u" от " + self.data_object.DocDate.strftime("%d %b %y")) + "<br>"
        html_text += unicode(u"Условия оплаты : " + self.data_object.payment_terms.payterm_name) + "<br>"
        html_text += unicode(u"Отправлено предоплат : " + simple_locale.number2string(self.data_object.MadePrepayments)) + "<br>"
        html_text += unicode(u"Отправлено постоплат : " + simple_locale.number2string(self.data_object.MadePostpayments)) + "<br>"
        html_text += unicode(u"Всего заказано : ")  + "<br>"
        html_text += unicode(self.get_table_order()) + "<br>"
        html_text += unicode(u"График выполнения : ")  + "<br>"
        html_text += unicode(self.get_steps_table())
        return html_text

class c_step_abst_wrapper(c_abst_wrapper):
    #a basic wrapper for an abstract step. ABSTRACT!!!
    @table_to_HTML_decorator
    def get_step_status_table(self):
        a_table = Philippe_HTML.Table()
        a_table.header_row = [unicode(u"---"), unicode(u"---")]
        a_table.rows.append([u"Тип этапа", unicode(self.data_object.discriminator)])
        a_table.rows.append([u"Имя этапа", unicode(self.data_object.step_name)])
        a_table.rows.append([u"Проект", unicode(self.data_object.project)])
        if self.data_object.is_scheduled:
            a_table.rows.append([u"Запланирован", self.data_object.planned_time_expected.strftime("%d %b %y")])
            a_table.rows.append([u"Возможна задержка до", simple_locale.number2string(self.data_object.planned_time_possible_delay) + u" дней"])
        else:
            a_table.rows.append([u"Не запланирован", u"Будет выполнен, как дойдет очередь"])
        return [a_table]

class c_step_payment_in_wrapper(c_step_abst_wrapper):
    obj_class_name = "c_step_payment_in"

    def get_html(self):
        html_text = u"Получение оплаты <br>"
        html_text += u"подробней: <br>"
        html_text += self.get_step_status_table()
        return html_text

class c_step_payment_out_wrapper(c_step_abst_wrapper):
    obj_class_name = "c_step_payment_out"

    def get_html(self):
        html_text = u"Исходящая оплата <br>"
        html_text += u"подробней: <br>"
        html_text += self.get_step_status_table()
        return html_text

class c_step_shipment_in_wrapper(c_step_abst_wrapper):
    obj_class_name = "c_step_shipment_in"

    def get_html(self):
        html_text = u"Оприходование товара <br>"
        html_text += u"подробней: <br>"
        html_text += self.get_step_status_table()
        return html_text

class c_step_shipment_out_wrapper(c_step_abst_wrapper):
    obj_class_name = "c_step_shipment_out"

    def get_html(self):
        html_text = u"Отгрузка <br>"
        html_text += u"подробней: <br>"
        html_text += self.get_step_status_table()
        return html_text

class c_crm_hashtag_wrapper(c_abst_wrapper):
    obj_class_name = "c_hastag"

    def get_html(self):
        html_text = u"Тематический фильтр по <b>#" + self.data_object.text + u"</b><br><br>"
        # Сортируем заметки по давности
        self.data_object.records.sort(key=lambda d: d.date_added)
        for rec_i in self.data_object.records:
            html_text += rec_i.get_html_text() + "<br><br>"
        return html_text

class c_crm_contact_wrapper(c_abst_wrapper):
    obj_class_name = "c_crm_contact"

    def get_html(self):
        html_text = u""
        if self.data_object.is_person:
            html_text += u"<b>" + unicode(self.data_object.name) + u"</b>" + u", " + unicode(self.data_object.job) + u"<br>"
            html_text += u"@" + unicode(self.data_object.company) + u"<br>"
        else:
            html_text += u"<b>" + unicode(self.data_object.company) + u"</b>" + u"<br><br>"
        if self.data_object.additional_info is not None:
            html_text += self.data_object.additional_info + u"<br>"
        if self.data_object.subs_to_prices:
            html_text += u"Подписан на рассылку коммерческих предложений" + u"<br>"
        if self.data_object.subs_to_logistics:
            html_text += u"Подписан на транспортную рассылку" + u"<br>"
        if self.data_object.subs_to_payments:
            html_text += u"Подписан на рассылку о платежах" + u"<br>"
        html_text += u"<br>"
        html_text += u"Контактная информация: <br>"
        for d_i in self.data_object.details:
            # # Чтобы заработало, надо ловить форварды и открывать их в браузере по умолчанию
            # if d_i.is_email(): #Генерим ссылку для отправки письма
            #     html_text += unicode(d_i.cont_type) + u":"
            #     html_text += utils.create_html_from_link(utils.generate_mailto_link(to_list=[d_i.cont_value]),d_i.cont_value) + u"<br>"
            # elif d_i.is_website():
            #     html_text += unicode(d_i.cont_type) + u":"
            #     html_text += utils.create_html_from_link(d_i.cont_value,d_i.cont_value) + u"<br>"
            # else:
                html_text += unicode(d_i) + u"<br>"
        return html_text
