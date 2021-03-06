# -*- coding: utf-8 -*-

__author__ = 'Vyakhorev'

from db_simulation import *
from db_crm import *
from db_utils import *
from db_exec import BASE
from db_handlers import engine
import utils

import statistics

BASE.metadata.create_all(engine)  #TODO: почему это не после импорта?

# # система контроля версий - пока не очень понятно, как это можно применить так..
# from alembic.config import Config
# from alembic import command
# alembic_cfg = Config("alembic.ini")
# command.stamp(alembic_cfg, "head")

from db_handlers import the_session_handler


# RECORD SIMULATION RESULTS and set settings

def iter_epoch_data():
    for sim_res in the_session_handler.get_all_objects_list_iter(cb_epoh_data):
        yield sim_res

def add_epoch_data(epoh_num, seed, sim_res):
    ep_i = cb_epoh_data(epoh_num = epoh_num, seed_value = seed, simulation_results = sim_res)
    the_session_handler.add_object_to_session(ep_i)
    the_session_handler.commit_session()  #Вот тут нужно комитить раз во много раз.

def clear_epoch_data():
    the_session_handler.delete_all_objects(cb_epoh_data)
    the_session_handler.commit_and_close_session()

###########################################################

def get_agent_list():
    repr_cls_i = with_polymorphic(c_agent, '*')
    for ag_i in the_session_handler.get_all_objects_list_iter(repr_cls_i):
        yield ag_i

def get_client_list():
    #Возвращает список всех записей в таблице
    for cl_m in the_session_handler.get_all_objects_list_iter(c_client_model):
        yield cl_m #Подозреваю, что можно было напрямую итератор передать

def get_supplier_list():
    #Возвращает список всех записей в таблице
    for sup_m in the_session_handler.get_all_objects_list_iter(c_supplier_model):
        yield sup_m #Подозреваю, что можно было напрямую итератор передать

def get_agent_list_by_name(agent_name):
    repr_cls = with_polymorphic(c_agent, '*')
    ans = []
    for ag_i in the_session_handler.get_active_session().query(repr_cls).filter_by(name = agent_name).all():
        ans += [ag_i]
    return ans

def get_agent_list_by_inn(agent_inn):
    repr_cls = with_polymorphic(c_agent, '*')
    ans = []
    for ag_i in the_session_handler.get_active_session().query(repr_cls).filter_by(inn = agent_inn).all():
        ans += [ag_i]
    return ans

def get_mat_flows_list(client_model = None):
    #Возвращает список всех записей в таблице
    if client_model is None:
        for m_f_i in the_session_handler.get_all_objects_list_iter(c_material_flow):
            yield m_f_i
    else:
        for m_f_i in the_session_handler.get_active_session().query(c_material_flow).filter_by(client_model_rec_id = client_model.rec_id).all():
            yield m_f_i

def get_matdist_list(matflow = None):
    if matflow is None:
        for md_i in the_session_handler.get_all_objects_list_iter(c_material_flow_matdist):
            yield md_i
    else:
        for md_i in the_session_handler.get_active_session().query(c_material_flow_matdist).filter_by(material_flow_rec_id = matflow.rec_id).all():
            yield md_i

def get_prices_list(agent_model = None):
    #Возвращает список всех записей в таблице
    if agent_model is None: #А это куды и зачем?
        print u"[db_main.get_prices_list] Подозрительный вызов"
        for pr_i in the_session_handler.get_all_objects_list_iter(c_material_price):
            yield pr_i
    else:
        if agent_model.discriminator == "supplier":
            for pr_i in the_session_handler.get_active_session().query(c_buy_price).filter_by(supplier_model_rec_id = agent_model.rec_id).all():
                yield pr_i
        elif agent_model.discriminator == "client":
            for pr_i in the_session_handler.get_active_session().query(c_sell_price).filter_by(client_model_rec_id = agent_model.rec_id).all():
                yield pr_i

def get_sell_prices():
    for pr_i in the_session_handler.get_all_objects_list_iter(c_sell_price):
        yield pr_i

def get_buy_prices():
    for pr_i in the_session_handler.get_all_objects_list_iter(c_buy_price):
        yield pr_i

def get_payment_terms():
    for pay_term_i in the_session_handler.get_all_objects_list_iter(c_payment_terms):
        yield pay_term_i

def get_materials_list():
    for mat_i in the_session_handler.get_all_objects_list_iter(c_material):
        yield mat_i

def get_material_types_list():
    for mat_type_i in the_session_handler.get_all_objects_list_iter(c_material_type):
        yield mat_type_i

def get_ccy_list():
    for ccy_i in the_session_handler.get_all_objects_list_iter(c_currency):
        yield ccy_i

def get_proj_list():
    #Возвращает список всех записей в таблице
    for proj_i in the_session_handler.get_all_objects_list_iter(c_project):
        yield proj_i

def get_initial_data_report_tree():
    my_report_list = []
    wh = the_session_handler.get_singleton_object(c_warehouse)
    bnk = the_session_handler.get_singleton_object(c_bank_account)
    # Заполняем отчетами
    wh_report = the_report_filler.get_report_for_object(wh)
    my_report_list.append(wh_report)
    bnk_report = the_report_filler.get_report_for_object(bnk)
    my_report_list.append(bnk_report)
    for proj_i in the_session_handler.get_all_objects_list_iter(c_project):
        my_report_list.append(the_report_filler.get_report_for_object(proj_i))
    return my_report_list

def get_records_list():
    return the_session_handler.get_all_objects_list(c_crm_record)

def get_records_list_iter():
    return the_session_handler.get_all_objects_list_iter(c_crm_record)

# def get_records_list_iter_from_hashtag(tag_i):
#     for rec_i in tag_i.records:
#         yield rec_i

def get_records_list_andfilt_by_hashtags(hashtags):
    #вход - список объектов-хештегов. Выход - общие записи. Пришлось циклом. Благо оно ленивое и не всё грузится.
    all_records = []
    for ht_i in hashtags:
        all_records += ht_i.records # если нет, то пусто?...
    filt_records = []
    for rec_i in all_records:
        do_add = 1
        for ht_i in hashtags:
            if not(ht_i in rec_i.hashtags):
                do_add = 0
                break
        if do_add: filt_records += [rec_i]
    filt_records.sort(key=lambda d: d.date_added)
    return filt_records

def get_records_iter_deep_search(search_string):
    #с юникдом работает как case_sensitive. Пришлось циклом
    # s = '%' + search_string + '%'
    # condition = or_(c_crm_record.headline.ilike(s), c_crm_record.long_html_text.ilike(s))
    # base_query = the_session_handler.get_active_session().query(c_crm_record).filter(condition)
    # return base_query.all()
    # НЕ ИСПОЛЬЗУЕТСЯ
    found_records = []
    search_string_l = search_string.lower()
    for r_i in the_session_handler.get_all_objects_list_iter(c_crm_record):
        if search_string_l in r_i.headline.lower():
            found_records += [r_i]
        elif search_string_l in r_i.hashtags_string.lower():
            found_records += [r_i]
        elif search_string_l in r_i.long_html_text.lower():
            found_records += [r_i]
    return found_records

def get_dynamic_crm_records_iterator():
    '''
    Итератор, подгружающий базу заметок худо-бедно экономно и динамически
    '''
    s = the_session_handler.get_active_session()
    ids = s.execute('SELECT crm_record.rec_id FROM crm_record ORDER BY crm_record.date_added DESC')
    for id_i in ids:
        yield s.query(c_crm_record).get(id_i.rec_id)

def get_dynamic_crm_records_iterator_by_hashtag(hashtag):
    '''
    Итератор, подгружающий базу заметок по хештегу худо-бедно экономно и динамически
    (можно получше сделать, из таблички..)
    '''
    s = the_session_handler.get_active_session()
    ids = s.execute('SELECT crm_record.rec_id FROM crm_record ORDER BY crm_record.date_added DESC')
    for id_i in ids:
        rec_i = s.query(c_crm_record).options(lazyload('*')).get(id_i.rec_id)
        if _match_crm_record_to_hashtag(rec_i, hashtag):
            yield rec_i

def _match_crm_record_to_hashtag(rec_i, hashtag):
    search_string_l = hashtag.hashtext().lower()
    if search_string_l in rec_i.hashtags_string.lower():
        return True

def get_dynamic_crm_records_iterator_search(search_string):
    s = the_session_handler.get_active_session()
    ids = s.execute('SELECT crm_record.rec_id FROM crm_record ORDER BY crm_record.date_added DESC')
    for id_i in ids:
        rec_i = s.query(c_crm_record).options(lazyload('*')).get(id_i.rec_id)
        if _match_crm_record_to_search_string(rec_i, search_string):
            yield rec_i

def _match_crm_record_to_search_string(rec_i, search_string):
    # TODO: вот это можно сделать поинтересней..
    search_string_l = search_string.lower()
    if search_string_l in rec_i.headline.lower():
        return True
    elif search_string_l in rec_i.hashtags_string.lower():
        return True
    elif search_string_l in rec_i.long_html_text.lower():
        return True

def get_hashtags_list_iter():
    return the_session_handler.get_all_objects_list_iter(c_hastag)

def get_hashtags_text_list():
    # Используется для подсвечивания тэгов - чтобы юзер понял, что ввёл то, что надо.
    # Ну и для подсказок.
    ans = []
    for h_i in the_session_handler.get_all_objects_list_iter(c_hastag):
        ans += [u"#" + h_i.text]
    return ans

def create_hashtag(dirty_text_for_hashtag):
    # так хештэги создают объекты базы - контрагенты, товары
    clean_text = utils.sanitize_to_hashtext(dirty_text_for_hashtag)
    existing = the_session_handler.get_active_session().query(c_hastag).filter(c_hastag.text == clean_text).all()
    if len(existing) >= 1:
        return existing[0]
    else:
        a_ht = c_hastag(text=clean_text)
        the_session_handler.add_object_to_session(a_ht)
        return a_ht

def check_if_hashtag_from_system(hashtag_text):
    # Проверяем, не является ли текст зарезервированным системой
    # Используется для удаления/добавления хештега

    # Не контрагент ли?
    for ag_i in the_session_handler.get_all_objects_list_iter(c_agent):
        if hashtag_text == ag_i.hashtag_name()[1:]:  # убираем "#"
            return True

    # # Не материал ли?
    # for mat_i in the_session_handler.get_all_objects_list_iter(c_material):
    #     if hashtag_text == mat_i.hashtag_name()[1:]:
    #         return True

    # Не группа ли материалов?
    for mat_i in the_session_handler.get_all_objects_list_iter(c_material_type):
        if hashtag_text == mat_i.hashtag_name()[1:]:
            return True

    # Ну, значит, всё ок.
    return False

def check_if_hashtag_name_exists(hashtag_text):
    # Используется при переименовании хештега
    all_hashtags = get_hashtags_text_list()
    if u'#'+hashtag_text in all_hashtags: return True
    return False

def rename_hashtag_usages(old_hashtag_name, new_hashtag_name):
    #В правильном случае, len(found_tags_old) = 1, len(found_tags_new) = 0
    old_hashtag_name = old_hashtag_name.lower()
    new_hashtag_name = new_hashtag_name.lower()
    found_tags_old = get_hashtags_from_names([old_hashtag_name])
    found_tags_new = get_hashtags_from_names([new_hashtag_name])
    if len(found_tags_old) == 0:
        return
    old_hashtag = found_tags_old[0]
    old_hashtag.text = new_hashtag_name
    for rec_i in old_hashtag.records:
        h_old = u"#" + old_hashtag_name
        h_new = u"#" + new_hashtag_name
        rec_i.headline = replace_unicode_text(unicode(rec_i.headline), h_old, h_new)
        rec_i.hashtags_string = replace_unicode_text(unicode(rec_i.hashtags_string), h_old, h_new)
        rec_i.long_html_text = replace_unicode_text(unicode(rec_i.long_html_text), h_old, h_new)
    if len(found_tags_new) >= 1:
        # Надо прилепить все одномиенные к этому - ссылки перебросить
        to_delete = []
        for new_ht in found_tags_new:
            for rec_i in new_ht.records:
                an_ind = rec_i.hashtags.index(new_ht)
                to_delete += [rec_i.hashtags.pop(an_ind)]
                rec_i.hashtags += [old_hashtag]
        #the_session_handler.commit_session()
        for forg_ht in to_delete:
            #the_session_handler.delete_concrete_object(forg_ht)
            the_session_handler.active_session.delete(forg_ht)
    the_session_handler.commit_session()

def delete_hashtag_usage(hashtag_name):
    found_tags = get_hashtags_from_names([hashtag_name])
    if len(found_tags) == 0:
        return
    hashtag = found_tags[0]
    for rec_i in hashtag.records:
        # Убираем "#" от тега
        str_old = u"#" + hashtag_name
        str_new = hashtag_name
        rec_i.headline = replace_unicode_text(unicode(rec_i.headline), str_old, str_new)
        rec_i.hashtags_string = replace_unicode_text(unicode(rec_i.hashtags_string), str_old, str_new)
        rec_i.long_html_text = replace_unicode_text(unicode(rec_i.long_html_text), str_old, str_new)
    the_session_handler.active_session.delete(hashtag)
    the_session_handler.commit_session()

def get_contacts_list(agent = None):
    if agent is None:
        for cnt_i in the_session_handler.get_all_objects_list_iter(c_crm_contact):
            yield cnt_i
    else:
        for cnt_i in the_session_handler.get_active_session().query(c_crm_contact).filter_by(company_id=agent.rec_id).all():
            yield cnt_i

def get_contacts_by_email(email_address):
    # Returns found contacts by email_address
    cont_dets = the_session_handler.get_active_session().query(c_crm_contact_details).filter(c_crm_contact_details.cont_value.like(email_address)).all()
    contacts = []
    for det_i in cont_dets:
        c_i = det_i.contact
        if not(c_i in contacts):
            contacts += [c_i]
    return contacts

def get_default_prices_from_orders(agent_model, material, is_group):
    # По клиенту / поставщику и материалу достаем условия из последнего заказа.
    # Тут временная реализация, поскольку потом придётся переделать проекты
    # (в родительском проекте не хватает ссылки на агента).

    # Задача - упростить форму ввода цены.

    ans_dict = {}
    ans_dict['price'] = 0
    ans_dict['payment_term'] = None

    if agent_model.discriminator == 'client':
        sess = the_session_handler.get_active_session()
        q = sess.query(c_project_client_order)
        q.filter(c_project_client_order.client_model == agent_model)
        q.order_by(c_project_client_order.DocDate.desc())
    elif agent_model.discriminator == 'supplier':
        sess = the_session_handler.get_active_session()
        q = sess.query(c_project_supplier_order)
        q.filter(c_project_supplier_order.supplier_model == agent_model)
        q.order_by(c_project_supplier_order.DocDate.desc())
    for order_i in q.all():
        for pos_i in order_i.goods:
            if not(is_group):
                if pos_i.material == material:
                    ans_dict['price'] = pos_i.price
                    ans_dict['payment_term'] = order_i.payment_terms
                    return ans_dict
            elif pos_i.material.material_type == material: # is_group = True
                ans_dict['price'] = pos_i.price
                ans_dict['payment_term'] = order_i.payment_terms
                return ans_dict
    return None

def get_default_price_terms(agent_model):
    # Берем условия платежа из других цен агента
    terms = []
    if agent_model.discriminator == 'client':
        for price_i in agent_model.sell_prices:
            terms += [price_i.payterm]
    elif agent_model.discriminator == 'supplier':
        for price_i in agent_model.buy_prices:
            terms += [price_i.payterm]
    if len(terms) > 0:
        return terms[0] # Можно выбрать и получше критерий, чем первый..
    else:
        return None

def update_todos_with_object(todoing):
    # receives a todoing inheritor, gets the dictionary with proposed todos,
    # checks the database - does everything comply.
    # in case updates required, returns a dict with updates.
    # todoing instance must inherit abst_key as well
    if not hasattr(todoing, 'propose_todos'):
        raise BaseException('Not supposed to see this class instance here')

    todo_proposed_schedule = todoing.propose_todos() # dictionaries
    todo_active_schedule = get_todo_schedule(todoing) # c_todo_item instances

    # TODO: а здесь можно просто старые удалить и новые записать, если есть отличия по датам




def get_todo_schedule(todoing):
    # все ремайндеры хранятся в crm_todo_item. Для объекта их можно подобрать по
    # object_id - это string_key() - метод abst_key.
    key_for_search = todoing.string_key()
    sess = the_session_handler.get_active_session()
    q = sess.query(c_todo_item)
    q.filter(c_todo_item.parent_object_id == key_for_search)
    q.filter(c_todo_item.is_active == True)
    active_todos = q.all()
    return active_todos



###########################################################

def estimate_shipment_stats(client, material_group = None):
    # 1. Вызываем в GUI (или где надо).
    # 2. Передаём словари в material_flow, если нужно в базу записать.
    # Метод, оценивающий статистику потребления (matflow). Всегда тут теперь оценивается.
    # Возвращает список словарей. Каждый словарь представляет собой MatFlow.
    # Если client = a_client, material_group = None - оценивает все потоки по клиенту
    # Если client = a_client, material_group = a_material_group - все по клиенту и группе товаров
    fact_shipments_list = []
    all_material_groups = []
    if material_group is not None:
        all_material_groups = [material_group]
    for sh_i in client.fact_shipments:
        if material_group is None:
            fact_shipments_list.append([sh_i.ship_date, sh_i.material, sh_i.ship_qtty])
            if not(sh_i.material.material_type in all_material_groups):
                all_material_groups += [sh_i.material.material_type]
        elif sh_i.material.material_type == material_group:
            fact_shipments_list.append([sh_i.ship_date, sh_i.material, sh_i.ship_qtty])
    for ord_i in client.active_orders: #Плюс, проверяем все подтверждённые заказы
        if not(ord_i.IsShipped):
            for pos_i in ord_i.goods:
                if material_group is None:
                    fact_shipments_list.append([ord_i.DateShipmentScheduled, pos_i.material, pos_i.qtty])
                    if not(pos_i.material.material_type in all_material_groups):
                        all_material_groups += [pos_i.material.material_type]
                elif pos_i.material.material_type == material_group:
                    fact_shipments_list.append([ord_i.DateShipmentScheduled, pos_i.material, pos_i.qtty])
    # Теперь на основе статистики в fact_shipments_list формируем mf_dicts
    mf_dicts = dict()  #Потом возвращаем содержимое словаря (без ключей)
    for m_gr in all_material_groups:
        mf_dicts[m_gr] = dict(material_type = m_gr, time_series = statistics.c_event_predictive_ts(), mat_dist = c_random_dict())
    # А теперь прогоняем статистику еще раз и заполняем временные ряды, откуда потом будем статистику тянуть
    not_aggregated = []

    for date_i, material_i, qtty_i in fact_shipments_list:
        not_aggregated.append([date_i, qtty_i])
        mf_dicts[material_i.material_type]["mat_dist"].add_elem(material_i, qtty_i)

    for date_i, qtty_i in aggregate_shipments(not_aggregated):
        mf_dicts[material_i.material_type]["time_series"].add_point(date_i,qtty_i)

    for mf_i in mf_dicts.itervalues():
        # Переоцениваем временной ряд
        mf_i["time_series"].run_estimations()
        mf_i["qtty_exp"] = mf_i["time_series"].prediction_value_expectation
        mf_i["qtty_std"] = round(mf_i["time_series"].prediction_value_std, 4)
        mf_i["timedelta_exp"] = mf_i["time_series"].prediction_timedelta_expectaion
        mf_i["timedelta_std"] = mf_i["time_series"].prediction_timedelta_std
        mf_i["last_shipment_date"] = mf_i["time_series"].last_event_date
        #print mf_i["time_series"]
        mf_i.pop("time_series")  #Не передаем временной ряд никуда
        # А теперь еще refinery - оцениваем распределение материалов (в нём нет взвешевания по времени)
        mf_i["mat_dist"].finalize()
    #debug
    #print("estimated model for " + str(client) + ":" + str(material_group))
    return mf_dicts.values()

def aggregate_shipments(shipments_list):
    # 0 - date, 1 - qtty
    # Все по порядку. Наверное.
    grouped_shipment_list = []
    last_date = None
    new_shipment = 0
    for date_i, qtty_i in shipments_list:
        if last_date is None:
            last_date = date_i
        if date_i <> last_date:
            grouped_shipment_list.append([last_date, new_shipment])
            new_shipment = 0
            last_date = date_i
        new_shipment += qtty_i
    return grouped_shipment_list

def get_shipments_history(client, material_group):
    fact_shipments_list = []
    for sh_i in client.fact_shipments:
        if sh_i.material.material_type == material_group:
            fact_shipments_list.append([sh_i.ship_date, sh_i.ship_qtty])
    return aggregate_shipments(fact_shipments_list)


def get_hashtags_from_names(hashcode_list):
    #Получаем лист имен хэштегов и возвращаем инстансы базы (только существующие)
    found_hashtags = []
    for ht_i in hashcode_list:
        found_hashtags += the_session_handler.get_active_session().query(c_hastag).filter(c_hastag.text == ht_i).all()
    return found_hashtags

""" А вот эти надо сделать сильно проще """

def init_system_from_database(the_devs):
    list_to_read = connected_to_DEVS.__subclasses__()
    #Метод ниже делает глубокое считывание. Таким образом, может считать не только наследников connected_to_DEVS.
    cashed_instances = the_session_handler.cash_instances_to_dict(list_to_read, True)
    #Каждый объект получает ссылку на систему - ничего более
    for inst_list_i in cashed_instances.itervalues():
        for inst_i in inst_list_i:
            inst_i.s_set_devs(the_devs)
            inst_i.prepare_for_simulation()  #do not create new connected_to_DEVS instances here! Use lastbreath_before_simulation!
    #Теперь собираем систему - явно указываем, какой объект куда идет
    the_devs.define_macro_market(cashed_instances["c_macro_market"][0])
    the_devs.define_trading_firm(cashed_instances["c_trading_firm"][0])
    clients = filter(lambda ag_i: ag_i.discriminator == "client", cashed_instances["c_agent"])
    the_devs.define_clients_list(clients)

# Some useful tests...
def print_order_positions():
    all_order_positions = the_session_handler.get_all_objects_list(c_order_position)
    for k, pos_i in enumerate(all_order_positions):
        cp_name = ""
        if pos_i.order.discriminator == "client_order":
            cp_name = pos_i.order.client_model.name
        elif pos_i.order.discriminator == "supplier_order":
            cp_name = pos_i.order.supplier_model.name
        print "["+str(k+1)+"] " + cp_name+ "  ---  " + pos_i.material.material_name + " qtty: " + str(pos_i.qtty) + " price: " + str(pos_i.price)

def print_firm():
    the_firm = the_session_handler.get_singleton_object(c_trading_firm)
    print "Active projects in the firm:"
    for proj_i in the_firm.projects:
        print "\t " + str(proj_i.string_key())
        for st_i in proj_i.iter_steps_depth():
            print "\t \t " + str(st_i.string_key())
    print "Warehouse:"
    print unicode(the_firm.warehouse)

def check_payproc():
    for st_i in the_session_handler.get_all_objects_list_iter(c_step_payment_in):
        print "a pay proc: " + str(st_i.pay_proc)

""" TEST """
if __name__ == "__main__":

    do_synch = 0  #change this if you must
    if do_synch:
        print "*" * 20
        print "READ XML -> DATABASE"
        import main_exec
        """ Write some instances to DB """
        main_exec.run_1C_synch()
        print "*" * 20
        print "DATABASE READY"
        print_firm()

    """ read them and run simulation"""
    print "*" * 20
    print "PREPARE SIMULATION..."
    #start_date = the_settings_manager.get_param_value("initial_data_date")
    start_date = datetime.datetime.now()
    the_devs = c_discrete_event_system(simpy.Environment(), start_date)
    the_devs.set_seed()
    init_system_from_database(the_devs)
    the_devs.lastbreath_before_simulation()
    the_devs.add_printer(console_log_printer())
    the_devs.simpy_env.process(the_devs.my_generator())  #Остальные вызываются каскадно
    print "*" * 20
    print "RUN SIMULATION..."
    print "*" * 20
    the_devs.simpy_env.run(until = 500)
    print "*" * 20
    print "FINISH"


# class c_base_settings_manager():
#
#     def get_simul_settings(self):
#         simul_params = ["pring_log", "epoch_num", "until"]
#         a_dict = dict()
#         for obj_i in the_session_handler.get_all_objects_list_iter(cb_base_settings):
#             if obj_i.param_name in simul_params:
#                 a_dict[obj_i.param_name] = obj_i.param_data
#         return a_dict
#
#     def set_default_base_simul_settings(self):
#         param_dict = dict(pring_log = False, epoch_num = 10, until = 200)
#         for par_k,par_v in param_dict.iteritems():
#             self.set_param(par_k, par_v)
#
#     def set_param(self,parameter_name,param_value):
#         print(parameter_name, param_value)
#         #Только этой процедурой!  Иначе задвоятся
#         #if the_session_handler.get_active_session().query(cb_base_settings).filter(cb_base_settings.param_name == parameter_name).count() == 0:
#         #    the_param = cb_base_settings(param_name = parameter_name)
#         #    the_session_handler.add_object_to_session(the_param)
#         #else:
#         #    the_param = the_session_handler.get_active_session().query(cb_base_settings).filter(cb_base_settings.param_name == parameter_name).one()
#         #the_param.param_data = param_value
#         #the_session_handler.commit_session()
#         #pass
#
#     def get_param_value(self,parameter_name):
#         the_param = the_session_handler.get_active_session().query(cb_base_settings).filter(cb_base_settings.param_name == parameter_name).one()
#         return the_param.param_data
#
#     def iter_all_params(self):
#         for param_i in the_session_handler.get_all_objects_list_iter(cb_base_settings):
#             yield param_i
#
# #the_settings_manager = c_base_settings_manager()
# #the_settings_manager.set_default_base_simul_settings()