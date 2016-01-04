# -*- coding: utf-8 -*-

# Сюда все заметки + бюджет
# Влючая процедуры и классы, работающие на синхронизацию

from db_exec import BASE
from db_utils import abst_key
from db_shared import *
import c_HTML_reports
from cnf import user_name


records_to_hastags = Table('crm_records_to_hastags', BASE.metadata,
                           Column('rec_id', Integer, ForeignKey('crm_record.rec_id')),
                           Column('hash_id', Integer, ForeignKey('crm_hastag.rec_id')))

class c_hastag(BASE, abst_key):
    __tablename__ = "crm_hastag"
    rec_id = Column(Integer, primary_key=True)
    text = Column(Unicode(255))

    def __repr__(self):
        return self.hashtext()

    def hashtext(self):
        return u"#" + self.text

class c_crm_record(BASE, abst_key):
    #Базовый функционал записи
    __tablename__ = "crm_record"
    rec_id = Column(Integer, primary_key=True)
    date_added = Column(DateTime)
    headline = Column(Unicode(255))
    long_html_text = Column(UnicodeText)
    hashtags_string = Column(Unicode(1024))  #Строка с хешкодами - чтобы быстро искать в GUI
    hashtags = relationship("c_hastag", secondary=records_to_hastags, backref="records")

    def __repr__(self):
        s = ""
        for h_i in self.hashtags:
            s += str(h_i) + ", "
        s += "\n" + str(self.date_added) + "\n"
        s += self.headline + "\n"
        s += self.long_html_text + "\n"
        return s

    def get_html_text(self):
        #returns some nicely formatted HTML text
        s = ""
        s += self.date_added.strftime("%Y %B %d (%A)")
        s += "   <u><b>" + self.headline + "<b></u><br>"
        s += '<a href="%s">%s</a>'%("edit:"+str(self.rec_id),"edit")
        #for h_i in self.hashtags:
        #    s += u"#" + unicode(h_i.text) + " "
        s += self.long_html_text
        return s

    def fix_hashtag_text(self):
        self.hashtags_string = ""
        texts = self.get_tags_text()
        for t in texts:
            self.hashtags_string += u"#" + t + " "

    def get_tags_text(self):
        tag_list = []
        for h_i in self.hashtags:
            tag_list += [h_i.text]
        return tag_list

    def match_with_tags(self, tag_list):
        self.hashtags = tag_list

class c_crm_contact(BASE, abst_key):
    __tablename__ = "crm_contacts"
    rec_id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('agents.rec_id'))
    company = relationship("c_agent", backref=backref('contacts'))
    name = Column(Unicode(255))
    job = Column(Unicode(255))
    is_person = Column(Boolean)
    additional_info = Column(UnicodeText)
    subs_to_prices = Column(Boolean)
    subs_to_logistics = Column(Boolean)
    subs_to_payments = Column(Boolean)

    def __repr__(self):
        s = unicode(self.name) + u", " + unicode(self.job) + u"\n"
        s += u"@" + unicode(self.company) + u"\n"
        if hasattr(self, "details"):
            for d_i in self.details:
                s += unicode(d_i) + u"\n"
        return s

    def add_new_contact_detail(self, t, v, is_fixed):
        self.details += [c_crm_contact_details(contact = self, cont_type = t, cont_value = v, is_type_fixed = is_fixed)]

    def change_existing_contact_detail(self, rec_id, t, v, is_fixed):
        tmp_dict = dict()
        for d_i in self.details:
            tmp_dict[d_i.rec_id] = d_i
        if tmp_dict.has_key(rec_id):
            d_the = tmp_dict[rec_id]
            d_the.cont_type = t
            d_the.cont_value = v
            d_the.is_type_fixed = is_fixed
        else: # Если ошибка логики - данные нельзя терять. Ну задвоятся..
            print("[c_crm_contact][change_existing_contact_detail] - error!")
            self.add_new_contact_detail(t, v, is_fixed)

class c_crm_contact_details(BASE, abst_key):
    # Если совсем приспичит, можно сделать классы-наследники для e-mail и т.п.
    # Может оказаться удобно для массовых рассылок. Пока просто к строке цепляемся.
    __tablename__ = "crm_contact_details"
    rec_id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('crm_contacts.rec_id'))
    contact = relationship("c_crm_contact", backref=backref('details', cascade="all,delete"))
    cont_type = Column(Unicode(255))  #Что за контакт
    cont_value = Column(Unicode(255))
    is_type_fixed = Column(Boolean)  #Чтобы "E-mail" не превращали в "Почта"

    def __repr__(self):
        s = unicode(self.cont_type) + " : " + unicode(self.cont_value)
        return s

    def is_email(self):
        return self.cont_type == u"E-mail"  #TODO нормализовать к этому виду

    def is_website(self):
        return self.cont_type == u"web-сайт" #TODO нормализовать к этому виду

    def check_is_email_format(self):
        # TODO re для нормализации имён типов. Проверяем, соответсвтует ли маске "somebody@somewhere.com"
        pass

    def check_is_website_format(self):
        pass

def crm_template_priceoffer(client):
    s = u"<b>Коммерческие предложения клиенту (#Офер)</b><br>"
    s += u"Для клиента "+unicode(client.hashtag_name())+u"<br>"
    #Группируем цены по условиям платежа
    prices = dict()
    for pr_i in client.sell_prices:
        if prices.has_key(pr_i.payterm):
            prices[pr_i.payterm] += [pr_i]
        else:
            prices[pr_i.payterm] = [pr_i]
    # А теперь печатаем табличку, сгруппированную по этапам оплаты
    for payterm, pr_list in prices.iteritems():
        s += "<br><i>" + payterm.payterm_name + "</i><br>"
        s += __crm_template_price_table(pr_list)
    return s

def crm_template_price_input(supplier):
    s = u"<b>#Прайс от поставщика</b><br>"
    s += u"От поставщика "+unicode(supplier.hashtag_name())+u"<br>"
    #Группируем цены по условиям платежа
    prices = dict()
    for pr_i in supplier.buy_prices:
        if prices.has_key(pr_i.payterm):
            prices[pr_i.payterm] += [pr_i]
        else:
            prices[pr_i.payterm] = [pr_i]
    # А теперь печатаем табличку, сгруппированную по этапам оплаты
    for payterm, pr_list in prices.iteritems():
        s += "<br><i>" + payterm.payterm_name + "</i><br>"
        s += __crm_template_price_table(pr_list)
    return s

@c_HTML_reports.table_to_HTML_decorator
def __crm_template_price_table(price_list):
    a_table = c_HTML_reports.Philippe_HTML.Table()
    a_table.header_row = [unicode(u"Материал"), unicode(u"Цена"), unicode(u"Особые условия")]
    for pr_i in price_list:
        if pr_i.is_for_group:
            c1 = pr_i.material_type.material_type_name
            mu = pr_i.material_type.measure_unit
        else:
            c1 = pr_i.material.material_name
            mu = pr_i.material.measure_unit
        c2 = u"%f %s / %s"%(pr_i.price_value, unicode(pr_i.payterm.ccy_quote.ccy_general_name), unicode(mu))
        if pr_i.nonformal_conditions is not None:
            c3 = unicode(pr_i.nonformal_conditions)
        else:
            c3 = u""
        a_table.rows.append([c1,c2,c3])
    return [a_table]

def crm_template_new_budget(client):
    s = u"#Бюджет потребления материалов "
    s += u"для клиента " + unicode(client.hashtag_name()) + u"<br><br>"
    s += __crm_template_budget_materials_consumption(client.material_flows)
    s += u"<b> Обоснование бюджета: </b><br>"
    return s

@c_HTML_reports.table_to_HTML_decorator
def __crm_template_budget_materials_consumption(material_flow_list):
    #s += u"<b>#" + unicode(a_mat_flow.material_type.hashtag_name()) +u"</b><br>"
    a_table = c_HTML_reports.Philippe_HTML.Table()
    a_table.header_row = [unicode(u"Материал"), unicode(u"Объём"), unicode(u"Регулярность")]
    for mf_i in material_flow_list:
        if mf_i.stats_mean_volume > 0:
            c1 = mf_i.material_type.hashtag_name()
            c2 = u"<b> %d %s </b> +/- %d"%(mf_i.stats_mean_volume, mf_i.material_type.measure_unit, mf_i.stats_std_volume)
            c3 = u"<b> каждые %d дней </b> +/- %d дн."%(mf_i.stats_mean_timedelta, mf_i.stats_std_timedelta)
            a_table.rows.append([c1,c2,c3])
    return [a_table]

def crm_template_change_volume_in_budget(a_mat_flow, old_volume, old_freq):
    s = u"Уточненный #бюджет по товару " + a_mat_flow.material_type.hashtag_name()
    s += u" для клиента " + a_mat_flow.client_model.hashtag_name() + "<br><br>"
    new_volume = float(a_mat_flow.stats_mean_volume)
    new_volume_std = a_mat_flow.stats_std_volume
    new_freq = float(a_mat_flow.stats_mean_timedelta)
    new_freq_std = a_mat_flow.stats_std_timedelta
    mu = a_mat_flow.material_type.measure_unit

    if new_freq > 0:
        new_level = new_volume/new_freq
    else:
        new_level = 0.
    if old_freq > 0:
        old_level = float(old_volume)/float(old_freq)
    else:
        old_level = 0.

    if new_level > old_level:
        if old_level > 0:
            a_prc = round(abs(new_level/old_level-1)*100,2)
            s += u"<b>Потребление выросло</b> на %d %% и составляет %d %s в день (было %d в день)"\
                 %(a_prc, new_level, mu, old_level) + u"<br>"
        else:
            s += u"<b>Потребление возобновилось!</b>. Теперь %d %s в день."%(new_level, mu) + u"<br>"
    elif new_level < old_level:
        if new_level == 0:
            s += u"<b>Потребление прекратилось!!!<b>" + u"<br>"
        elif old_level > 0:
            a_prc = round(abs(new_level/old_level-1)*100,2)
            s += u"<b>Потребление упало</b> на %d %% и составляет %d %s в день (было %d в день)"\
                 %(a_prc, new_level, mu, old_level) + u"<br>"
        else:
            s += u"Потребление упало. Теперь %d %s в день."%(new_level, mu) + u"<br>" #Что ещё здесь написать-то?...
    elif new_level == old_level:
        s += u"<b>Потребление не изменилось:</b> %d %s в день"%(new_level, mu) + u"<br>"

    if old_volume <> new_volume and old_volume > 0:
        if old_volume < new_volume:
            a_prc = round(abs(new_volume/old_volume-1)*100,2)
            s += u"Размер разового заказа вырос на %d %% и составляет <b> %d %s </b> +/- %d"%(a_prc, new_volume, mu, new_volume_std) + u"<br>"
        if old_volume > new_volume:
            a_prc = round(abs(new_volume/old_volume-1)*100,2)
            s += u"Размер разового заказа снизился на %d %% и составляет <b> %d %s </b> +/- %d"%(a_prc, new_volume, mu, new_volume_std) + u"<br>"
    else:
        s += u"Размер разового заказа <b> %d %s </b> +/- %d<br>"%(new_volume, mu, new_volume_std) + u"<br>"

    if old_freq <> new_freq and old_freq > 0:
        if old_freq > new_freq:
            a_prc = round(abs(new_freq/old_freq-1)*100,2)
            s += u"Частота заказов выросла на %d %% и теперь заказ происходит каждые <b> %d дней </b> +/- %d дн."\
                 %(a_prc, new_freq, new_freq_std) + u"<br>"
        if old_freq < new_freq:
            a_prc = round(abs(new_freq/old_freq-1)*100,2)
            s += u"Частота заказов снизилась на %d %% и теперь заказ происходит каждые <b> %d дней </b> +/- %d дн."\
                 %(a_prc, new_freq, new_freq_std) + u"<br>"
    else:
        s += u"Заказ происходит каждые <b> %d дней </b>  +/- %d дн."%(new_freq, new_freq_std) + u"<br>"
    s += u"<br><b>Комментарии:<b><br>"
    return s

def crm_template_new_budget_for_new_matflow(a_mat_flow):
    s = u"С клиентом " + a_mat_flow.client_model.hashtag_name() + u" достигнута новая договорённость!<br><br>"
    s += u"Новый #бюджет по " + a_mat_flow.material_type.hashtag_name() + u"<br>"
    s += u"Объём потребления: <b> %d </b> +/- %d <br>"%(a_mat_flow.stats_mean_volume, a_mat_flow.stats_std_volume)
    s += u"Частота: <b> каждые %d дней </b> +/- %d дн.<br>"%(a_mat_flow.stats_mean_timedelta, a_mat_flow.stats_std_timedelta)
    s += u"Детализация по материалам: <br>"
    s += __crm_template_materials_distribution_table(a_mat_flow.material_dist)
    s += u"Как удалось завоевать линию снабжения: <br>"
    return s

@c_HTML_reports.table_to_HTML_decorator
def __crm_template_materials_distribution_table(mat_dist_list):
    a_table = c_HTML_reports.Philippe_HTML.Table()
    a_table.header_row = [unicode(u"Материал"), unicode(u"Вероятность")]
    for md_i in mat_dist_list:
        c1 = unicode(md_i.material.material_name)
        c2 = "%d %%"%(round(md_i.choice_prob,2))
        a_table.rows.append([c1,c2])
    return a_table

def crm_template_new_sales_lead(a_lead):
    s = u"С клиентом " + a_lead.client_model.hashtag_name() + u" начались переговоры о поставках "
    s += a_lead.material_type.hashtag_name() + u".<br>"
    s += u"Это новый #лид - первый шаг к продажам.<br>"
    in_month = a_lead.expected_qtty * 30. / a_lead.expected_timedelta
    s += u"Объёмы заказов могут составить около <b>%d %s в месяц</b>, при этом:"%(in_month, a_lead.material_type.measure_unit)
    s += u"<ul>"
    s += u"<li>Возможный объём разового заказа: <b> %d </b> %s.</li>"%(a_lead.expected_qtty, a_lead.material_type.measure_unit)
    s += u"<li>Ожидаемая частота заказа: <b> каждые %d дней </b>.</li>"%(a_lead.expected_timedelta)
    s += u"</ul><br>"
    d1 = a_lead.expected_start_date_from
    d2 = a_lead.expected_start_date_till
    s += u"Ориентировочно, поставки начнутся %s - %s.<br>"%(d1.strftime("%x"), d2.strftime("%x"))
    if a_lead.instock_promise:
        s += u"Товар продвигается со складской программой - клиенту важно наличие товара на складе."
    else:
        s += u"Товар продвигается с прямой доставкой под заказ с максимально эффективной ценой, без лишних наценок за хранение."
    s += u"<br>"
    if a_lead.success_prob < 0.3:
        s += u"Шансы на успех совсем невысоки, потому как <...>"
    elif 0.3 <= a_lead.success_prob < 0.6:
        s += u"Шансы на успех не так уж и малы, но есть ряд сложностей: <...>"
    elif 0.6 <= a_lead.success_prob:
        s += u"Шансы на успех высоки, главное проработать вопросы: <...>"
    s += u"<br>"
    if a_lead.sure_level < 0.3:
        s += u"Клиент не раскрывает всей информации, единственное, что было сказано: <...>"
    elif 0.3 <= a_lead.sure_level < 0.6:
        s += u"Клиент сообщил лишь, что: <...>"
    elif 0.6 <= a_lead.sure_level:
        s += u"Клиент активно идёт на контакт и предоставил следующую информацию о потребностях: <...>"
    s += u"<br>"
    # Теперь заголовок заметки
    headline = u""
    if a_lead.success_prob < 0.3:
        headline = u"Маловероятная возможность для развития "
    elif 0.3 <= a_lead.success_prob < 0.6:
        headline = u"Новая возможность для развития - надо рассмотреть "
    elif 0.6 <= a_lead.success_prob < 0.8:
        headline = u"Хорошая возможность - надо не упустить "
    elif 0.8 <= a_lead.success_prob <0.95:
        headline = u"Успех близок, продолжаем работу "
    elif 0.95 <= a_lead.success_prob:
        headline = u"Это успех! "
    headline += a_lead.material_type.hashtag_name() + u" -> " + a_lead.client_model.hashtag_name()
    return s, headline

def crm_template_change_sales_lead(old_lead, new_lead):
    s = u"Проработка поставок " + new_lead.material_type.hashtag_name() + u" на " + new_lead.client_model.hashtag_name() + u".<br>"
    s += u"Это пока #лид - предварительная, очень важная для успеха дела работа.<br>"
    d1 = new_lead.expected_start_date_from
    d2 = new_lead.expected_start_date_till
    s += u"Ориентировочно, поставки начнутся %s - %s.<br>"%(d1.strftime("%x"), d2.strftime("%x"))
    if old_lead.success_prob > new_lead.success_prob:
        s += u"Шансы на успех снижаются! :-( <br>"
    elif old_lead.success_prob < new_lead.success_prob:
        s += u"Шансы на успех растут! :-) <br>"
    old_in_month = old_lead.expected_qtty * 30. / old_lead.expected_timedelta
    new_in_month = new_lead.expected_qtty * 30. / new_lead.expected_timedelta
    if old_in_month > new_in_month:
        s += u"Объём потребления <b>вырос</b> до <b> %d </b> %s в месяц. <br>"%(new_in_month, new_lead.material_type.measure_unit)
    elif old_in_month < new_in_month:
        s += u"Объём потребления <b>снизился</b> до <b> %d </b> %s в месяц. <br>"%(new_in_month, new_lead.material_type.measure_unit)
    if old_lead.instock_promise <> new_lead.instock_promise:
        if new_lead.instock_promise:
            s += u"Теперь товар продвигается со складской программой - клиенту оказалось важно наличие товара на складе.<br>"
        else:
            s += u"Теперь товар продвигается с прямой доставкой под заказ - клиенту не так важно наличие товара на нашем складе.<br>"
    headline = u"Работа по поставкам " + new_lead.material_type.hashtag_name() + u" -> " + new_lead.client_model.hashtag_name()
    if old_lead.sure_level > new_lead.sure_level:
        s += u"Возникают сомнения, правду ли говорит клиент: <...> <br>"
    elif old_lead.sure_level < new_lead.sure_level:
        s += u"Получена уточняющая информация: <...> <br>"
    return s, headline


def crm_template_material_request(client = None, a_mat_flow = None):
    if client is None and a_mat_flow is not None:
        client = a_mat_flow.client_model
    s = u"#ЗапросТовара<br>"
    if client is not None and a_mat_flow is not None:
        s += u"Клиент " + client.hashtag_name() + u" запросил товар из группы " + a_mat_flow.material_type.hashtag_name()
    elif client is not None and a_mat_flow is None:
        s += u"Клиент " + client.hashtag_name() + u" запросил товар из группы ..."
    else:
        s += u"Клиент ... запросил товар из группы ..."
    s += u"<br><br> Наша реакция на запрос: "
    return s

