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

from db_handlers import the_session_handler


""" RECORD SIMULATION RESULTS and set settings """

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
    #TODO: наверное, можно ускорить
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
        a_ht = c_hastag(text = clean_text)
        the_session_handler.add_object_to_session(a_ht)
        return a_ht

def rename_hashtag_usages(old_hashtag_name, new_hashtag_name):
    #В правильном случае, len(found_tags_old) = 1, len(found_tags_new) = 0
    old_hashtag_name = old_hashtag_name.lower()
    new_hashtag_name = new_hashtag_name.lower()
    found_tags_old = get_hashtags_from_names([old_hashtag_name])
    found_tags_new = get_hashtags_from_names([new_hashtag_name])
    if len(found_tags_old) >= 1:
        old_hashtag = found_tags_old[0]
        old_hashtag.text = new_hashtag_name
        for rec_i in old_hashtag.records:
            h_old = u"#" + old_hashtag_name
            h_new = u"#" + new_hashtag_name
            rec_i.headline = replace_unicode_text(unicode(rec_i.headline), h_old, h_new)
            rec_i.hashtags_string = replace_unicode_text(unicode(rec_i.hashtags_string), h_old, h_new)
            rec_i.long_html_text = replace_unicode_text(unicode(rec_i.long_html_text), h_old, h_new)
        if len(found_tags_new) >= 1:
            # TODO: можно было просто переделать таблицу соответствия
            # Надо прилепить все одномиенные к этому - ссылки перебросить
            to_delete = []
            for new_ht in found_tags_new:
                for rec_i in new_ht.records:
                    an_ind = rec_i.hashtags.index(new_ht)
                    to_delete += [rec_i.hashtags.pop(an_ind)]
                    rec_i.hashtags += [old_hashtag]
            the_session_handler.commit_session()
            for forg_ht in to_delete:
                the_session_handler.delete_concrete_object(forg_ht)

# def get_contacts_list_iter():
#     return the_session_handler.get_all_objects_list_iter(c_crm_contact)

def get_contacts_list(agent = None):
    if agent is None:
        for cnt_i in the_session_handler.get_all_objects_list_iter(c_crm_contact):
            yield cnt_i
    else:
        for cnt_i in the_session_handler.get_active_session().query(c_crm_contact).filter_by(company_id=agent.rec_id).all():
            yield cnt_i

###########################################################

def fix_sales_budget(client = None, mat_flow = None):
    # Пересчет данных из mat_flow/всех mat_flow по клиенту / по всем mat_flow в ожидаемые значения.
    mat_flow_list = []  #вот по этим
    if client is None and mat_flow is None:  #по всем обновим
        mat_flow_list = the_session_handler.get_all_objects_list_iter(c_material_flow)  #итератор
    if mat_flow is not None and client is None:  #только по одному материальному потоку
        mat_flow_list += [mat_flow]
    if client is not None and mat_flow is None:  #Достаем все материальные потоки
        mat_flow_list = get_mat_flows_list(client) #итератор
    # Очищаем бюджет TODO: проверить, что удаляется сначала, потом добавляется
    the_session_handler.delete_all_objects(c_sales_budget)
    #the_session_handler.commit_session()   #Проверить с и без
    the_firm = the_session_handler.get_singleton_object(c_trading_firm)
    wh_vault = the_firm.default_wh_vault
    prices_dict = dict()  #Заполняем промежуточный словарик, чтобы проще было цены искать для mf_i
    for pr_i in the_session_handler.get_all_objects_list_iter(c_sell_price):
        if pr_i.is_for_group:
            k_i = (pr_i.client_model, pr_i.material_type)
        else:
            k_i = (pr_i.client_model, pr_i.material)
        prices_dict[k_i] = pr_i
    for mf_i in mat_flow_list: #для каждого мат. потока пишем ожидания прям в бюджет. Без симуляций пока..
        for sh_date, material, qtty in mf_i.get_expected_budget_iter():
            if prices_dict.has_key((mf_i.client_model,material.material_type)):
                pr_ent = prices_dict[(mf_i.client_model,material.material_type)]
                bgt_i = c_sales_budget(material=material, client=mf_i.client_model, quantity=qtty, price=pr_ent.price_value,
                                       payment_terms=pr_ent.payterm, expected_date_of_shipment=sh_date, wh_vault=wh_vault)
                the_session_handler.add_object_to_session(bgt_i)
            elif prices_dict.has_key((mf_i.client_model,material)):
                pr_ent = prices_dict[(mf_i.client_model,material)]
                bgt_i = c_sales_budget(material=material, client=mf_i.client_model, quantity=qtty, price=pr_ent.price_value,
                                       payment_terms=pr_ent.payterm, expected_date_of_shipment=sh_date, wh_vault=wh_vault)
                the_session_handler.add_object_to_session(bgt_i)
            else:
                print("[fix_sales_budget]: no price available of %s for %s " % (str(material), str(mf_i.client_model)))
    the_session_handler.commit_session()

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
    for date_i, material_i, qtty_i in fact_shipments_list:
        mf_dicts[material_i.material_type]["time_series"].add_point(date_i,qtty_i)
        mf_dicts[material_i.material_type]["mat_dist"].add_elem(material_i, qtty_i)
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

def get_hashtags_from_names(hashcode_list):
    #Получаем лист имен хэштегов и возвращаем инстансы базы (только существующие)
    found_hashtags = []
    for ht_i in hashcode_list:
        found_hashtags += the_session_handler.get_active_session().query(c_hastag).filter(c_hastag.text == ht_i).all()
    return found_hashtags

""" А вот эти надо сделать сильно проще """

class c_base_settings_manager():

    def get_simul_settings(self):
        simul_params = ["pring_log", "epoch_num", "until"]
        a_dict = dict()
        for obj_i in the_session_handler.get_all_objects_list_iter(cb_base_settings):
            if obj_i.param_name in simul_params:
                a_dict[obj_i.param_name] = obj_i.param_data
        return a_dict

    def set_default_base_simul_settings(self):
        param_dict = dict(pring_log = False, epoch_num = 10, until = 200)
        for par_k,par_v in param_dict.iteritems():
            self.set_param(par_k, par_v)

    def set_param(self,parameter_name,param_value):
        #Только этой процедурой!  Иначе задвоятся
        if the_session_handler.get_active_session().query(cb_base_settings).filter(cb_base_settings.param_name == parameter_name).count() == 0:
            the_param = cb_base_settings(param_name = parameter_name)
            the_session_handler.add_object_to_session(the_param)
        else:
            the_param = the_session_handler.get_active_session().query(cb_base_settings).filter(cb_base_settings.param_name == parameter_name).one()
        the_param.param_data = param_value
#        the_session_handler.commit_session()

    def get_param_value(self,parameter_name):
        the_param = the_session_handler.get_active_session().query(cb_base_settings).filter(cb_base_settings.param_name == parameter_name).one()
        return the_param.param_data

    def iter_all_params(self):
        for param_i in the_session_handler.get_all_objects_list_iter(cb_base_settings):
            yield param_i

the_settings_manager = c_base_settings_manager()
the_settings_manager.set_default_base_simul_settings()

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
    start_date = the_settings_manager.get_param_value("initial_data_date")
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
