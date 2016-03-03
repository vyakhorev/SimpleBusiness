# -*- coding: utf-8 -*-

"""
Created on Fri May 30 16:06:54 2014

@author: Vyakhorev
"""

#********************************************************************
#****           X M L           *************************************
#********************************************************************


#from cnf import InputDir, FileWithLists, FileWithLogs, FileWithDynamicData, OutputDir, FileForSalesBudgetExport

import xml.etree.ElementTree as ElementTree
import unicodecsv
import csv
import codecs
from db_main import *
from db_handlers import SynchFindingListError, SynchUnknownError
from utils import c_task, c_msg

#################################
def synch_error_handler(fn):
    #д.б. аргумент "xml_node"
    def wrapped(*args, **kwargs):
        try:
            f = fn(*args, **kwargs)
            return f
        except SynchFindingListError as an_error:
            #Не нашли в базе элемент "справочника"
            print "A kind of internal key error occured ..."
            func_name = "[" + fn.__name__ + "]"
            print "@" + func_name + ' - looks like there is no item in the list:'
            print "\t item code: " + an_error.acc_code
            print "\t item type: " + an_error.item_class_name
            raise SystemExit("Synchronisation stopped due to SynchFindingListError")
        except:
            #Необработанная ошибка
            func_name = "[" + fn.__name__ + "]"
            print "@" + func_name + ' - looks like an unknown problem with synch here'
            if kwargs.has_key("xml_node"):
                node_value = kwargs["xml_node"]
            else:
                node_value = "xml-node for object not available"
            raise SynchUnknownError(func_name,node_value)
            #raise SystemExit("Syncronisation stopped due to unknown error")
    return wrapped

def notna(an_object):
    if an_object is None:
        is_none = 1
    else:
        is_none = 0
    return [an_object, is_none]

def attr_ch(acc_sys_obj, attr_name, new_val):
    # Заменяет аттрибут в объекте и воозвращает сообщение об изменении.
    # Удобно для логирования изменений аттрибутов при синхронизации.
    s = None
    old_val = getattr(acc_sys_obj, attr_name)
    if old_val<>new_val:
        # скобки для читабельности
        s = u"Объект [%s] с кодом [%s] \n \t меняет аттрибут [%s] с [%s] на [%s]"%(acc_sys_obj.__class__.__name__,
            acc_sys_obj.account_system_code, attr_name, unicode(old_val), unicode(new_val))
    setattr(acc_sys_obj, attr_name, new_val)
    return s

def nappend(a_list, a_value):
    if a_value is not None:
        a_list.append(a_value)

def get_and_report_obj(obj_class, account_system_code, msgs, obj_logname = u""):
    if obj_logname == u"":
        obj_logname = obj_class.__name__
    if not(the_session_handler.check_existance_of_account_object(obj_class, account_system_code)):
        msgs += [u"Создаю новый объект [%s] с кодом %s"%(obj_logname,account_system_code)]
        obj_i = obj_class(account_system_code = account_system_code)
        the_session_handler.add_object_to_session(obj_i)
    else:
        obj_i = the_session_handler.get_account_system_object(obj_class, account_system_code)
    return obj_i

#################################
#   Выгрузка бюджета в csv
#################################

class c_print_budget_to_csv(c_task):
    # Выгрузка бюджета продаж в csv (пока не результаты симуляций)
    def __init__(self, csv_file_path):
        super(c_print_budget_to_csv, self).__init__(name=u"Выгрузка бюджета продаж")
        self.csv_file_path = csv_file_path

    def run_task(self):
        # Вызывается в admin_scripts.c_admin_tasks_manager
        yield c_msg(u"%s - старт"%(self.name))
        yield c_msg(u"выгружаю файл %s..."%(self.csv_file_path))
        budget_file = open(self.csv_file_path, mode='wb')
        csv_budget_file = unicodecsv.writer(budget_file, encoding='cp1251')

        the_firm = the_session_handler.get_singleton_object(c_trading_firm)
        wh_vault = the_firm.default_wh_vault
        prices_dict = dict()  #Заполняем промежуточный словарик цен (внутри - листы)
        for pr_i in the_session_handler.get_all_objects_list_iter(c_sell_price):
            if pr_i.is_for_group:
                k_i = (pr_i.client_model, pr_i.material_type)
            else:
                k_i = (pr_i.client_model, pr_i.material)
            if not(prices_dict.has_key(k_i)):
                prices_dict[k_i] = []
            prices_dict[k_i] += [pr_i]

        csv_budget_file.writerow(["mf_key",
                                  "date",
                                  "material_id",
                                  "client_id",
                                  "warehouse_id",
                                  "payment_cond_id",
                                  "quantity",
                                  "price",
                                  "is_subs",
                                  "is_urgent",
                                  "desired_lead_time"]) # TODO: implement in matflow is_urgent

        #для каждого мат. потока пишем ожидания прям в бюджет. Без симуляций пока..
        k = 0
        for mf_i in the_session_handler.get_all_objects_list_iter(c_material_flow):
            for sh_date, material, qtty, is_urgent in mf_i.get_expected_budget_iter(horizon_days=360):
                has_price = True
                if prices_dict.has_key((mf_i.client_model, material)):
                    pr_ent_list = prices_dict[(mf_i.client_model, material)]
                elif prices_dict.has_key((mf_i.client_model, material.material_type)):
                    pr_ent_list = prices_dict[(mf_i.client_model, material.material_type)]
                else:
                    yield c_msg(u"нету цены на %s для %s " % (unicode(material), unicode(mf_i.client_model)))
                    has_price = False
                if has_price: # без цены не печатаем
                    # Подбираем подходящую цену из списка
                    has_price = False
                    for pr_i in pr_ent_list:
                        if pr_i.is_per_order_only and not is_urgent:
                            if pr_i.min_order_quantity <= qtty:
                                pr_ent = pr_i
                                has_price = True
                        elif not pr_i.is_per_order_only and is_urgent:
                            if pr_i.min_order_quantity <= qtty:
                                pr_ent = pr_i
                                has_price = True
                if has_price:
                    csv_budget_file.writerow([mf_i.string_key(),
                                              datetime.date(year=sh_date.year, month=sh_date.month, day=sh_date.day).strftime("%Y.%m.%d"),
                                              material.account_system_code,
                                              mf_i.client_model.account_system_code,
                                              wh_vault.account_system_code,
                                              pr_ent.payterm.account_system_code,
                                              qtty,
                                              pr_ent.price_value,
                                              mf_i.are_materials_equal,
                                              is_urgent,
                                              pr_ent.order_fulfilment_timedelta])
                    k += 1
                else:
                    yield c_msg(u"нету подходящей цены на %s для %s " % (unicode(material), unicode(mf_i.client_model)))
        budget_file.close()
        yield c_msg(u"Выгрузил %d строк"%(k))
        yield c_msg(u"%s - успешно завершено"%(self.name))

#********************************************************************
#**********Загрузка из xml списоков *********************************
#********************************************************************

class c_read_lists_from_1C_task(c_task):
    # Загрузка всех списков из xml-файла.
    def __init__(self, xml_file_path):
        self.xml_file_path = xml_file_path
        super(c_read_lists_from_1C_task, self).__init__(name=u"Обновление справочников")

    def run_task(self):
        # Вызывается в admin_scripts.c_admin_tasks_manager
        yield c_msg(u"%s - старт"%(self.name))
        #---- Грузим из XML списки
        tree = ElementTree.parse(self.xml_file_path)
        root = tree.getroot()
        priority_list = []  # Заполняем список того, что хотим сделать
        priority_list.append(["Currencies", xml_LoadCurrency, 1]) #1 - commit, 0 - no commit till end of routine
        priority_list.append(["Payment_terms", xml_LoadPaymentTerm, 0])
        priority_list.append(["ItemsType", xml_LoadMaterialType, 0])
        priority_list.append(["ItemsTypeAccounting", xml_LoadMaterialTypeAccounting, 0])
        priority_list.append(["Items", xml_LoadMaterial, 0])
        priority_list.append(["CP", xml_LoadCP, 0])
        priority_list.append(["Vaults", xml_LoadVault, 0])
        priority_list.append(["PayTypes", xml_LoadPaymentType, 0]) # Этих больше нет. Зафиг не нужны.
        for (nodename, load_function, do_commit) in priority_list:
            for child1 in root.iter(nodename):
                yield c_msg(u"загружаю " + nodename)
                for child2 in child1:
                    is_success, messages = load_function(child2)
                    for msg_i in messages:
                        yield c_msg(msg_i)
            if do_commit:
                yield c_msg(u"записываю " + nodename)
                the_session_handler.commit_session()
                yield c_msg(nodename + u" записаны!")
        yield c_msg(u"записываю все пропущенные изменения")
        the_session_handler.commit_session()
        yield c_msg(u"запись сделана")
        yield c_msg(u"%s - успешно завершено"%(self.name))

@synch_error_handler
def xml_LoadCurrency(xml_node):
    msgs = []
    account_system_code = unicode(xml_node.attrib['account_system_code'])
    ccy_i = get_and_report_obj(c_currency,account_system_code,msgs,u"валюта")
    nappend(msgs, attr_ch(ccy_i, "ccy_general_name", unicode(xml_node.attrib['short_name'])))
    nappend(msgs, attr_ch(ccy_i, "ccy_name", unicode(xml_node.attrib['long_name'])))
    nappend(msgs, attr_ch(ccy_i, "ccy_public_code", unicode(xml_node.attrib['public_code'])))
    return [1, msgs]

@synch_error_handler
def xml_LoadPaymentTerm(xml_node):
    msgs = []
    account_system_code = unicode(xml_node.attrib['account_system_code'])
    pt_stages = c_payment_stages()
    for item_i in xml_node:
        if item_i.tag == 'Payment_Stage':
            pay_delay = int(convert(item_i.attrib['Term']))
            pay_proc = convert(item_i.attrib['Proc'])
            pt_stages.add_payment_term(pay_delay,pay_proc)
    ccy_quote_code = unicode(xml_node.attrib['CcyQuote_code'])
    ccy_quote = the_session_handler.get_account_system_object(c_currency, ccy_quote_code)
    ccy_pay_code = unicode(xml_node.attrib['CcyPay_code'])
    ccy_pay = the_session_handler.get_account_system_object(c_currency, ccy_pay_code)
    payment_terms_i = get_and_report_obj(c_payment_terms,account_system_code,msgs,u"условия платежа")
    if unicode(xml_node.attrib['ItemName']) == u"Да":  #TODO: выгрузить 1/0 из 1С
        nappend(msgs, attr_ch(payment_terms_i, "fixation_at_shipment", True))
    else:
        nappend(msgs, attr_ch(payment_terms_i, "fixation_at_shipment", False))
    nappend(msgs, attr_ch(payment_terms_i, "payterm_name", unicode(xml_node.attrib['ItemName'])))
    nappend(msgs, attr_ch(payment_terms_i, "payterm_stages", pt_stages))
    nappend(msgs, attr_ch(payment_terms_i, "ccy_quote", ccy_quote))
    nappend(msgs, attr_ch(payment_terms_i, "ccy_pay", ccy_pay))
    return [1, msgs]

@synch_error_handler
def xml_LoadMaterialType(xml_node):
    msgs = []
    account_system_code = unicode(xml_node.attrib['account_system_code'])
    material_type_i = get_and_report_obj(c_material_type,account_system_code,msgs,u"тип материала")
    nappend(msgs, attr_ch(material_type_i, "material_type_name", unicode(xml_node.attrib['ItemTypeName'])))
    return [1, msgs]

@synch_error_handler
def xml_LoadMaterialTypeAccounting(xml_node):
    msgs = []
    account_system_code = unicode(xml_node.attrib['account_system_code'])
    material_type_accounting_i = get_and_report_obj(c_material_type_accounting,account_system_code,msgs,u"учетный тип материала")
    nappend(msgs, attr_ch(material_type_accounting_i, "material_type_accounting_name", unicode(xml_node.attrib['ItemTypeName'])))
    return [1, msgs]

@synch_error_handler    
def xml_LoadMaterial(xml_node):
    msgs = []
    account_system_code = unicode(xml_node.attrib['account_system_code'])
    mattyp_code = unicode(xml_node.attrib['type_the_code'])
    mattypacc_code = unicode(xml_node.attrib['acc_type_the_code'])
    mat_type = the_session_handler.get_account_system_object(c_material_type, mattyp_code)
    mat_type_acc = the_session_handler.get_account_system_object(c_material_type_accounting, mattypacc_code)
    material_i = get_and_report_obj(c_material,account_system_code,msgs,u"материал")
    meas_unit = unicode(xml_node.attrib['measure_unit'])
    nappend(msgs, attr_ch(material_i, "material_name", unicode(xml_node.attrib['ItemName'])))
    nappend(msgs, attr_ch(material_i, "material_type", mat_type))
    nappend(msgs, attr_ch(material_i, "material_type_acc", mat_type_acc))
    nappend(msgs, attr_ch(material_i, "measure_unit", meas_unit))
    # Меняем группы материалов
    # FIXME: что-то не так в базе с группами..
    nappend(msgs, attr_ch(mat_type, "measure_unit", meas_unit))
    nappend(msgs, attr_ch(mat_type_acc, "measure_unit", meas_unit))
    return [1, msgs]

@synch_error_handler
def xml_LoadCP(xml_node):
    msgs = []
    account_system_code = unicode(xml_node.attrib['account_system_code'])
    cp_type = xml_node.tag
    if cp_type == "A_client":
        cp_class, cp_log_name = c_client_model, u"клиент"
    elif cp_type == "A_material_supplier":
        cp_class, cp_log_name = c_supplier_model, u"поставщик"
    else:
        msgs += [u"Не могу обработать тип %s, код 1C: %s"%(cp_type, account_system_code)]
        return [0, msgs]
    if not(the_session_handler.check_existance_of_account_object(cp_class, account_system_code)):
        msgs += [u"Создаю нового агента (%s) с кодом %s"%(cp_log_name, account_system_code)]
        cp_i = cp_class(account_system_code=account_system_code)
        the_session_handler.add_object_to_session(cp_i)
    else:
        cp_i = the_session_handler.get_account_system_object(cp_class, account_system_code)
    nappend(msgs, attr_ch(cp_i, "name", unicode(xml_node.attrib['CPName'])))
    nappend(msgs, attr_ch(cp_i, "full_name", unicode(xml_node.attrib['CPFullName'])))
    nappend(msgs, attr_ch(cp_i, "inn", unicode(xml_node.attrib['inn'])))
    #nappend(msgs, attr_ch(cp_i, "hashtag", unicode(xml_node.attrib['CPHashtag'])))
    return [1, msgs]

@synch_error_handler
def xml_LoadVault(xml_node):
    msgs = []
    account_system_code = unicode(xml_node.attrib['account_system_code'])
    vault_i = get_and_report_obj(c_warehouse_vault, account_system_code, msgs, u"место хранения")
    nappend(msgs, attr_ch(vault_i, "vault_name", unicode(xml_node.attrib['vault_name'])))
    nappend(msgs, attr_ch(vault_i, "is_available_exw", unicode(xml_node.attrib['is_available_exw'])))
    return [1, msgs]

@synch_error_handler
def xml_LoadPaymentType(xml_node):
    # Статья ДДС FIXME: из 1С выгрузились лишние
    msgs = []
    account_system_code = unicode(xml_node.attrib['account_system_code'])
    paytype_i = get_and_report_obj(c_payment_type,account_system_code,msgs,u"тип платежа")
    nappend(msgs, attr_ch(paytype_i, "name", unicode(xml_node.attrib['type_name'])))
    return [1, msgs]

#********************************************************************
#**********Загрузка из xml истории отгрузок - отдельная табличка****
#********************************************************************

class c_read_logs_from_1C_task(c_task):
    # Загрузка всех отгрузок и платежей из базы - статистики только ради.
    def __init__(self, xml_file_path):
        self.xml_file_path = xml_file_path
        super(c_read_logs_from_1C_task, self).__init__(name=u"Загрузка лога отгрузок и оплат")

    def run_task(self):
        # Вызывается в admin_scripts.c_admin_tasks_manager
        yield c_msg(u"%s - старт"%(self.name))
        delete_list = [(u"отгрузки",c_fact_shipment), (u"оплаты",c_fact_payment)]
        for cl_name, cl_i in delete_list:
            # TODO: можно и не удалять. Симпатичней будет.
            yield c_msg(u"Удаляю %s (лог)"%(cl_name))
            the_session_handler.delete_all_objects(cl_i)
            yield c_msg(u"Все %s удалены"%(cl_name))
        tree = ElementTree.parse(self.xml_file_path)
        root = tree.getroot()
        priority_list = []  # Заполняем список того, что хотим сделать
        priority_list.append(["ShipmentsLog", xml_LoadFactShipment, 1]) #1 - commit, 0 - no commit till end of routine
        priority_list.append(["PaymentsLog", xml_LoadFactPayment, 1])
        for (nodename, load_function, do_commit) in priority_list:
            for child1 in root.iter(nodename):
                yield c_msg(u"загружаю " + nodename)
                a_counter = 0
                not_counter = 0
                for child2 in child1:
                    try_msg = []
                    # try:
                    is_success, messages = load_function(child2)
                    if not is_success:
                        try_msg += [c_msg(u"Ошибка с обработкой %s"%(nodename))]
                        not_counter += 1
                    else:
                        a_counter += 1
                    for msg_i in messages:
                        try_msg += [c_msg(msg_i)]
                    # except SynchFindingListError:
                    #     try_msg += [c_msg(u"Ошибка с обработкой %s"%(nodename))]
                    #     not_counter += 1
                    for msg in try_msg:
                        yield msg
                yield c_msg(u"%s загружено %d записей из %d"%(nodename, a_counter, not_counter+a_counter))
            if do_commit:
                yield c_msg(u"записываю " + nodename)
                the_session_handler.commit_session()
                yield c_msg(nodename + u" записаны!")
        yield c_msg(u"записываю все пропущенные изменения")
        the_session_handler.commit_session()
        yield c_msg(u"запись сделана")
        yield c_msg(u"%s - успешно завершено"%(self.name))

@synch_error_handler                
def xml_LoadFactShipment(xml_node):
    msgs = []
    item_1C_code = unicode(xml_node.attrib['Item_the_code'])
    try:
        a_item = the_session_handler.get_account_system_object(c_material, item_1C_code)
    except SynchFindingListError:
        msgs += [c_msg(u'SynchFindingListError: не нашёл товар с 1С кодом ' + item_1C_code)]
        return [0, msgs]
    CP_1C_code = unicode(xml_node.attrib['CP_the_code'])
    try:
        a_CP = the_session_handler.get_account_system_object(c_client_model, CP_1C_code)
    except SynchFindingListError:
        msgs += [c_msg(u'SynchFindingListError: не нашёл клиента с 1С кодом ' + CP_1C_code)]
        return [0, msgs]
    item_qtty = convert(xml_node.attrib['Qtty'])
    shipment_date = convert_str_2_date(xml_node.attrib['Date'])
    sh_i = c_fact_shipment(ship_qtty = item_qtty, ship_date = shipment_date,material=a_item, client_model = a_CP)
    the_session_handler.add_object_to_session(sh_i)
    return [1, msgs]

@synch_error_handler
def xml_LoadFactPayment(xml_node):
    msgs = []
    pay_i = c_fact_payment()
    # Вполне возможно, что всех контрагентов не будет.
    # Когда будет - значит, клиент. Можно проверить статистику платежей.
    # Когда не будет - ну и фиг с ним. Это только ради статистики платежей.
    CP_1C_code = unicode(xml_node.attrib['CP_the_code'])
    does_exist = the_session_handler.check_existance_of_account_object(c_agent, CP_1C_code)
    if does_exist:
        pay_i.agent_model = the_session_handler.get_account_system_object(c_agent, CP_1C_code)
    else:
        pay_i.agent_model = None
    PayType_code = unicode(xml_node.attrib['PayType_code'])
    if PayType_code.strip() <> "":  # А вот это должно быть
        pay_i.paytype = the_session_handler.get_account_system_object(c_payment_type, PayType_code)
    else: # Надо такого избегать. Но не принципиально.
        pay_i.paytype = None # Но и такое надо хендлить.
    ccy_code = unicode(xml_node.attrib['Ccy_code'])
    pay_i.ccy_pay = the_session_handler.get_account_system_object(c_currency, ccy_code)
    pay_i.sum_total = convert(xml_node.attrib['Sum'])
    pay_i.pay_date = convert_str_2_date(xml_node.attrib['Date'])
    the_session_handler.add_object_to_session(pay_i)
    return [1, msgs]

#********************************************************************
#**********Загрузка из xml динамических данных***********************
#**********склады, денежные счета открытые заказы.. *****************
#********************************************************************

class c_read_dynamic_data_from_1C_task(c_task):
    # Загрузка всех списков из xml-файла.
    def __init__(self, xml_file_path):
        self.xml_file_path = xml_file_path
        super(c_read_dynamic_data_from_1C_task, self).__init__(name=u"загрузка склада, р/с, заказов, проектов из 1С")

    def run_task(self):
        # Вызывается в admin_scripts.c_admin_tasks_manager
        yield c_msg(u"%s - старт"%(self.name))
        #Обнуляем объеты - ведь считаем все заново
        yield c_msg(u"Обнуляю склад")
        the_WH = the_session_handler.get_singleton_object(c_warehouse)
        the_WH.set_to_zero()
        for v_i in the_session_handler.get_all_objects_list_iter(c_warehouse_vault):
            v_i.warehouse = the_WH
        yield c_msg(u"Обнуляю расчетный счет")
        the_BANK = the_session_handler.get_singleton_object(c_bank_account)
        the_BANK.set_to_zero()
        yield c_msg(u"Склад и расчетный счет обнулены")
        #---- Грузим из XML списки
        tree = ElementTree.parse(self.xml_file_path)
        root = tree.getroot()
        priority_list = []  # Заполняем список того, что хотим сделать
        #priority_list.append(["Inventory", xml_LoadWarehousePosition, 1, the_WH]) #1 - commit, 0 - no commit till end of routine
        #priority_list.append(["Money", xml_LoadMoney, 1, the_BANK])
        priority_list.append(["ClientOrders", xml_LoadClientOrder, 0, None])
        #priority_list.append(["SupplierOrders", xml_LoadSupplierOrder, 0, None])
        for (nodename, load_function, do_commit, cont_i) in priority_list:
            for child1 in root.iter(nodename):
                yield c_msg(u"загружаю " + nodename)
                for child2 in child1:
                    if cont_i is None:
                        is_success, messages = load_function(child2)
                    else:
                        is_success, messages = load_function(child2, cont_i)
                    for msg_i in messages:
                        yield c_msg(msg_i)
            if do_commit:
                yield c_msg(u"записываю " + nodename)
                the_session_handler.commit_session()
                yield c_msg(nodename + u" записаны!")
        yield c_msg(u"записываю все пропущенные изменения")
        the_session_handler.commit_session()
        yield c_msg(u"запись сделана")
        yield c_msg(u"%s - успешно завершено"%(self.name))

@synch_error_handler
def xml_LoadWarehousePosition(xml_node, the_WH):
    msgs = []
    vault_code = unicode(xml_node.attrib['vault_system_code'])
    a_vault = the_session_handler.get_account_system_object(c_warehouse_vault, vault_code)
    material_code = unicode(xml_node.attrib['material_system_code'])
    does_exist = the_session_handler.check_existance_of_account_object(c_material, material_code)
    if does_exist:
        a_material = the_session_handler.get_account_system_object(c_material, material_code)
        qtty, cost = convert(xml_node.attrib['Qtty']), convert(xml_node.attrib['Cost_RUB'])
        the_session_handler.merge_object_to_session(a_vault, a_material)
        the_WH.add_position(material=a_material, vault=a_vault, qtty=qtty, cost=cost)
    else:
        msgs += [u"ошибка: не найден материал с кодом %s"%(material_code)]
    return [1, msgs]

@synch_error_handler
def xml_LoadMoney(xml_node, the_BANK):
    msgs = []
    #Код валюты
    ccy_code = unicode(xml_node.attrib['ccy_system_code'])
    #Ищем валюту
    a_ccy = the_session_handler.get_account_system_object(c_currency, ccy_code)
    #Считываем цифры
    qtty = convert(xml_node.attrib['Sum'])
    #Добавляем позицию
    the_BANK.add_position(a_ccy, qtty)
    return [1, msgs]

@synch_error_handler
def xml_LoadClientOrder(xml_node):
    # TODO: этапы оплаты - теперь есть в 1С
    msgs = []
    account_system_code = unicode(xml_node.attrib['account_system_code'])
    the_proj_existed = the_session_handler.check_existance_of_account_object(c_project_client_order, account_system_code)
    cl_ord = get_and_report_obj(c_project_client_order,account_system_code,msgs,u"заказ клиента")

    a_client = the_session_handler.get_account_system_object(c_client_model, unicode(xml_node.attrib['client_system_code']))
    nappend(msgs, attr_ch(cl_ord, "client_model", a_client))

    paycond_code = unicode(xml_node.attrib['PaymentTerms_code'])
    if the_session_handler.check_existance_of_account_object(c_payment_terms, paycond_code):
        payment_cond = the_session_handler.get_account_system_object(c_payment_terms, paycond_code)
        nappend(msgs, attr_ch(cl_ord, "payment_terms", payment_cond))
    else:
        msgs += [u"ошибка: не найдены условия платежа для заказа %s клиента %s"%(account_system_code, a_client.name)]
        msgs += [u"заказ %s будет удален"%(account_system_code)]
        the_session_handler.delete_concrete_object(cl_ord)
        return [0, msgs]

    #vault = the_session_handler.get_account_system_object(c_warehouse_vault, unicode(xml_node.attrib['Vault_code']))

    nappend(msgs, attr_ch(cl_ord, "DocDate", convert_str_2_date(xml_node.attrib['OrderDate'])))
    nappend(msgs, attr_ch(cl_ord, "DateShipmentScheduled", convert_str_2_date(xml_node.attrib['DateWhenDone'])))
    # TODO: alternate DB schema and delete MadePrepayments, MadePostpayments
    # nappend(msgs, attr_ch(cl_ord, "MadePrepayments", convert(xml_node.attrib['PrepaymentMade'])))
    # nappend(msgs, attr_ch(cl_ord, "MadePostpayments", convert(xml_node.attrib['PostpaymentMade'])))
    nappend(msgs, attr_ch(cl_ord, "AgreementName", unicode(xml_node.attrib['Specification'])))
    # sh_date = convert_str_2_date(xml_node.attrib['DateShipped'])
    # if type(sh_date) == datetime.datetime:
    #     nappend(msgs, attr_ch(cl_ord, "IsShipped", True))
    #     nappend(msgs, attr_ch(cl_ord, "DateFactShipment", sh_date))
    # elif sh_date == 0:
    #     nappend(msgs, attr_ch(cl_ord, "IsShipped", False))
    list_with_items = list()
    for item_i in xml_node:
        if item_i.tag == "ordered_position":
            it_i_code = unicode(item_i.attrib['Item_code'])
            if the_session_handler.check_existance_of_account_object(c_material, it_i_code):
                it_i = the_session_handler.get_account_system_object(c_material, it_i_code)
                item_qtty = convert(item_i.attrib['Qtty'])
                item_price = convert(item_i.attrib['Price'])
                vat_rate = convert(item_i.attrib['VAT_rate_above'])/100
                list_with_items += [[it_i, item_qtty, item_price, vat_rate]]
            else:
                msgs += [u"ошибка: не найден товар %s для заказа %s"%(it_i_code, cl_ord.account_system_code)]
                msgs += [u"заказ %s будет удален"%(cl_ord.account_system_code)]
                the_session_handler.delete_concrete_object(cl_ord)
                return [0, msgs]
    if the_proj_existed:
        cl_ord.synchronize_positions_with_a_list(list_with_items)
    else:
        for pos_list_i in list_with_items:
            cl_ord.add_position(pos_list_i[0], pos_list_i[1], pos_list_i[2], pos_list_i[3])
        #cl_ord.build_order_steps()
    return [1, msgs]

@synch_error_handler
def xml_LoadSupplierOrder(xml_node):
    msgs = []
    #Считываем строки
    account_system_code = unicode(xml_node.attrib['account_system_code'])
    #Проверяем, нету ли в системе такого заказа. Если нет, то создается:
    does_the_proj_exist = the_session_handler.check_existance_of_account_object(c_project_supplier_order,account_system_code)
    sup_ord = the_session_handler.recieve_account_system_object(c_project_supplier_order,account_system_code)
    #Поставщик
    supplier_code = unicode(xml_node.attrib['supplier_system_code'])
    a_supplier = the_session_handler.get_account_system_object(c_agent, supplier_code)
    sup_ord.supplier_model = a_supplier
    #Условия платежа
    payment_cond_code = unicode(xml_node.attrib['PaymentTerms_code'])
    payment_cond = the_session_handler.get_account_system_object(c_payment_terms, payment_cond_code)
    sup_ord.payment_terms = payment_cond
    #Условия отгрузки - склад
    #vault_code = unicode(xml_node.attrib['Vault_code'])
    #vault = the_session_handler.get_account_system_object(c_warehouse_vault, vault_code)
    #sup_ord.set_shipment_details(vault)
    #Прочие детали
    sup_ord.DocDate = convert_str_2_date(xml_node.attrib['OrderDate'])
    sup_ord.DateShipmentScheduled = convert_str_2_date(xml_node.attrib['DateWhenDone'])
    # TODO: alternate db and kill these
    # sup_ord.MadePrepayments = convert(xml_node.attrib['PrepaymentMade'])
    # sup_ord.MadePostpayments = convert(xml_node.attrib['PostpaymentMade'])
    sup_ord.AgreementName = unicode(xml_node.attrib['Specification'])
    # sh_date = convert_str_2_date(xml_node.attrib['DateShipped'])
    # if type(sh_date) == datetime.datetime:
    #     sup_ord.IsShipped = True
    #     sup_ord.DateFactShipment = sh_date
    # elif sh_date == 0:
    #     sup_ord.IsShipped = False
    #Обновляем список материалов
    list_with_items = list()
    for item_i in xml_node:
        if item_i.tag == "ordered_position":
            it_i_code = unicode(item_i.attrib['Item_code'])
            it_i = the_session_handler.get_account_system_object(c_material, it_i_code)
            item_qtty = convert(item_i.attrib['Qtty'])
            item_price = convert(item_i.attrib['Price'])
            vat_rate = convert(item_i.attrib['VAT_rate_above'])/100
            list_with_items += [[it_i, item_qtty, item_price, vat_rate]]
    if does_the_proj_exist: #Проект уже существует в базе. Передаем его целиком в заказ - он будет синхронизироваться
        sup_ord.synchronize_positions_with_a_list(list_with_items)
    else: #Проекта еще нет в базе. Добавим все позиции поименно
        for pos_list_i in list_with_items:
            sup_ord.add_position(pos_list_i[0], pos_list_i[1], pos_list_i[2], pos_list_i[3])
        #Строим шаги проекта
        #sup_ord.build_order_steps()
    return [1, msgs]

@synch_error_handler
def xml_LoadShipmentProject(xml_node):
    msgs = []
    return [1, msgs]

class c_read_generalinfo_from_1C_task(c_task):
    # Пока просто дату выгрузки получает
    def __init__(self):
        super(c_read_generalinfo_from_1C_task, self).__init__(name=u"Обновление даты выгрузки")

    def run_task(self):
        # Вызывается в admin_scripts.c_admin_tasks_manager
        yield c_msg(u"%s - старт"%(self.name))
        tree = ElementTree.parse(FileWithDynamicData)
        root = tree.getroot()
        current_date = convert_str_2_date(root.find('GeneralInfo').attrib['CurrentDate'])
        the_settings_manager.set_param("initial_data_date", current_date)
        the_session_handler.commit_session()
        yield c_msg(u"дата выгрузки: %s"%(current_date.strftime("%x")))

class c_update_ccy_stats(c_task):
    def __init__(self):
        super(c_update_ccy_stats, self).__init__(name=u"Оценка статистики курса валют")

    def run_task(self):
        # TODO: а вот это надо сделать нормально
        yield c_msg(u"%s - старт"%(self.name))
        a_ccy1 = the_session_handler.get_account_system_object(c_currency,unicode("840"))
        a_ccy2 = the_session_handler.get_account_system_object(c_currency,unicode("978"))
        a_ccy3 = the_session_handler.get_account_system_object(c_currency,unicode("643"))
        the_macro_model = the_session_handler.get_singleton_object(c_macro_market)
        the_macro_model.add_ccy_quote(a_ccy1,51.,34.6,0.020)
        the_macro_model.add_ccy_quote(a_ccy2,55.,49.0,0.025)
        the_macro_model.add_ccy_quote(a_ccy3,1,1,0)
        the_session_handler.add_object_to_session(the_macro_model)
        the_session_handler.commit_session()
        for s in the_macro_model.ccy_quotes.itervalues():
            yield c_msg(u"%s buy: %f, sell:%f, stdev:%f"%(unicode(s["ccy"]),s["buy"],s["sell"],s["stdev"]))

class c_build_excessive_links(c_task):
    # Это трудновыводимый костыль.
    def __init__(self):
        super(c_build_excessive_links, self).__init__(name=u"Конструирование the_firm")

    def run_task(self):
        #Пока в базе одна фирма, всё просто
        yield c_msg(u"%s - старт"%(self.name))
        the_firm = the_session_handler.get_singleton_object(c_trading_firm)
        the_firm.define_warehouse(the_session_handler.get_singleton_object(c_warehouse))
        the_firm.define_bank_account(the_session_handler.get_singleton_object(c_bank_account))
        the_firm.define_projects_list(the_session_handler.get_all_objects_list(c_project))
        the_firm.define_sell_prices_list(the_session_handler.get_all_objects_list(c_sell_price))
        sklad = the_session_handler.get_account_system_object(c_warehouse_vault, u"БП0000008")
        the_firm.define_default_wh_vault(sklad)
        roubles = the_session_handler.get_account_system_object(c_currency, u"643")
        the_firm.define_main_currency(roubles)
        the_session_handler.commit_session()
        yield c_msg(u"%s - дело сделано"%(self.name))

