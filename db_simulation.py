# -*- coding: utf-8 -*-

__author__ = 'Vyakhorev'

""" REFS """


from db_exec import BASE
from db_utils import *
from utils import *
from db_shared import *

import c_HTML_reports
import c_meganode

import datetime
import numpy
import random
import simpy
import sys

from convert import *

""" SIM UTILS """


class connected_to_DEVS(object):
    #TODO: во время симуляции мы создаём объекты. Передавать по "пайпам" все "системное" от родителей одним методом!
    #Any class present in simulation should inherit this
    #The only purpose is to collect childs and read them. We may implement smth friendly here..
    def log_repr(self):
        return self.__repr__()

    def s_set_devs(self, discrete_event_system):
        self.devs = discrete_event_system

    def prepare_for_simulation(self):
        # Do not create new instances here. They could loose link to DEVS
        pass

    def lastbreath_before_simulation(self):
        # Called just before the simulation - you should remember to call it. You can create new instances here
        pass

class cb_epoh_data(BASE):
    __tablename__ = "epoh_data"
    rec_id = Column(Integer, primary_key=True)
    epoh_num = Column(Integer)
    seed_value = Column(Integer)
    simulation_results = Column(PickleType)  #Можно не трачить мутабельность

class cb_simul_dataframe(BASE):
    #TODO: вот тут можно сделать иерархию обсерверов
    #Хранит результаты симуляций в агрегированном виде
    #После симуляции заполнены объекты cb_epoh_data. Их-то мы тут и финализируем.
    __tablename__ = "simul_dataframes"
    rec_id = Column(Integer, primary_key=True)
    data_frame = Column(PickleType)  #Можно не трачить мутабельность
    var_name = Column(Unicode(255))   #Название переменной
    data_frame_type = Column(Unicode(255))
    observer_name = Column(Unicode(255))     #Адрес переменной - пока открытый вопрос. Пока без адреса, все в корень.

class console_log_printer(object):
    def pr(self, timestamp, sender_name, msg_text):
        msg = ("@[%d] #[%s] : %s"% (timestamp, sender_name, msg_text))
        print(msg)

class list_log_printer(object):
    def __init__(self, log_list):
        self.log_list = log_list

    def pr(self, timestamp, sender_name, msg_text):
        msg = [0,0,0]
        msg[0] = timestamp
        msg[1] = sender_name
        msg[2] = msg_text
        self.log_list += [msg]

# TODO delete this class in next version
class c_sales_budget(BASE):
    #После симуляции, сюда отдельно пишутся ожидания о потреблении клиентами
    #(все записи перетираются при этом)
    __tablename__ = "sales_budget"
    rec_id = Column(Integer, primary_key=True)
    material_rec_id = Column(Integer, ForeignKey('materials.rec_id'))
    material = relationship("c_material")
    client_rec_id = Column(Integer, ForeignKey('agents_clients.rec_id'))
    client = relationship("c_client_model")
    expected_date_of_shipment = Column(DateTime)
    wh_vault_rec_id = Column(Integer, ForeignKey('warehouse_vaults.rec_id'))
    wh_vault = relationship("c_warehouse_vault")
    quantity = Column(SqliteNumeric)
    price = Column(SqliteNumeric)
    payment_terms_rec_id = Column(Integer, ForeignKey('payment_terms.rec_id'))
    payment_terms = relationship("c_payment_terms")

    def csv_header(self):
        return ["date", "material_id", "client_id", "warehouse_id", "payment_cond_id", "quantity", "price"]

    def csv_line(self):
        d = self.expected_date_of_shipment
        sh_date = datetime.date(year = d.year, month = d.month, day = d.day).strftime("%Y.%m.%d")
        l = [sh_date, self.material.account_system_code, self.client.account_system_code]
        l += [self.wh_vault.account_system_code, self.payment_terms.account_system_code , self.quantity, self.price]
        return l

"""<SIMULATION SYSTEM>"""

class c_discrete_event_system():
    #Holder for environment.
    #We start runtime with creating this object
    def __init__(self, simpy_env, real_world_datetime_start):
        #К этим обращаемся напрямую для наглядности
        self.simpy_env = simpy_env
        self.logging_on = True
        self.random_generator = None
        self.__real_world_datetime_start = real_world_datetime_start
        self.log_printers = []

    def init_materials_market(self):
        self.materials_market = c_materials_market(self, self.clients_list, self.trading_firm)

    def convert_datetime_to_simtime(self, a_real_date):
        if not(a_real_date is None):
            return (a_real_date - self.__real_world_datetime_start).days

    def convert_simtime_to_datetime(self, simul_time_days):
        return self.__real_world_datetime_start + datetime.timedelta(days = simul_time_days)

    def nowsimtime(self):
        return self.simpy_env.now

    def define_trading_firm(self, trading_firm):
        self.trading_firm = trading_firm

    def define_clients_list(self, clients_list):
        self.clients_list = clients_list

    def define_macro_market(self, macro_market):
        self.macro_market = macro_market

    def set_seed(self, seed = None):
        if seed is None:
            seed = random.randint(0, sys.maxint)  #Обрати внимание, когда на разных 32/64 запускаешь!
        self.random_generator = random.Random(seed)

    def __check_readiness(self):
        am_i_ready = 1
        if self.random_generator is None:
            am_i_ready = 0
        if self.trading_firm is None:
            am_i_ready = 0
        if self.macro_market is None:
            am_i_ready = 0
        return am_i_ready

    def lastbreath_before_simulation(self):
        #TODO: do a smart global call here (maybe I should kill "prepare_for_simulation"
        for cl_i in self.clients_list:
            cl_i.lastbreath_before_simulation()
        self.trading_firm.lastbreath_before_simulation()
        self.macro_market.lastbreath_before_simulation()

    def my_generator(self):
        #Это самый первый генератор, куда мы заходим
        if self.__check_readiness():
            #Инициализация некоторых виртуальных объектов...
            self.init_materials_market()
            #Объявляем процесс торговли (продажа материалов)
            self.simpy_env.process(self.trading_firm.my_generator())
            #Объявляем процесс спроса со стороны клиентов
            for cl_i in self.clients_list:
                self.simpy_env.process(cl_i.my_generator())
            #Объявляем макроэкономические стат. флуктуации (пока только курсы валют)
            self.simpy_env.process(self.macro_market.my_generator())
            #запускаем рынок для торговли материалами (пока просто передает заказы)
            self.simpy_env.process(self.materials_market.my_generator())
        else:
            raise BaseException("system is not ready")
        yield empty_event(self.simpy_env) #Formality

    @error_decorator
    def sent_log(self, sender_instance, msg_text, msg_priority = 1):
        if self.logging_on: #В каждом принтере (методе) необходимо выключать все вычисления, если logging_on = False
            sender_name = sender_instance.log_repr()  #make this readable in any class
            timestamp = self.nowsimtime()
            for a_pr in self.log_printers:
                a_pr.pr(timestamp, sender_name, msg_text)

    def add_printer(self, a_printer):
        # Куда лог выводить
        self.log_printers += [a_printer]

def empty_event(simpy_env):
    return simpy_env.timeout(0)

class c_trading_firm(BASE, abst_key, connected_to_DEVS):
    #Our company, single record. Conviniet way to keep links for "agent-specific" behaviour.
    __tablename__ = "trading_firms"
    rec_id = Column(Integer, primary_key=True)
    warehouse_rec_id = Column(Integer, ForeignKey('warehouse.rec_id'))
    warehouse = relationship("c_warehouse", foreign_keys=[warehouse_rec_id])
    bank_account_rec_id = Column(Integer, ForeignKey('simul_bank_account.rec_id'))
    bank_account = relationship("c_bank_account", foreign_keys=[bank_account_rec_id])
    main_currency_rec_id = Column(Integer, ForeignKey('currencies.rec_id'))
    main_currency = relationship("c_currency", foreign_keys=[main_currency_rec_id])
    default_wh_vault_rec_id = Column(Integer, ForeignKey('warehouse_vaults.rec_id'))
    default_wh_vault = relationship("c_warehouse_vault", foreign_keys=[default_wh_vault_rec_id])

    def log_repr(self):
        return("Interline")

    def define_main_currency(self, a_ccy):
        # This sets accounting currency.
        self.main_currency = a_ccy

    def define_default_wh_vault(self, a_vault):
        # Отсюда будут генериться просимулированные отгрузки.
        # Это потом может в material flow перекочевать.
        self.default_wh_vault = a_vault

    def define_warehouse(self, a_warehouse):
        self.warehouse = a_warehouse

    def define_bank_account(self, a_bank_account):
        self.bank_account = a_bank_account

    def define_projects_list(self, proj_list):
        self.projects = proj_list

    def define_sell_prices_list(self, sell_prices_list):
        self.sell_prices = sell_prices_list

    def prepare_for_simulation(self):
        self.client_order_gateway = c_client_order_gateway(self, self.devs)
        self.supply_manager = c_supply_manager(self.devs)

    def my_generator(self):
        yield self.devs.simpy_env.process(self.warehouse.my_generator()) #This do some inits
        self.devs.sent_log(self, "warehouse is ready")
        yield self.devs.simpy_env.process(self.bank_account.my_generator())
        self.devs.sent_log(self, "bank account is ready")
        self.devs.simpy_env.process(self.client_order_gateway.my_generator()) #this one works permanentely
        self.devs.sent_log(self, "order gateway is ready")
        # Заказы клиентов всегда поступают от клиентов. Поэтому запускаем все процессы, кроме client_order.
        for proj_i in self.projects:
            if not(proj_i.discriminator in ["client_order"]):
                self.devs.simpy_env.process(proj_i.my_generator())
                self.devs.sent_log(self, "started " + str(proj_i))
        yield empty_event(self.devs.simpy_env) #Formality
        self.devs.sent_log(self, "initialized")

    def recieve_a_client_order(self, new_order, is_approved = 0):
        #Будем пока считать, что принимаем все заказы клиентов
        # UnicodeEncodeError
        #self.devs.sent_log(self, u"recieved " + str(new_order))
        if is_approved:
            #Это напрямую из системы
            self.client_order_gateway.add_order(new_order)
        else:
            #Можно отказать в заказе
            self.client_order_gateway.add_order(new_order)

class c_supply_manager():
    # Виртуальный класс, ответственный за оформление новых заказов поставщику.
    # TODO - пока просто передаю из клиента информацию
    def __init__(self, devs):
        self.devs = devs
        self.to_order = []

    def add_order(self, order):
        self.to_order += [order]

class c_client_order_gateway():
    """
    Это главный менеджер склада. Тут решается, что и когда отгружается. Склад и этапы просто пытаются выполнить указания.
    Здесь все заказы клиентов. Поэтому именно этот класс будет
    назначен ответственным за то, чтобы "подменять" товары.
    При отгрузке, в случае невозможности отгрузить то, что нужно
    этот класс незамедлительно пытается отгрузить любой другой товар
    субститут (у проекта есть параметр substitute_materials, который подбирает материальный поток).
    В этом классе все заказы клиентов уже только с одной строкой (так генерятся, деление существующих в c_client_model)
    """
    def __init__(self, trading_firm, devs):
        self.devs = devs
        self.trading_firm = trading_firm
        self.pending_orders = []  #Не отгрузились
        self.cancelled_orders = [] #Облом
        self.succesful_orders = [] #Отгрузились

    def log_repr(self):
        return "orders_gateway"

    def my_generator(self):
        # Можем оставить этот процесс чисто для подсчета статистики и марщрутизации "остаточных" заказов
        # Ну и, самое главное, для блокировок.
        while 1:
            yield self.devs.simpy_env.timeout(10)
            self.check_pending_orders()
            self.devs.sent_log(self, " pending orders: " + str(len(self.pending_orders)))
            self.devs.sent_log(self, " succesful orders: " + str(len(self.succesful_orders)))
            self.devs.sent_log(self, " cancelled orders: " + str(len(self.cancelled_orders)))

    def add_order(self, order):
        # Все заказы клиентов сначала попадают сюда. Сразу же запускаются, мы лишь их регистрируем.
        order.is_cancelled = False
        self.devs.simpy_env.process(order.my_generator())
        if order.IsShipped:
            self.succesful_orders += [order]
        else:
            self.pending_orders += [order]

    def check_pending_orders(self):
        # Проходит по waiting_orders и превращает в pending_orders те, что с близкой датой отгрузки.
        # Это нужно будет переделать сразу же, как оттестирую сам факт отгрузки.
        indexes_to_pop = []
        for i, ord_i in enumerate(self.pending_orders):
            if ord_i.is_cancelled:
                # отказ клиента.
                indexes_to_pop += [i]
        indexes_to_pop.sort(reverse = 1)
        for i in indexes_to_pop:
            # allow orders to start trying execution - this is a temp. solution
            self.cancelled_orders += [self.pending_orders.pop(i)]

class c_materials_market():
    """
    Все заказы от клиентов попадают сюда. Все заказы принимает одна фирма. Потом можно добавить симуляцию конкуренции.
    """
    def __init__(self, devs, clients_list, trading_firm):
        self.devs = devs
        self.clients = clients_list
        self.trading_firm = trading_firm

    def log_repr(self):
        return "materials_market"

    def put_a_client_order(self, new_order, is_approved = 0):
        #TODO: Тут может быть вероятность того, что мы не пройдем по цене/срокам
        #На самом деле, тут можно просто сделать сравнение требуемых сроков/цены с нашими..
        self.trading_firm.recieve_a_client_order(new_order, is_approved)

    def my_generator(self):
        #we may emit price changes here
        yield empty_event(self.devs.simpy_env)

class c_material_flow(BASE, abst_key, connected_to_DEVS):
    __tablename__ = 'material_flows'
    rec_id = Column(Integer, primary_key=True)
    client_model_rec_id = Column(Integer, ForeignKey('agents_clients.rec_id'))
    client_model = relationship("c_client_model", backref=backref('material_flows', cascade="all,delete"))
    #У material_type есть аттрибут are_materials_equal. Если истина, то заполняем процесс для
    #группы материалов. Если ложь, то для конкретного материала.
    are_materials_equal = Column(Boolean)
    #put_supplier_order_if_not_available = Column(Boolean)
    material_type_rec_id = Column(Integer, ForeignKey('material_types.rec_id'))
    material_type = relationship("c_material_type")
    is_active = Column(Boolean)
    #Параметры нашего нехитрого процесса - явно запишем-ка, потом упростим
    stats_mean_timedelta = Column(SqliteNumeric)  #Ожидаемый интервал между заказами
    stats_std_timedelta = Column(SqliteNumeric) #С.к.о. интервала между заказами
    stats_mean_volume = Column(SqliteNumeric) #Ожидаемое значение объёма заказа
    stats_std_volume = Column(SqliteNumeric)  #Отклонение объёма заказа
    last_shipment_date = Column(DateTime)  #Последняя дата отгрузки (должен обновляться при синхронизации)
    next_expected_shipment_date = Column(DateTime)  #Следующая отгрузка (должен обновляться при синхронизации)
    economy_orders_share = Column(SqliteNumeric)

    def __repr__(self):
        return self.log_repr()

    def log_repr(self):
        return "flow " + unicode(self.material_type) + " -> " + unicode(self.client_model)

    def get_expected_budget_iter(self, horizon_days=180):
        if self.stats_mean_timedelta < 1:
            print("[c_material_flow][get_expected_budget_iter] too small timedelta!")
            self.stats_mean_timedelta = 1

        if self.material_dist is not None:
            tod = datetime.datetime.now()
            # today_with_time = datetime.datetime(year=tod.year, month=tod.month, day=tod.day)
            if self.next_expected_shipment_date is None:
                self.next_expected_shipment_date = datetime.datetime.today()

            too_old = False
            if (self.next_expected_shipment_date - tod).days < -1*horizon_days:
                # хрень с вводом на тестовых данных
                too_old = True

            if (self.next_expected_shipment_date is None) or too_old:
                sh_date = tod
            else:
                sh_date = self.next_expected_shipment_date

            timestep = datetime.timedelta(days=self.stats_mean_timedelta)
            sh = self.economy_orders_share
            if self.economy_orders_share is None:
                sh = 0.0
            while (sh_date - tod).days <= horizon_days:
                for md_i in self.material_dist:
                    material = md_i.material
                    qtty = float(self.stats_mean_volume * md_i.choice_prob)
                    if qtty*sh > 0.01:
                        yield sh_date, material, qtty*sh, True #urgent shipment
                    if qtty*(1-sh) > 0.01:
                        yield sh_date, material, qtty*(1-sh), False #non-urgent shipment
                sh_date = sh_date + timestep

    def get_next_order_date_expectation(self):
        #gui А?
        if self.stats_mean_volume > 0 and self.is_active:
            if not self.next_expected_shipment_date is None:
                return self.next_expected_shipment_date
            else:
                st_date = datetime.date.today()
            if not(self.stats_mean_timedelta is None):
                dT = datetime.timedelta(days = self.stats_mean_timedelta)
                return st_date + dT

    def set_inactive(self):
        #Если по какой-то причине больше не активен - выключаем
        self.is_active = False
        self.stats_mean_timedelta = 0
        self.stats_std_timedelta = 0
        self.stats_mean_volume = 0
        self.stats_std_volume = 0
        self.material_dist = None  #TODO: проверить, удаляются ли.. Хотя с чего вдруг..

    def update_stats(self, dict_with_stats):
        #Look at db_main.estimate_shipment_stats for dict structure
        self.stats_mean_volume = dict_with_stats["qtty_exp"]
        self.stats_std_volume = dict_with_stats["qtty_std"]
        self.stats_mean_timedelta = dict_with_stats["timedelta_exp"]
        self.stats_std_timedelta = dict_with_stats["timedelta_std"]
        #self.stats_last_order_date = dict_with_stats["last_shipment_date"] #last shipment or confirmed order
        if (dict_with_stats["last_shipment_date"] is None) or (dict_with_stats["timedelta_exp"] is None):
            self.next_expected_shipment_date = datetime.datetime.today()
        else:
            timed = datetime.timedelta(days=dict_with_stats["timedelta_exp"])
            nextdate = dict_with_stats["last_shipment_date"] + timed
            self.next_expected_shipment_date = nextdate
        self.rewrite_material_probs_from_dict(dict_with_stats["mat_dist"])

    def rewrite_material_probs_from_dict(self, a_random_dict):
        # Теперь обновляем / создаем c_material_flow_matdist:
        tmp_mat_dict = dict()
        # Заполянем словарик той статистикой, что была в прошлый раз
        for md_i in self.material_dist:
            md_i.choice_prob = 0  #не удаляем - обнуляем.. Потом ручками можно удалить.
            tmp_mat_dict[md_i.material] = md_i
        # Идём по циклу в новой статистике и либо обновляем историю, либо создаём новые инстансы
        for mat_i, prob_i in a_random_dict.write_dict_with_results().iteritems():
            if tmp_mat_dict.has_key(mat_i): #обновляем
                tmp_mat_dict[mat_i].choice_prob = prob_i
            else: #создаем новый (комитится в gui)
                new_md = c_material_flow_matdist(material_flow = self, material = mat_i, choice_prob = prob_i)
                self.material_dist += [new_md]
                tmp_mat_dict[mat_i] = new_md

    def prepare_for_simulation(self):
        if self.disconnected_from_session:
            self.next_expected_shipment_date = self.devs.convert_datetime_to_simtime(self.next_expected_shipment_date)
            self.last_order_num = 0  # при симуляции именуем
            #Собираем случайный словарик - будем по нему материалы разыгрывать
            self.material_dist_dict = c_random_dict()
            for md_i in self.material_dist:
                self.material_dist_dict.add_elem(md_i.material, md_i.choice_prob)
            self.material_dist_dict.finalize() #перестраховка просто

    def my_generator(self):
        while 1:
            sh_time = self.order_sh_time()
            qtty = self.order_qtty()
            dT_before_next_one = 0
            if not(sh_time is None):
                if qtty>0 and sh_time>0:  #TODO: спорный момент с sh_time
                    self.devs.sent_log(self, "new order of " + str(qtty) + " delivery before " + str(sh_time))
                    self.last_order_num += 1
                    self.client_model.generate_new_order(self, sh_time, qtty)
                    dT_before_next_one = sh_time - self.devs.nowsimtime()
            dT_before_next_one = max([dT_before_next_one, 1])
            yield self.devs.simpy_env.timeout(dT_before_next_one)

    def draw_random_materials(self, qtty):
        #Всё довольно хитро. Клиент управляет процессом новых заказов.
        #После того, как my_generator здесь вызвал generate_new_order, клиент обратится сюда и возьмёт
        #набор материалов для такого количества (случайный набор).
        n_of_lots = 50  #заказ разбивается на n_of_lots частей и каждая часть случайно выбирается (конкретный материал)
        qtty_per_lot = float(qtty / n_of_lots)
        materials_dict = dict()
        for k in range(1,n_of_lots):
            #Пропорционально частоте встречаемости разыгрываем взятие товара
            mat_i = self.material_dist_dict.choose_random(self.devs.random_generator)
            if materials_dict.has_key(mat_i):
                materials_dict[mat_i] += qtty_per_lot
            else:
                materials_dict[mat_i] = qtty_per_lot
        return materials_dict

    def order_sh_time(self):
        if self.next_expected_shipment_date is None:
            self.next_expected_shipment_date = 0
        if not((self.stats_mean_timedelta is None) or (self.stats_std_timedelta is None)):
            dT = self.devs.random_generator.normalvariate(self.stats_mean_timedelta, self.stats_std_timedelta)
            dT = max([dT,1])
            new_order_date = self.next_expected_shipment_date
            self.next_expected_shipment_date = new_order_date + dT
            return new_order_date

    def order_qtty(self):
        newQ = 0
        if not((self.stats_mean_volume is None) or (self.stats_std_volume is None)):
            newQ = max([self.devs.random_generator.normalvariate(self.stats_mean_volume, self.stats_std_volume),0])
        return newQ

    def is_material_inside(self, material):
        if material.material_type == self.material_type:
            return 1
        else:
            return 0

    def get_substitute_list(self):
        # Когда клиент размещает заказ, он идет на склад и проверяет, есть ли он.
        # Если его нет, проверяет альтернативы по этому списку.
        subst_list = []
        if self.are_materials_equal:
            for md_i in self.material_dist:
                subst_list += [md_i.material]
        else:
            subst_list = []
        return subst_list

    def get_volume_std_in_proc(self):
        if self.stats_std_volume is not None:
            if self.stats_std_volume >0:
                return (self.stats_std_volume/self.stats_mean_volume) * 100
        return 0

    def set_volume_std_from_proc(self, std_in_proc):
        # std_in_proc - стандартное отклонение, выраженное в процентах от ожидания.
        if self.stats_mean_volume is not None:
            self.stats_std_volume = (std_in_proc * self.stats_mean_volume) / 100
        else:
            self.stats_std_volume = 0

class c_material_flow_matdist(BASE, abst_key,connected_to_DEVS):
    #Отвечает за выбор конкретного материала в табличке с материальными потоками.
    __tablename__ = 'material_flow_matdist'
    rec_id = Column(Integer, primary_key=True)
    material_flow_rec_id = Column(Integer, ForeignKey('material_flows.rec_id'))
    material_flow = relationship("c_material_flow", backref=backref('material_dist', cascade="all,delete"))
    material_rec_id = Column(Integer, ForeignKey('materials.rec_id'))
    material = relationship("c_material")
    choice_prob = Column(SqliteNumeric)

class c_sales_oppotunity(BASE, abst_key, connected_to_DEVS):
    # Задаёт возможное появление потока потребления в будущем
    __tablename__ = 'sales_oppotunities'
    rec_id = Column(Integer, primary_key=True)
    material_type_rec_id = Column(Integer, ForeignKey('material_types.rec_id'))
    material_type = relationship("c_material_type")
    client_model_rec_id = Column(Integer, ForeignKey('agents_clients.rec_id'))
    client_model = relationship("c_client_model", backref=backref('sales_oppotunities', cascade="all,delete"))
    success_prob = Column(SqliteNumeric) # Вероятность того, что возьмут.
    sure_level = Column(SqliteNumeric) # Насколько уверены в показаниях клиента.
    expected_qtty = Column(SqliteNumeric) # Ожидаемый объём разового заказа
    expected_timedelta = Column(SqliteNumeric) # Ожидаемая регулярность
    expected_start_date_from = Column(DateTime) # Стартовая дата
    expected_start_date_till = Column(DateTime) # Стартовая дата
    instock_promise = Column(Boolean)

    def get_dummy_copy(self):
        my_dummy_copy = c_dummy(self)
        # TODO: проверить, что колонки превращается в значения
        my_dummy_copy.fix_attrs(["success_prob", "expected_qtty", "expected_timedelta", "expected_start_date_from",
                                 "expected_start_date_till", "instock_promise", "sure_level"])
        return my_dummy_copy

    def log_repr(self):
        return "oppotunity " + unicode(self.material_type) + " -> " + unicode(self.client_model)

    def prepare_for_simulation(self):
        if self.disconnected_from_session:
            self.expected_start_date = self.devs.convert_datetime_to_simtime(self.expected_start_date_from)

    def my_generator(self):
        time_till_try = self.expected_start_date # TODO: на случайную величину
        yield self.devs.simpy_env.timeout(self.expected_start_date)
        if self.devs.random_generator.uniform(0,1) > (1-self.success_prob):
            # Сделка получилась. Иначе - облом.
            self.devs.sent_log(self, "start of sales!")
            new_matflow = self.create_matflow_sim()
            self.devs.simpy_env.process(new_matflow.my_generator())

    def create_matflow_sim(self):
        # Создаём поток потребления.
        new_matflow = c_material_flow()
        new_matflow.next_expected_shipment_date = self.devs.nowsimtime()
        new_matflow.client_model = self.client_model
        new_matflow.material_type = self.material_type
        new_matflow.is_active = True
        new_matflow.stats_mean_timedelta = self.expected_timedelta # TODO: на случайную величину
        new_matflow.put_supplier_order_if_not_available = not(self.instock_promise)
        new_matflow.stats_mean_volume = self.expected_qtty #TODO: на случайную величину
        # Чтобы заполнить иные параметры, смотрим на существующие matflow.
        # Если таковых нет.. То равновероятно всё.
        matfl_dist = c_random_dict()
        av_timedelta_std = 0.
        av_qtty_std = 0.
        eq_mat = [0.0,0.0] #first for True, second for False
        c = 0
        are_mat_eq = False
        for cl_i in self.devs.clients_list:
            for mf_i in cl_i.material_flows:
                if mf_i.material_type == self.material_type:
                    c += 1
                    #Немного статистики здесь - считаем, сколько какого товара потребляют в месяц.
                    for m_i in mf_i.material_dist:
                        q = m_i.choice_prob * mf_i.stats_mean_volume / mf_i.stats_mean_timedelta #Потребление в день
                        matfl_dist.add_elem(m_i, q) # На самом деле, метод считает
                    av_timedelta_std += mf_i.stats_std_timedelta
                    av_qtty_std += mf_i.stats_std_volume
                    if mf_i.are_materials_equal:
                        eq_mat[0] +=1
                    else:
                        eq_mat[1] +=1
        if c > 0: #Финализируем
            av_timedelta_std = av_timedelta_std / float(c)
            av_qtty_std = av_qtty_std / float(c)
            are_mat_eq = eq_mat[0] > eq_mat[1]
        elif c == 0:
            # Случай, когда нету подходящих аналогов потребления
            for m_i in self.material_type.materials: #выбор материалов равновероятен
                matfl_dist.add_elem(m_i)
            av_timedelta_std = new_matflow.stats_mean_timedelta * 0.33
            av_qtty_std = new_matflow.stats_mean_volume * 0.33
            are_mat_eq = False #TODO: поправить, когда будут "потребляемые"
        matfl_dist.finalize()
        new_matflow.rewrite_material_probs_from_dict(matfl_dist)
        new_matflow.stats_std_timedelta = av_timedelta_std
        new_matflow.stats_std_volume = av_qtty_std
        new_matflow.are_materials_equal = are_mat_eq
        return new_matflow

    def combine_concrete_materials_list(self):
        # Поскольку ввести сразу распределение материалов нереально, прикидываем его.
        pass

class c_warehouse(BASE, abst_key, connected_to_DEVS):
    #Одиночка
    __tablename__ = 'warehouse'
    rec_id = Column(Integer, primary_key=True)
    #trading_firm_rec_id = Column(Integer, ForeignKey('trading_firms.rec_id'))
    #trading_firm = relationship("c_trading_firm", backref=backref('projects'))
    #inventory = Column(MutableDict.as_mutable(PickleType)) #Mutabca надо трачить мутабельность

    def __repr__(self):
        s = u"A [c_warehouse] with materials:\n"
        for pos_i in self.positions:
            material = pos_i.material
            qtty = pos_i.qtty
            s += "\t" + unicode(material.material_name) + " : " + str(qtty) + "\n"
        return s

    def log_repr(self):
        return "warehouse"

    def add_position(self, material, vault, qtty, cost):
        if qtty>0 and cost>=0:
            #TODO: maybe we should drop this table during simulation
            pos_i = c_warehouse_position(material = material, vault = vault, acc_code = "41",
                                         qtty = qtty, cost = cost)
            self.positions += [pos_i]
            # TODO: delete the code below. Looks obsolete.
            # if self.inventory is None:
            # 	self.inventory = dict()
            # if not(hasattr(self, "vaults")):
            # 	self.valuts = []
            # key_i = (material, vault)
            # pos_i = dict()
            # pos_i["qtty"] = qtty
            # pos_i["cost"] = cost
            # pos_i["profit"] = profit
            # if self.inventory.has_key(key_i):
            # 	pos_i_old = self.inventory[key_i]
            # 	pos_i["qtty"] += pos_i_old["qtty"]
            # 	pos_i["cost"] += pos_i_old["cost"]
            # 	pos_i["profit"] += pos_i_old["profit"]
            # self.inventory[key_i] = pos_i
        else:
            self.devs.sent_log(self, "[c_warehouse] - an attempt to add negative cost / qtty, material: " + material.material_name + " @ " + vault.vault_name)

    def set_to_zero(self):
        #Обнуление - при синхронизации
        self.inventory = None

    def prepare_for_simulation(self):
        #На основе словаря с товарами строим словарь с контейнерами SimPy
        self.inventory = dict()
        for posit_i in self.positions:
            key_i = (posit_i.material, posit_i.vault)
            pos_i = dict()
            pos_i["qtty"] = posit_i.qtty
            pos_i["cost"] = posit_i.cost
            pos_i["profit"] = 0
            if self.inventory.has_key(key_i):
                pos_i_old = self.inventory[key_i]
                pos_i["qtty"] += pos_i_old["qtty"]
                pos_i["cost"] += pos_i_old["cost"]
                pos_i["profit"] += pos_i_old["profit"]
            self.inventory[key_i] = pos_i
        for v in self.inventory.itervalues():
            v["cont"] = simpy.Container(self.devs.simpy_env)

    def my_generator(self):
        # Каждый товар теперь берется из контейнера.
        yield self.devs.simpy_env.process(self.init_containers())

    def init_containers(self):
        for inv_i in self.inventory.itervalues():
            qtty_i = inv_i["qtty"]
            cont_i = inv_i["cont"]
            yield cont_i.put(qtty_i) # No logic behind blocking
        yield empty_event(self.devs.simpy_env)

    def check_qtty(self, material, vault):
        if self.inventory.has_key((material, vault)):
            return self.inventory[(material, vault)]["qtty"]
        else:
            return 0

    def check_cost(self, material, vault):
        if self.inventory.has_key((material, vault)):
            return self.inventory[(material, vault)]["cost"]
        else:
            return 0

    def do_ship_out(self, material, vault, qtty, revenue = 0):
        #TODO: profits are not so simple
        #TODO: it is very important to account for the moment of profit - we have many processes here...
        #a simple instruction - a generator. The only way to do a shipment out.
        k = (material, vault)
        if not(self.inventory.has_key(k)):
            self.inventory[k] = dict(qtty = 0, cost = 0, cont = simpy.Container(self.devs.simpy_env), profit = 0)
        self.devs.sent_log(self, "shipping out %d of %s from %s"% (qtty,unicode(material),unicode(vault)))
        #self.devs.sent_log(self, "shipping out %d of %s from %s"(qtty,"material here","vault_here"))
        yield self.inventory[k]["cont"].get(qtty) #we go further only if we succeed to take here
        cost = self.calculate_cost_of_qtty(k, qtty)
        self.inventory[k]["qtty"] -= qtty  #just to account for
        self.inventory[k]["cost"] -= cost
        profits = revenue - cost
        self.inventory[k]["profit"] += profits
        self.devs.sent_log(self, "%s is shipped, profits: %d"% (unicode(material),profits))

    def do_ship_in(self, material, vault, qtty, cost):
        #a simple instruction - a generator. The only way to do a shipment in.
        k = (material, vault)
        if not(self.inventory.has_key(k)):
            self.inventory[k] = dict(qtty = 0, cost = 0, cont = simpy.Container(self.devs.simpy_env), profit = 0)
        self.devs.sent_log(self, "recieving %d of %s to %s"%(qtty,unicode(material),unicode(vault)))
        yield self.inventory[k]["cont"].put(qtty) #we go further only if we succeed to put here
        self.inventory[k]["qtty"] += qtty  #just to account for
        self.inventory[k]["cost"] += cost

    def do_a_move_vault_to_vault(self, material, qtty, vault_from, vault_to):
        k_from = (material, vault_from)
        k_to = (material, vault_to)
        if not(self.inventory.has_key(k_from)):
            self.inventory[k_from] = dict(qtty = 0, cost = 0, cont = simpy.Container(self.devs.simpy_env))
        if not(self.inventory.has_key(k_to)):
            self.inventory[k_to] = dict(qtty = 0, cost = 0, cont = simpy.Container(self.devs.simpy_env))
        #take the inventory
        yield self.inventory[k_from]["cont"].get(qtty)
        cost = self.calculate_cost_of_qtty(k_from, qtty)
        self.inventory[k_from]["qtty"] -= qtty
        self.inventory[k_from]["cost"] -= cost
        #put the inventory
        yield self.inventory[k_to]["cont"].put(qtty)
        self.inventory[k_to]["qtty"] += qtty
        self.inventory[k_to]["cost"] += cost
        self.devs.sent_log(self, "%d of %s moved %s -> %s"(qtty, str(material), str(vault_from), str(vault_to)))

    def do_add_costs(self, material, vault, costs):
        # adds direct costs
        self.inventory[(material, vault)]["costs"] += costs

    def calculate_cost_of_qtty(self, inv_key, qtty):
        #Считает себестоимость количества.
        total_qtty = self.inventory[inv_key]["qtty"]
        total_cost = self.inventory[inv_key]["cost"]
        if qtty == 0 or total_qtty == 0:
            cost_of_qtty = 0
        else:
            cost_price = total_cost/total_qtty
            cost_of_qtty = qtty * cost_price
        return cost_of_qtty

class c_warehouse_position(BASE, abst_key, connected_to_DEVS):
    __tablename__ = 'warehouse_positions'
    rec_id = Column(Integer, primary_key=True)
    warehouse_rec_id = Column(Integer, ForeignKey('warehouse.rec_id'))
    warehouse = relationship("c_warehouse", backref=backref('positions', cascade="all,delete"))
    meterial_rec_id = Column(Integer, ForeignKey('materials.rec_id'))
    material = relationship("c_material")
    vault_rec_id = Column(Integer, ForeignKey('warehouse_vaults.rec_id'))
    vault = relationship("c_warehouse_vault")
    acc_code = Column(Unicode(255)) # Строка типа 41.01 или 41.04
    qtty = Column(SqliteNumeric)
    cost = Column(SqliteNumeric) #БУ

class c_bank_account(BASE, abst_key, connected_to_DEVS):
    #Одиночка
    __tablename__ = 'simul_bank_account'
    rec_id = Column(Integer, primary_key=True)
    money = Column(MutableDict.as_mutable(PickleType))

    def __repr__(self):
        return "bank account"

    def log_repr(self):
        return "bank account"

    @error_decorator
    def add_position(self, ccy, amount):
        if self.money is None:
            self.money = dict()
        if self.money.has_key(ccy):
            pos_i = self.money[ccy]
            pos_i["amount"] += amount
        else:
            pos_i = dict()
            pos_i["amount"] = amount
            self.money[ccy] = pos_i

    def set_to_zero(self):
        #Обнуление - при синхронизации
        self.money = None

    def prepare_for_simulation(self):
        #На основе словаря с товарами строим словарь с контейнерами SimPy
        for v in self.money.itervalues():
            v["cont"] = simpy.Container(self.devs.simpy_env)

    def my_generator(self):
        yield self.devs.simpy_env.process(self.init_containers())

    def init_containers(self):
        if len(self.money.keys()) > 0:
            for ccy, d in self.money.iteritems():
                yield self.devs.simpy_env.process(self.add_money(ccy,d["amount"]))
        else:
            yield empty_event(self.devs.simpy_env)

    @error_decorator
    def add_money(self, ccy, ccy_amount):
        if ccy_amount > 0:
            if not(self.money.has_key(ccy)):
                new_cont = simpy.Container(self.devs.simpy_env)
                self.money[ccy] = dict(amount = ccy_amount, cont = new_cont)
            yield self.money[ccy]["cont"].put(ccy_amount)  #this shedules an event
            self.money[ccy]["amount"] += ccy_amount
            self.devs.sent_log(self, "add %d %s"% (ccy_amount, unicode(ccy)))

    @error_decorator
    def take_money(self, ccy, ccy_amount):
        if not(self.money.has_key(ccy)):
            new_cont = simpy.Container(self.devs.simpy_env)
            self.money[ccy] = dict(amount = ccy_amount, cont = new_cont)
        self.devs.sent_log(self, "try to take %d %s"% (ccy_amount, unicode(ccy)))
        if ccy_amount > self.money[ccy]["amount"]: #Не хватает
            rub_ccy = self.devs.trading_firm.main_currency
            ins_vol = ccy_amount - self.money[ccy]["amount"]
            if ccy == rub_ccy: # Inform and proceed - we'll let container do the job
                self.devs.sent_log(self, "insufficient %d %s"% (ins_vol, unicode(ccy)))
            else:  # we shedule buying some currency and proceed
                # we may delete "yield" here
                yield self.devs.simpy_env.process(self.buy_ccy(ccy, ins_vol))
        yield self.money[ccy]["cont"].get(ccy_amount)  #this shedules an event
        self.money[ccy]["amount"] -= ccy_amount
        self.devs.sent_log(self, "took %d %s"% (ccy_amount, unicode(ccy)))

    @error_decorator
    def buy_ccy(self, ccy_buy, qtty_buy):
        # TODO: Если делать нечего или хандра напала, можно определить финансовый рынок/банк и выполнять там операции
        #Покупка "валюты" за рубли
        self.devs.sent_log(self, "request to buy %d %s"% (qtty_buy, ccy_buy))
        if not(self.money.has_key(ccy_buy)):
            new_cont = simpy.Container(self.devs.simpy_env)
            self.money[ccy_buy] = dict(amount = ccy_amount, cont = new_cont)
        #Процесс покупки
        #Простая логика. Сначала продаем все рубли. Если не хватает, продаем другие валюты.
        #Если не хватает, через день по второму кругу.
        rub_ccy = self.devs.trading_firm.main_currency
        money_bought = 0
        while money_bought < qtty_buy:
            #TODO - вставить проверку на то, что, пока покупаем валюту, деньги пришли и покупать больше не надо.
            RUBCCY_buy_quote = self.devs.macro_market.get_ccy_buy_quote(ccy_buy) #Почем можно купить валюту
            avail_roubles = self.get_money_level(rub_ccy)
            if avail_roubles >= (qtty_buy-money_bought)*RUBCCY_buy_quote:
                #Можем сразу всю сумму за рубли купить
                money_to_buy = (qtty_buy-money_bought)
                rouble_to_sell = money_to_buy * RUBCCY_buy_quote
                yield self.devs.simpy_env.process(self.take_money(rub_ccy, rouble_to_sell))
                yield self.devs.simpy_env.process(self.add_money(ccy_buy,money_to_buy))
                self.devs.sent_log(self, "sold %d %s, bought %d %s"% (rouble_to_sell, rub_ccy, money_to_buy, ccy_buy))
                money_bought += money_to_buy
            else:
                #Не можем сразу всю сумму купить
                #Продаем рубли
                if avail_roubles > 0:
                    rouble_to_sell = avail_roubles
                    money_to_buy = rouble_to_sell / RUBCCY_buy_quote
                    yield self.devs.simpy_env.process(self.take_money(rub_ccy, rouble_to_sell))
                    yield self.devs.simpy_env.process(self.add_money(ccy_buy,money_to_buy))
                    self.devs.sent_log(self, "sold %d %s, bought %d %s"% (rouble_to_sell, rub_ccy, money_to_buy, ccy_buy))
                    money_bought += money_to_buy
                #Смотрим остатки по другим валютам
                for a_ccy, d in self.money.iteritems():
                    if a_ccy <> rub_ccy and a_ccy <> ccy_buy:
                        another_ccy_level = d["amount"]
                        if another_ccy_level>0 and money_bought < ccy_qtty_to_buy:
                            #Находим кросс-курс через покупку-продажу рубля
                            #Еще раз узнаем курс - yield выше мог занять время
                            RUBCCY_buy_quote = self.devs.macro_market.get_ccy_buy_quote(ccy_name_to_buy)
                            RUBAnotherCCY_buy_quote = the_system.macro_market.get_ccy_buy_quote(a_ccy)
                            #Наглядный пересчет суммы:
                            avail_RUB_eq = another_ccy_level * RUBAnotherCCY_buy_quote
                            need_RUB_eq = (ccy_qtty_to_buy-money_bought) * RUBCCY_buy_quote
                            if avail_RUB_eq >= need_RUB_eq:
                                #Хватает другой валюты, покупаем все
                                money_to_buy = (ccy_qtty_to_buy-money_bought)
                                money_to_sell_anoth_ccy = money_to_buy * RUBCCY_buy_quote / RUBAnotherCCY_buy_quote
                            else:
                                #Не хватает другой валюты - продаем что есть
                                money_to_sell_anoth_ccy = another_ccy_level
                                money_to_buy = money_to_sell_anoth_ccy * RUBAnotherCCY_buy_quote / RUBCCY_buy_quote
                            yield self.devs.simpy_env.process(self.take_money(a_ccy, money_to_sell_anoth_ccy))
                            yield self.devs.simpy_env.process(self.add_money(ccy_buy,money_to_buy))
                            self.devs.sent_log(self, "sold %d %s, bought %d %s"% (money_to_sell_anoth_ccy, a_ccy, money_to_buy, ccy_name_to_buy))
                            money_bought += money_to_buy
                if money_bought < ccy_qtty_to_buy:
                    self.devs.sent_log(self, "bought %d %s out of %d %s and out of money"% (money_bought, ccy_buy, qtty_buy, ccy_buy))
                    yield the_system.env.timeout(1) #Ждем один день - и снова по всему циклу

    @error_decorator
    def get_money_level(self, ccy):
        if self.money.has_key(ccy):
            return self.money[ccy]["amount"]
        else:
            return 0

    @error_decorator
    def get_rouble_m2m_level(self):
        all_money_level = 0
        for ccy, v_i in self.money.iteritems():
            ccy_rate = self.devs.macro_market.get_ccy_quote(ccy)
            all_money_level += v_i["amount"]*ccy_rate
        return all_money_level

    def get_money_names(self):
        # Не имена, а сами инстансы - изменил чуток..
        return self.money.keys()

class c_macro_market(BASE, abst_key, connected_to_DEVS):
    #Пока костыль с рублем - потом лучше матрицу кросс-курсов сделать
    #Одиночка
    __tablename__ = 'simul_macro_market'
    rec_id = Column(Integer, primary_key=True)
    #Словарик текущих курсов к рублю, их волатильности
    ccy_quotes = Column(MutableDict.as_mutable(PickleType)) #Mutabca надо трачить мутабельность
    #сcy - ссылка на c_currency, buy - почем можно купить,
    #sell - почем можно продать, stdev - волатильность

    def log_repr(self):
        return "market"

    def my_generator(self):
        if self.devs.logging_on:
            self.devs.simpy_env.process(self.log_printer())
        while 1:
            yield self.devs.simpy_env.process(self.day_step())

    def log_printer(self):
        while 1:
            yield self.devs.simpy_env.timeout(10)
            for k,v in self.ccy_quotes.iteritems():
                if str(k) <> "RUB":
                    av_rate = (v["buy"]+v["sell"])/2
                    self.devs.sent_log(self, "%s is %d"%(str(k), av_rate))

    def add_ccy_quote(self, ccy, buy, sell, stdev):
        if self.ccy_quotes is None:
            self.ccy_quotes = dict()
        quote_i = dict(ccy = ccy, buy = buy, sell = sell, stdev = stdev)
        self.ccy_quotes[ccy] = quote_i

    def get_ccy_buy_quote(self, ccy):
        return self.ccy_quotes[ccy]["buy"]

    def get_ccy_sell_quote(self, ccy):
        return self.ccy_quotes[ccy]["sell"]

    def get_ccy_quote(self, ccy):
        b = self.ccy_quotes[ccy]["buy"]
        s = self.ccy_quotes[ccy]["sell"]
        return (b+s)/2

    def get_ccy_list(self):
        return self.ccy_quotes.keys()

    def day_step(self):
        yield self.devs.simpy_env.timeout(1)
        for q_i in self.ccy_quotes.itervalues():
            buy_i = q_i["buy"]
            sell_i = q_i["sell"]
            stdev_i = q_i["stdev"]
            price_i = (sell_i + buy_i)/2
            spread = price_i - sell_i
            dr = self.devs.random_generator.normalvariate(0,stdev_i)
            newprice = price_i*(1+dr)
            q_i["buy"] = newprice + spread
            q_i["sell"] = newprice - spread

    def convert_rate(self,ccy_from,ccy_to):
        # sum_ccy_to = sum_ccy_from * convert_rate
        fr_r = self.get_ccy_quote(ccy_from)
        to_r = self.get_ccy_quote(ccy_to)
        rt = fr_r / to_r
        return rt

""" В проектах и их этапах сосредоточено много логики """

class c_project(BASE, abst_key, connected_to_DEVS):
    __tablename__ = 'projects'
    discriminator = Column(Unicode(50))
    __mapper_args__ = {'polymorphic_identity':'base_project', 'polymorphic_on': discriminator}
    rec_id = Column(Integer, primary_key=True)
    is_completed = Column(Boolean)
    root_step_rec_id = Column(Integer)
    root_step = relationship("c_step", cascade="all,delete", uselist=False, foreign_keys = [root_step_rec_id], primaryjoin = "c_project.root_step_rec_id==c_step.rec_id", post_update=True)
    trading_firm_rec_id = Column(Integer, ForeignKey('trading_firms.rec_id'))
    trading_firm = relationship("c_trading_firm", backref=backref('projects'))

    def log_repr(self):
        return unicode(self.project_name)

    def init_root(self, root_step = None):
        #any step could be a root.
        if root_step is None:
            root_step = c_step(step_name = "root", is_scheduled = 0)
        root_step.project = self
        self.root_step = root_step

    def add_step(self, a_step, parent_step = None):
        a_step.project = self
        if parent_step is None:
            a_step.parent_step = self.root_step
            self.root_step.add_child_step(a_step)
        else:
            parent_step.add_child_step(a_step)

    def iter_steps_depth(self):
        # iterates all the steps
        if self.root_step is not None:
            for st_i in self.root_step.iter_subtree():
                yield st_i

    def update_status(self):
        is_cmpl = 1
        for st_i in self.iter_steps_depth():
            if not(st_i.is_completed):
                is_cmpl = 0
                break
        self.is_completed = is_cmpl

    def prc_completed(self):
        all_num_of_steps = 0
        completed_steps = 0
        for st_i in self.all_steps:
            all_num_of_steps += 1
            if st_i.is_completed:
                completed_steps += 1
        ans = completed_steps / all_num_of_steps
        return ans

    def prepare_for_simulation(self):
        pass

    def my_generator(self):
        yield self.devs.simpy_env.process(self.root_step.my_generator())

    def set_completed(self):
        for st_i in self.iter_steps_depth():
            st_i.set_completed()
        self.is_completed = 1

    def set_uncompleted(self):
        for st_i in self.iter_steps_depth():
            st_i.set_uncompleted()
        self.is_completed = 0

    #GUI
    def get_min_step_date(self):
        min_date = None
        for st_i in self.iter_steps_depth():
            if min_date is None:
                min_date = st_i.planned_time_expected
            elif st_i.planned_time_expected < min_date:
                min_date = st_i.planned_time_expected
        return min_date

    def get_max_step_date(self):
        max_date = None
        for st_i in self.iter_steps_depth():
            if max_date is None:
                max_date = st_i.planned_time_expected
            elif st_i.planned_time_expected > max_date:
                max_date = st_i.planned_time_expected
        return max_date

    def get_first_expected_event_date(self):
        min_date = None
        for st_i in self.iter_steps_depth():
            if not(st_i.is_completed):
                if min_date is None:
                    min_date = st_i.planned_time_expected
                elif st_i.planned_time_expected < min_date:
                    min_date = st_i.planned_time_expected
        return min_date

class c_project_order(c_project):
    # This is a generic order. The thing that client order and supplier order have in common
    # Здесь определяется куча общих атрибутов и пара методов для работы с таблицей товаров
    __tablename__ = 'projects_orders'
    __mapper_args__ = {'polymorphic_identity': 'orders'}
    rec_id = Column(Integer, ForeignKey('projects.rec_id'), primary_key=True)
    account_system_code = Column(Unicode(255))
    AgreementName = Column(Unicode(255, convert_unicode = True))        #Спецификация
    DocDate = Column(DateTime)
    DateShipmentScheduled = Column(DateTime)
    DateFactShipment = Column(DateTime)
    IsShipped = Column(Boolean)
    MadePrepayments = Column(SqliteNumeric)  #В валюте заказа - для синхронизации
    MadePostpayments = Column(SqliteNumeric)
    payment_terms_type_rec_id = Column(Integer, ForeignKey("payment_terms.rec_id"))
    payment_terms = relationship("c_payment_terms")

    def log_repr(self):
        return unicode(u"Generic order " + self.AgreementName)

    def __repr__(self):
        return self.log_repr()

    def prepare_for_simulation(self):
        if self.disconnected_from_session:
            self.DocDate = self.devs.convert_datetime_to_simtime(self.DocDate)
            self.DateShipmentScheduled = self.devs.convert_datetime_to_simtime(self.DateShipmentScheduled)
            self.DateFactShipment = self.devs.convert_datetime_to_simtime(self.DateFactShipment)

    def add_position(self, material, qtty, price, vat_rate):
        # Проверяем, есть ли такой материал уже. Если есть, добавляем.
        # Если там другая цена или ставка НДС - то не добавляем, будет две позиции.
        # Эта логика используется только в self.synchronize_positions_with_a_list - при синхронизации уже существующих позиций.
        # При симуляции этот массив состоит из одного элемента всегда (как единица работы).
        # Уникальный "ключ" строки - set (material, str(price), str(vat_rate))
        the_key = (material, price, vat_rate)
        key_exists = 0
        k = 0
        while not(key_exists) and k<=(len(self.goods)-1):
            a_pos = self.goods[k]
            a_key = (a_pos.material, a_pos.price, a_pos.vat_rate)
            if a_key == the_key:
                # Меняем существующую позицию и выходим из цикла
                key_exists = 1
                a_pos.qtty += qtty
            k += 1
            a_pos.qtty_left = qtty  #Сколько осталось отгрузить
        if not(key_exists):
            new_position = c_order_position(material = material, qtty = qtty, qtty_left = qtty,
                                            price = price, vat_rate = vat_rate)
            self.goods += [new_position]

    def synchronize_positions_with_a_list(self, list_with_items):
        # В отличие от add_position, синхронизирует себя со списком:
        # [material, qtty, price, vat_rate]
        # Уникальный "ключ" строки - set (material, str(price), str(vat_rate))
        # Потом можно еще упаковку добавить.
        dict_pos = dict()  #промежуточный словарик, куда сворачиваем сырой list_with_items
        for pos_list_i in list_with_items:
            a_key = (pos_list_i[0], pos_list_i[2], pos_list_i[3])
            if dict_pos.has_key(a_key):
                dict_pos[a_key] += pos_list_i[1]
            else:
                dict_pos[a_key] = pos_list_i[1]
        # Теперь, используя словарь dict_pos, проверяем, что все позиции совпадают со словарём.
        indexes_to_delete = []  # сюда будем складывать те, которых не было в list_with_items.
        found_keys = []
        # Сначала ищем то, что в нашей базе лишнее, а в 1С есть, и правим количества
        for i, pos_i in enumerate(self.goods):
            pos_key = (pos_i.material, pos_i.price, pos_i.vat_rate)
            if dict_pos.has_key(pos_key):
                if pos_i.qtty <> dict_pos[pos_key]:
                    pos_i.qtty = dict_pos[pos_key]
                del dict_pos[pos_key]  #Мы нашли этот ключ и сделали все корректировки. Можно забыть об этой позиции.
            else:   #Придется позицию удалить. Так как речь идет о БД, сохраним их до следующего цикла.
                indexes_to_delete += [i]
        indexes_to_delete.sort(reverse = 1) #делаем pop с конца
        # Всё, что осталось в словаре, можно в базу добавлять.
        # Чтобы не плодить мусор (прежде всего, в базе), меняем сперва позиции из indexes_to_delete (с первого)
        new_positions = [] # нельзя пока индексы в self.goods трогать
        for k, qtty in dict_pos.iteritems():
            if len(indexes_to_delete) > 0: #берем из стека к удалению
                i = indexes_to_delete.pop(0)
                pos_i = self.goods[i]
            else: #новый делаем
                pos_i = c_order_position()
                new_positions += [pos_i]
            pos_i.material = k[0]
            pos_i.price = k[1]
            pos_i.vat_rate = k[2]
            pos_i.qtty = qtty
        # Теперь удаляем лишние и оставшиеся (если дело происходит во время симуляции, то обращения к the_session_handler не будет
        # А если вдруг и будет, то приведет к ошибке.
        for i in indexes_to_delete:
            pos_to_del = self.goods.pop(i)
            #TODO: проверить, что действительно не остаётся в базе подвешенных позиций и что всё работает без этого:
            # if hasattr(self,"disconnected_from_session"):
            # 	if not(self.disconnected_from_session):
            # 		the_session_handler.delete_concrete_object(pos_to_del)
            # else:  #Значит, еще не в симуляции - тогда точно надо удалять
            # 	the_session_handler.delete_concrete_object(pos_to_del)
            pos_to_del = None
        # Ну и теперь примешаем новые позиции
        self.goods += new_positions

    def get_order_cost(self):
        v = 0
        #current_rate = self.devs.macro_market.get_ccy_buy_quote(self.payment_terms.ccy_quote)
        for pos_i in self.goods:
            v += pos_i.qtty * pos_i.price #* current_rate
        return v

class c_order_position(BASE, abst_key, connected_to_DEVS):
    #TODO: упаковки придется добавить для какой-никакой реалистичности. Потом.
    __tablename__ = 'order_position'
    rec_id = Column(Integer, primary_key=True)
    material_rec_id = Column(Integer, ForeignKey('materials.rec_id'))
    material = relationship("c_material")
    order_rec_id = Column(Integer, ForeignKey('projects_orders.rec_id'))
    order = relationship("c_project_order", backref=backref('goods', cascade="all,delete"))
    qtty = Column(SqliteNumeric)
    qtty_left = Column(SqliteNumeric)  #Zero if everything is shipped
    price = Column(SqliteNumeric)
    vat_rate = Column(SqliteNumeric)

    def __repr__(self):
        return unicode(u"position %s in qtty %d"% (self.material.material_name, self.qtty))

    def get_clone(self):
        new_order_position = c_order_position()
        new_order_position.material = material
        new_order_position.client_model = client_model
        new_order_position.qtty = qtyy
        new_order_position.price = price
        new_order_position.vat_rate = vat_rate

class c_project_client_order(c_project_order):
    __tablename__ = 'projects_client_order'
    __mapper_args__ = {'polymorphic_identity': 'client_order'}
    rec_id = Column(Integer, ForeignKey('projects_orders.rec_id'), primary_key=True)
    try_to_order = Column(Boolean) #Если истина, то при отсутствии товара попытается заказать у поставщика
    client_model_rec_id = Column(Integer, ForeignKey("agents_clients.rec_id"))
    client_model = relationship("c_client_model", backref=backref("active_orders", cascade = "all,delete"))

    def log_repr(self):
        return u"Client order " + unicode(self.client_model.name) + u":" + unicode(self.AgreementName)

    def get_clone(self, what_to_do_with_positions = 0):
        # TODO: красивей было бы определить для родителя и доопределить тут. Но пока оно не нужно.
        # Клонирование полезно при отгрузке - когда грузим частями. Тогда заказ просто дробится.
        new_proj = c_project_client_order()
        #Общие параметры - вот это и клонирование дерева можно в родительский класс.
        new_proj.is_completed = self.is_completed
        new_proj.trading_firm = self.trading_firm
        #Клонирование дерева
        new_proj.init_root(self.root_step.get_clone())  #там в иерархии вызывается клонирование
        #Специфичные параметры
        new_proj.AgreementName = self.AgreementName
        new_proj.DocDate = self.DocDate
        new_proj.DateShipmentScheduled = self.DateShipmentScheduled
        new_proj.DateFactShipment = self.DateFactShipment
        new_proj.IsShipped = self.IsShipped
        new_proj.try_to_order = self.try_to_order
        new_proj.MadePrepayments = self.MadePrepayments
        new_proj.MadePostpayments = self.MadePostpayments
        new_proj.client_model = self.client_model
        new_proj.payment_terms = self.payment_terms
        new_proj.goods = []
        if hasattr(self,"devs"):
            new_proj.devs = self.devs
            new_proj.disconnected_from_session = self.disconnected_from_session
        if what_to_do_with_positions == 0:  #omit
            pass
        elif what_to_do_with_positions == 1:  #clone
            for pos_i in self.goods:
                new_proj.goods += [pos_i.get_clone()]
        elif what_to_do_with_positions == 2:  #relink
            for pos_i in self.goods:
                new_proj.goods += [pos_i]
        return new_proj

    def build_order_steps(self, random_possible_delay_shipment = 10, random_possible_delay_payment = 15, during_simulation = False):
        steps_prepay = []
        steps_postpay = []
        #Отгрузка
        st_sh = c_step_shipment_out(is_completed = False, is_scheduled = 1, planned_time_expected = self.DateShipmentScheduled,
                                    step_name = unicode(u"отгрузка"), qtty_shipped = 0)
        st_sh.planned_time_possible_delay = random_possible_delay_shipment  #Случайная задержка отгрузки до 10ти дней.
        if during_simulation:
            st_sh.s_set_devs(self.devs)
            st_sh.disconnected_from_session = True
            #st_sh.randomize_date()
        #Предоплаты
        for tup_i in self.payment_terms.payterm_stages.get_prepayments():
            st_i = c_step_payment_in(is_completed = False, is_scheduled = 1)
            if during_simulation:
                delay_time = tup_i[0]
            else:
                delay_time = datetime.timedelta(days = tup_i[0])
            st_i.planned_time_expected = self.DateShipmentScheduled + delay_time
            st_i.planned_time_possible_delay = random_possible_delay_payment  #Случайная задержка предоплаты
            st_i.pay_proc = tup_i[1]
            st_i.step_name = unicode(u"предоплата " + str(round(st_i.pay_proc)) + u"%")
            if during_simulation:
                st_i.s_set_devs(self.devs)
                st_i.disconnected_from_session = True
                #st_i.randomize_date()
            steps_prepay.append(st_i)
        #Постоплаты
        for tup_i in self.payment_terms.payterm_stages.get_postpayments():
            st_i = c_step_payment_in(is_completed = False, is_scheduled = 1)
            if during_simulation:
                delay_time = tup_i[0]
            else:
                delay_time = datetime.timedelta(days = tup_i[0])
            st_i.planned_time_expected = self.DateShipmentScheduled + delay_time
            st_i.planned_time_possible_delay = random_possible_delay_payment  #Случайная задержка постоплаты - можно рейтинг ввести..
            st_i.pay_proc = tup_i[1]
            st_i.step_name = unicode(u"постоплата " + str(round(st_i.pay_proc)) + u"%")
            if during_simulation:
                st_i.s_set_devs(self.devs)
                st_i.disconnected_from_session = True
                #st_i.randomize_date()
            steps_postpay.append(st_i)
        #Кидаем этапы в дерево проекта - здесь определяется очередность
        self.init_root()  #Этап-пустышка
        if during_simulation:
            self.root_step.s_set_devs(self.devs)
        steps_prepay.sort(key = lambda d: d.planned_time_expected, reverse = False)
        for i, st_i in enumerate(steps_prepay):
            if i==0: self.add_step(st_i)
            else: self.add_step(steps_prepay[i-1],st_i)  #Каждая предоплата подчинена предыдущей по графику
        if len(steps_prepay)>0: #
            self.add_step(st_sh, st_i)  #Вот тут не хватает полноценной Petri.. Но и так неплохо.
        else:
            self.add_step(st_sh)
        for st_i in steps_postpay:  #Постоплаты запускаются параллельно - не дожидаюстя друг друга.
            self.add_step(st_i, st_sh)

    def refresh_order_steps(self):
        #TODO: Вот это не такая простая задача. Надо вернуться.
        """self.MadePrepayments
        self.MadePostpayments
        for st_i in self.root_step.children_steps:
            if st_i.discriminator == "shipment":
                if self.IsShipped:
                    st_i.set_completed()"""
        pass

    def prepare_for_simulation(self):
        super(c_project_client_order, self).prepare_for_simulation()

    def my_generator(self):
        msg = "executing client order"
        if not(hasattr(self,"devs")):
            print "DEVS is LOST!!!"
        self.devs.sent_log(self, msg)
        #parent_generator = super(c_project_client_order, self).my_generator
        #yield self.devs.simpy_env.process(parent_generator()) #parent
        yield self.devs.simpy_env.process(self.root_step.my_generator())

    def split_client_order_by_items(self):
        # Один заказ превращается в несколько - в каждом по одному наименованию товара.
        # Необходимо для того, чтобы привести заказ из системы к виду генерируемого заказа.
        # Все генерируемые заказы этой обратки не проходят (но проходят split_client_order_by_qtty)
        # Так проще отгружать частями (см. следующий метод) - нет блокировок процесса, если нет какого-то одного товара.
        after_split = []
        if len(self.goods) == 1:  #if 0 there should be an error somewhere..
            #nothing to split
            after_split += [self]
        else:
            #первый элемент пойдет этому же проекту (чтобы лишних ссылок не плодить..)
            tmp_pos = self.goods.pop(0)
            for pos_i in self.goods:
                new_proj = self.get_clone(what_to_do_with_positions = 0)  #omit positions during cloning
                #Вот тут придётся обо всех связях помнить - алхимия уже убрана.
                new_proj.goods += [pos_i]
                pos_i.client_order = new_proj
                new_proj.client_model.active_orders += [new_proj]  #Вот это вызывало досадную ошибку
                after_split += [new_proj]
            self.goods = []
            self.goods += [tmp_pos]  #!!! Тут мы не добавляем
            after_split += [self]
        #В общем-то, все заказы можно получить из клиента.. Но мы их вернем.
        return after_split

class c_project_supplier_order(c_project_order):
    __tablename__ = 'projects_supplier_order'
    __mapper_args__ = {'polymorphic_identity': 'supplier_order'}
    rec_id = Column(Integer, ForeignKey('projects_orders.rec_id'), primary_key=True)
    supplier_model_rec_id = Column(Integer, ForeignKey('agents_suppliers.rec_id'))
    supplier_model = relationship("c_supplier_model", backref=backref('active_orders'))
    parent_shipment_project_rec_id = Column(Integer, ForeignKey('projects_import_shipment.rec_id'))
    parent_shipment_project = relationship("c_project_import_shipment", backref=backref('supplier_orders'))

    def log_repr(self):
        return u"Supplier order " + self.supplier_model.name + ":" + self.AgreementName

    def build_order_steps(self, random_possible_delay_shipment = 10, random_possible_delay_payment = 15):
        #TODO: недоделка!!
        steps_prepay = []
        steps_postpay = []
        #Отгрузка
        st_sh = c_step_shipment_in(is_completed = False, is_scheduled = 1, planned_time_expected = self.DateShipmentScheduled, step_name = unicode(u"поступление"))
        st_sh.planned_time_possible_delay = random_possible_delay_shipment  #Случайная задержка отгрузки до 10ти дней.
        #Предоплаты
        for tup_i in self.payment_terms.payterm_stages.get_prepayments():
            st_i = c_step_payment_out(is_completed = False, is_scheduled = 1)
            delay_time = datetime.timedelta(days = tup_i[0])
            st_i.planned_time_expected = self.DateShipmentScheduled + delay_time
            st_i.planned_time_possible_delay = random_possible_delay_payment  #Случайная задержка предоплаты
            st_i.pay_proc = tup_i[1]
            st_i.step_name = unicode(u"prepayment " + str(round(st_i.pay_proc)) + u"%")
            steps_prepay.append(st_i)
        #Постоплаты
        for tup_i in self.payment_terms.payterm_stages.get_postpayments():
            st_i = c_step_payment_out(is_completed = False, is_scheduled = 1)
            delay_time = datetime.timedelta(days = tup_i[0])
            st_i.planned_time_expected = self.DateShipmentScheduled + delay_time
            st_i.planned_time_possible_delay = random_possible_delay_payment  #Случайная задержка постоплаты - можно рейтинг ввести..
            st_i.pay_proc = tup_i[1]
            st_i.step_name = unicode(u"deferment of payment " + str(round(st_i.pay_proc)) + u"%")
            steps_postpay.append(st_i)
        #Кидаем этапы в дерево проекта - здесь определяется очередность
        #TODO А давайте простенькую таможню сделаем - за 5 дней до поступления.
        self.init_root()  #Этап-пустышка
        for st_i in steps_prepay:
            self.add_step(st_i)
        if len(steps_prepay)>0:
            self.add_step(st_sh, st_i)
        else:
            self.add_step(st_sh)
        for st_i in steps_postpay:
            self.add_step(st_i, st_sh)

    def refresh_order_steps(self):
        pass

    def prepare_for_simulation(self):
        super(c_project_supplier_order, self).prepare_for_simulation()

    def my_generator(self):
        msg = "executing supplier order"
        self.devs.sent_log(self, msg)
        parent_generator = super(c_project_supplier_order, self).my_generator
        yield self.devs.simpy_env.process(parent_generator()) #parent
        yield empty_event(self.devs.simpy_env)

class c_project_import_shipment(c_project):
    # Другая ветка развития моей идеи с проектами
    __tablename__ = 'projects_import_shipment'
    __mapper_args__ = {'polymorphic_identity': 'import_shipment'}
    rec_id = Column(Integer, ForeignKey('projects.rec_id'), primary_key=True)
    account_system_code = Column(Unicode(255))

class c_step(BASE, abst_key, connected_to_DEVS):
    #Base class for all steaps
    __tablename__ = 'steps'
    discriminator = Column(Unicode(50))
    __mapper_args__ = {'polymorphic_identity':'base_step', 'polymorphic_on': discriminator}
    rec_id = Column(Integer, primary_key=True)
    is_completed = Column(Boolean)
    is_scheduled = Column(Boolean)  #Если False, то не обращает внимания на даты - просто запускает, не думая.
    planned_time_expected = Column(DateTime)
    planned_time_possible_delay = Column(SqliteNumeric) #days - always and everywhere
    step_name = Column(Unicode(255))
    project_rec_id = Column(Integer, ForeignKey('projects.rec_id'))
    project = relationship("c_project", backref=backref('all_steps', cascade="all,delete"))
    parent_step_rec_id = Column(Integer, ForeignKey('steps.rec_id'))
    children_steps = relationship("c_step", cascade="all,delete", backref=backref('parent_step', remote_side = [rec_id]))

    def __repr__(self):
        return self.discriminator + " " + str(self.rec_id)

    def get_children(self):
        return self.children_steps

    def get_parent(self):
        return self.parent_step

    def iter_subtree(self):
        for st_i in self.children_steps:
            yield st_i
            for st_ij in st_i.iter_subtree():
                yield st_ij

    def add_child_step(self, a_step):
        self.children_steps += [a_step]

    def log_repr(self):
        return self.project.log_repr() + " : " + self.step_name

    def set_completed(self):
        self.is_completed = 1

    def set_uncompleted(self):
        # TODO: проверка подчинённых - что-то поумней дерева надо сделать...
        self.is_completed = 0

    def get_clone(self, new_project = None, with_sublings = 1):
        #Вот это можно переделывать в каждом потомке
        new_step = c_step()
        self.clone_basic(new_step, new_project)
        if with_sublings:
            self.clone_structure(new_step, new_project)
        return new_step

    def clone_structure(self, inst_clone, new_project = None):
        inst_clone.children_steps = []
        for st_i in self.children_steps:
            inst_clone.add_child_step(st_i.get_clone(new_project, 1))

    def clone_basic(self, inst_clone, new_project = None):
        #Чтобы классы-наследники могли себя клонировать..
        inst_clone.is_completed = self.is_completed
        inst_clone.is_scheduled = self.is_scheduled
        inst_clone.planned_time_expected = self.planned_time_expected
        inst_clone.planned_time_possible_delay = self.planned_time_possible_delay
        inst_clone.step_name = self.step_name
        if hasattr(self, "devs"):
            inst_clone.devs = self.devs
            inst_clone.disconnected_from_session = self.disconnected_from_session
            # if self.is_scheduled:  # see randomize_date
            # 	inst_clone.planned_time = self.planned_time
        if new_project: #новый проект (вызов из клонирования проекта
            inst_clone.project = new_project
        else:
            inst_clone.project = self.project

    def prepare_for_simulation(self):
        if self.disconnected_from_session:
            if self.is_scheduled:
                self.planned_time_expected = self.devs.convert_datetime_to_simtime(self.planned_time_expected)
                #self.randomize_date()

    def randomize_date(self):
        #TODO: do something clever with time randomization
        t_0 = int(self.planned_time_expected)
        t_1 = int(t_0 + self.planned_time_possible_delay)
        self.planned_time = self.devs.random_generator.randint(t_0, t_1)

    def my_generator(self):
        # delay simulation
        yield self.devs.simpy_env.process(self.run_step_timeout())
        self.devs.sent_log(self, "start logic")
        # specific logic
        yield self.devs.simpy_env.process(self.step_logic())
        self.devs.sent_log(self, "logic done")
        # child steps
        self.devs.sent_log(self, "child starting")
        yield self.devs.simpy_env.process(self.run_child_steps())

    def step_logic(self):
        yield empty_event(self.devs.simpy_env)

    def run_step_timeout(self):
        if self.is_scheduled:
            self.randomize_date()
            till_step = max([self.planned_time - self.devs.nowsimtime(),0])
            self.devs.sent_log(self, "waiting for " + str(till_step))
            yield self.devs.simpy_env.timeout(till_step)
        else:
            yield empty_event(self.devs.simpy_env)

    def run_child_steps(self):
        for st_i in self.children_steps:
            self.devs.simpy_env.process(st_i.my_generator())
            yield empty_event(self.devs.simpy_env)

class c_step_shipment_in(c_step):
    __tablename__ = 'steps_shipment_in'
    __mapper_args__ = {'polymorphic_identity': 'shipment_in'}
    rec_id = Column(Integer, ForeignKey('steps.rec_id'), primary_key=True)
    #define any specific fields here

    def get_clone(self, new_project = None, with_sublings = 1):
        new_step = c_step_shipment_in()
        self.clone_basic(new_step, new_project)
        if with_sublings:
            self.clone_structure(new_step, new_project)
        return new_step

    def step_logic(self):
        self.devs.sent_log(self, "recieving %s"% (self.project.AgreementName))
        #Запускаем процесс отгрузки. Он может поменять сам заказ, если товара нет.
        # vault = self.project.wh_vault
        # for pos_i in self.project.goods:
        # 	material = pos_i.material
        # 	qtty = pos_i.qtty
        # 	cost = pos_i.price * qtty * self.calc_current_cost_calc_rate()  # Вот чтобы курсы были нормальными, нужно учет вводить. Всё реально.
        # 	yield self.devs.simpy_env.process(self.project.trading_firm.warehouse.do_ship_in(material, vault, qtty, cost))
        yield empty_event(self.devs.simpy_env)

    def calc_current_cost_calc_rate(self):
        return self.devs.macro_market.get_ccy_quote(self.project.payment_terms.ccy_quote)

class c_step_shipment_out(c_step):
    __tablename__ = 'steps_shipment_out'
    __mapper_args__ = {'polymorphic_identity': 'shipment_out'}
    rec_id = Column(Integer, ForeignKey('steps.rec_id'), primary_key=True)
    #define any specific fields here
    qtty_shipped = Column(SqliteNumeric)

    def get_clone(self, new_project = None, with_sublings = 1):
        new_step = c_step_shipment_out()
        new_step.qtty_shipped = self.qtty_shipped
        self.clone_basic(new_step, new_project)
        if with_sublings:
            self.clone_structure(new_step, new_project)
        return new_step

    def step_logic(self, time_waited = 0):
        max_wait_time = 15
        if len(self.project.goods)>1:
            raise BaseException("There should be only one item per order here")
        base_material = self.get_item()
        qtty_to_ship = self.get_qtty()
        price_for_shipment = self.get_price()
        if hasattr(self.project, "substitute_materials"):
            subst_list = self.project.substitute_materials
        else:
            subst_list = []
        self.devs.sent_log(self, u"shipment of %d units %s"% (qtty_to_ship, unicode(base_material)))
        #Запускаем процесс отгрузки.
        #Волты, которые надо проверить - все доступные к exw
        vaults_to_check = []
        for v_i in self.project.devs.trading_firm.warehouse.vaults:
            if v_i.is_available_exw:
                vaults_to_check += [v_i]
        #Цикл проверки наличия
        materials_to_try = [base_material] + subst_list
        time_start = self.devs.nowsimtime() - time_waited  #Когда началась стартовая отгрузка
        not_shipped = True
        while not_shipped and time_waited <= max_wait_time:
            for mat_i in materials_to_try:
                qtty_available_by_vault = dict()
                for v_i in vaults_to_check:
                    qtty_available_by_vault[v_i] = self.project.devs.trading_firm.warehouse.check_qtty(mat_i, v_i)
                for v_i, av_qtty in qtty_available_by_vault.iteritems():
                    if qtty_to_ship > 0 and av_qtty > 0:
                        if av_qtty > qtty_to_ship: qtty_sh = qtty_to_ship
                        else: qtty_sh = av_qtty
                        revenue = qtty_sh * price_for_shipment * self.calc_current_cost_calc_rate()
                        # TODO: а прям тут "проводки" по счетам - прибыль и налоги и посчитаем...
                        yield self.devs.simpy_env.process(self.devs.trading_firm.warehouse.do_ship_out(mat_i, v_i, qtty_sh))
                        self.devs.sent_log(self, "%s in qtty %d - shipment done, waiting time: %d"%
                                           (mat_i.material_name, qtty_sh, time_waited))
                        qtty_to_ship -= qtty_sh
                        self.project.goods[0].qtty_left -= qtty_sh
                        self.qtty_shipped += qtty_sh
                        not_shipped = False #Этот этап перейдет в оплаты. Что уж отгрузится.
            yield self.devs.simpy_env.timeout(1) #Ждем - вдруг завтра получится отгрузиться
            time_waited = self.devs.nowsimtime() - time_start
        if qtty_to_ship > 0 and time_waited <= max_wait_time:  #Если отгрузилось, но не всё, то ветвим проект.
            self.devs.sent_log(self, "partly shipped waiting for %d of %s"% (qtty_to_ship, base_material.material_name))
            self.devs.simpy_env.process(self.split_and_run(time_waited))
        elif qtty_to_ship > 0 and time_waited > max_wait_time:
            revenue = qtty_to_ship * price_for_shipment * self.calc_current_cost_calc_rate()
            self.devs.sent_log(self, "gone due to long waiting time - no %s available, lost revenue %d RUB"%
                               (base_material.material_name, revenue))
            self.project.is_cancelled = True #Это для статистики чисто.. Ну и потом для блокировок товара.
            yield empty_event(self.devs.simpy_env)
        elif qtty_to_ship == 0:
            self.devs.sent_log(self, "shipped all ordered qtty of %s"%(base_material.material_name))
            self.project.IsShipped = True
            yield empty_event(self.devs.simpy_env)

    def split_and_run(self, time_already_waited):
        #Если товара не хватает на складе, запускаем это.
        new_sh_step = self.get_clone(new_project = self.project, with_sublings = 1) #Можно и без параметров
        yield self.devs.simpy_env.process(new_sh_step.step_logic(time_already_waited))

    def calc_current_cost_calc_rate(self):
        return self.devs.macro_market.get_ccy_quote(self.project.payment_terms.ccy_quote)

    def get_item(self):
        return self.project.goods[0].material

    def get_qtty(self):
        if len(self.project.goods)>1:
            raise BaseException("There should be only one item per order here")
        return self.project.goods[0].qtty_left

    def get_price(self):
        return self.project.goods[0].price

class c_step_payment_in(c_step):
    __tablename__ = 'steps_payment_in'
    __mapper_args__ = {'polymorphic_identity': 'payment_in'}
    rec_id = Column(Integer, ForeignKey('steps.rec_id'), primary_key=True)
    #define any specific fields here
    pay_proc = Column(SqliteNumeric)

    def get_clone(self, new_project = None, with_sublings = 1):
        new_step = c_step_payment_in()
        new_step.pay_proc = self.pay_proc
        self.clone_basic(new_step, new_project)
        if with_sublings:
            self.clone_structure(new_step, new_project)
        return new_step

    def step_logic(self):
        # Собираем информацию для платежа. Если родительский этап есть и отгрузка, то берем количество и дату из неё.


        # Пока предположим, что по курсу на дату оплаты
        v = 0
        current_rate = self.devs.macro_market.get_ccy_buy_quote(self.project.payment_terms.ccy_quote)
        for pos_i in self.project.goods:
            v += pos_i.qtty * pos_i.price * current_rate
        sum = v * self.pay_proc * 0.01
        ccy_pay = self.project.payment_terms.ccy_pay
        self.devs.sent_log(self, "recivable of %d %s"% (sum, ccy_pay))
        if sum > 0:
            yield self.devs.simpy_env.process(self.devs.trading_firm.bank_account.add_money(ccy_pay, sum))
        else:
            self.devs.sent_log(self, "ERROR - trying to add zero or negative sum")
            yield empty_event(self.devs.simpy_env)

class c_step_payment_out(c_step):
    __tablename__ = 'steps_payment_out'
    __mapper_args__ = {'polymorphic_identity': 'payment_out'}
    rec_id = Column(Integer, ForeignKey('steps.rec_id'), primary_key=True)
    #define any specific fields here
    pay_proc = Column(SqliteNumeric)

    def get_clone(self, new_project = None, with_sublings = 1):
        new_step = c_step_payment_out()
        new_step.pay_proc = self.pay_proc
        self.clone_basic(new_step, new_project)
        if with_sublings:
            self.clone_structure(new_step, new_project)
        return new_step

    def step_logic(self):
        v = 0
        ccy_quote = self.project.payment_terms.ccy_quote
        ccy_pay = self.project.payment_terms.ccy_pay
        if ccy_quote<>ccy_pay:
            current_rate = self.devs.macro_market.get_ccy_buy_quote(self.project.payment_terms.ccy_quote)
        else:
            current_rate = 1
        for pos_i in self.project.goods:
            v += pos_i.qtty * pos_i.price * current_rate
        sum = v * self.pay_proc * 0.01
        self.devs.sent_log(self, "payment of %d %s"% (sum, ccy_pay))
        yield self.devs.simpy_env.process(self.devs.trading_firm.bank_account.take_money(ccy_pay, sum))

class c_step_defined_payment(c_step):
    # Этап оплаты из системы - почти самостоятельный объект. Один класс на получение и на оплату.
    # Это когда не нужна чёткая привязка к underlying проекту по суммам.
    __tablename__ = 'steps_defined_payment'
    __mapper_args__ = {'polymorphic_identity': 'defined_payment'}
    account_system_code = Column(Unicode(255))
    rec_id = Column(Integer, ForeignKey('steps.rec_id'), primary_key=True)
    is_incoming = Column(Boolean) # Если истина, то приход. Иначе - расход.
    pay_sum = Column(SqliteNumeric)
    # Не уверен, что такое есть:
    payterm_rec_id = Column(Integer, ForeignKey('payment_terms.rec_id'))
    payterm = relationship("c_payment_terms")

class c_step_wh_movement(c_step):
    # Со склада на склад
    __tablename__ = 'steps_wh_movement'
    __mapper_args__ = {'polymorphic_identity': 'wh_movement'}
    account_system_code = Column(Unicode(255))
    rec_id = Column(Integer, ForeignKey('steps.rec_id'), primary_key=True)
    vault_from_rec_id = Column(Integer, ForeignKey('warehouse_vaults.rec_id'))
    vault_from = relationship("c_warehouse_vault", foreign_keys=[vault_from_rec_id])
    vault_to_rec_id = Column(Integer, ForeignKey('warehouse_vaults.rec_id'))
    vault_to = relationship("c_warehouse_vault", foreign_keys=[vault_to_rec_id])

class c_step_shipment_service(c_step):
    __tablename__ = 'steps_sh_service'
    __mapper_args__ = {'polymorphic_identity': 'sh_service'}
    account_system_code = Column(Unicode(255))
    rec_id = Column(Integer, ForeignKey('steps.rec_id'), primary_key=True)
    cost = Column(SqliteNumeric)
    vat_rate = Column(SqliteNumeric)
    description = Column(Unicode(255))
    payterm_rec_id = Column(Integer, ForeignKey('payment_terms.rec_id'))
    payterm = relationship("c_payment_terms")
    logistics_agent_rec_id = Column(Integer, ForeignKey('agents_logistic.rec_id'))
    logistics_agent = relationship("c_logistic_agent_model")

class c_step_customs_clearance(c_step):
    __tablename__ = 'steps_customs_clear'
    __mapper_args__ = {'polymorphic_identity': 'customs_clear'}
    account_system_code = Column(Unicode(255))
    rec_id = Column(Integer, ForeignKey('steps.rec_id'), primary_key=True)
    duty_sum = Column(SqliteNumeric)
    vat_sum = Column(SqliteNumeric)
    customs_agent_rec_id = Column(Integer, ForeignKey('agents.rec_id'))
    customs_agent = relationship("c_agent")


""" Агенты: клиенты, поставщики, логисты """

class c_agent(BASE, abst_key, connected_to_DEVS):
    # TODO: обогатить логику агента договорами и учётной системой (отражение наших операций)
    # Любой контрагент
    __tablename__ = 'agents'
    discriminator = Column(Unicode(50))
    __mapper_args__ = {'polymorphic_identity':'agent', 'polymorphic_on': discriminator}
    rec_id = Column(Integer, primary_key=True)
    name = Column(Unicode(255))
    full_name = Column(Unicode(255))
    inn = Column(Unicode(255))   #Возможно, несколько через ";"
    account_system_code = Column(Unicode(255))  #Возможно, несколько через ";"

    def __repr__(self):
        return unicode(self.name)

    def log_repr(self):
        return unicode(self.name)

    def hashtag_name(self):
        return u"#" + sanitize_to_hashtext(unicode(self.name))

    def prepare_for_simulation(self):
        pass

class c_supplier_model(c_agent):
    #nothing to simulate here..
    __tablename__ = 'agents_suppliers'
    __mapper_args__ = {'polymorphic_identity': 'supplier'}
    rec_id = Column(Integer, ForeignKey('agents.rec_id'), primary_key=True)

    def prepare_for_simulation(self):
        pass

    def my_generator(self):
        pass

class c_client_model(c_agent):
    __tablename__ = 'agents_clients'
    __mapper_args__ = {'polymorphic_identity': 'client'}
    rec_id = Column(Integer, ForeignKey('agents.rec_id'), primary_key=True)

    def update_stats_on_material_flows(self, list_with_stats_dict):
        #Синхронизируем по списку словарей список mat_flow
        existing_mfs  = dict()
        for mf_i in self.material_flows:
            existing_mfs[mf_i.material_type] = mf_i
        for dict_mf_i in list_with_stats_dict:
            gr = dict_mf_i["material_type"]
            if not(existing_mfs.has_key(gr)):
                existing_mfs[gr] = c_material_flow(client_model=self, are_materials_equal=1,
                                                   put_supplier_order_if_not_available=0, material_type=gr)
            existing_mfs[gr].update_stats(dict_mf_i)
            existing_mfs.pop(gr)
        #Все, кто остались в словаре existing_mfs подлежат обнулению - их нет в статистике
        for mf_i in existing_mfs.itervalues():
            mf_i.set_inactive

    def prepare_for_simulation(self):
        #Так было проще - может, и быстрей
        self.material_flows_dict = dict()
        for mf_i in self.material_flows:
            #TODO  - проверка в GUI, что у клиента не задваиваются мат. потоки
            self.material_flows_dict[mf_i.material_type] = mf_i
        self.sell_prices_dict = dict()
        for pr_i in self.sell_prices:
            #TODO  - проверка в GUI, что у клиента одна и только одна цена на товар
            if not(pr_i.is_for_group):
                self.sell_prices_dict[pr_i.material] = pr_i
            else:
                self.sell_prices_dict[pr_i.material_type] = pr_i
        #TODO: rebuild with accounting model (when implemented)
        self.order_stats_by_material_qtty = dict()
        self.order_stats_by_material_sum = dict()
        self.order_stats_by_material_group_qtty = dict()
        self.order_stats_by_material_group_sum = dict()
        self.order_stats_total = 0

    def lastbreath_before_simulation(self):
        #Slice the orders!
        before_slice = []
        sliced_orders = []
        # TODO Вот тут уже ссылка на devs в active_orders потеряна. ПОЧЕМУ?
        for ord_i in self.active_orders:
            before_slice += [ord_i]
        for ord_i in before_slice:  # метод ord_i.split_client_order_by_items() меняет self.active_orders
            sliced_orders += ord_i.split_client_order_by_items()
        self.active_orders = sliced_orders

    def my_generator(self):
        #Отправляем все принятые клиентские заказы
        for ord_i in self.active_orders:
            self.add_signed_order_to_queque(ord_i)
        #Запускаем генераторы новых заказов
        for mf_i in self.material_flows:
            self.devs.simpy_env.process(mf_i.my_generator())
        yield empty_event(self.devs.simpy_env)

    def add_signed_order_to_queque(self, order_proj):
        #This is the first entry point for any signed client order (constructed as с_project)
        material_i = order_proj.goods[0].material  #the only item available
        #Возможно, динамически подвязывать этот список - не лучшее решение. Но это свойство заказа, не товара.
        subst_list = self.get_substitute_list_for_material(material_i)
        order_proj.substitute_materials = subst_list  #Динамическая привязка аттрибута
        self.send_order_to_market(order_proj, 1)

    def send_order_to_market(self, order_proj, is_approved = 0):
        self.count_order_statistics(order_proj)
        self.devs.materials_market.put_a_client_order(order_proj, is_approved)

    def count_order_statistics(self, new_order):
        #apply to any new generated order
        for pos_i in new_order.goods:
            if not(self.order_stats_by_material_qtty.has_key(pos_i.material)):
                self.order_stats_by_material_qtty[pos_i.material] = 0
                self.order_stats_by_material_sum[pos_i.material] = 0
            if not(self.order_stats_by_material_group_qtty.has_key(pos_i.material.material_type)):
                self.order_stats_by_material_group_qtty[pos_i.material.material_type] = 0
                self.order_stats_by_material_group_sum[pos_i.material.material_type] = 0
            self.order_stats_by_material_qtty[pos_i.material] += pos_i.qtty
            self.order_stats_by_material_sum[pos_i.material] += pos_i.price*pos_i.price
            self.order_stats_by_material_group_qtty[pos_i.material.material_type] += pos_i.qtty
            self.order_stats_by_material_group_sum[pos_i.material.material_type] += pos_i.price*pos_i.price
            self.order_stats_total += pos_i.price*pos_i.price

    def generate_new_order(self, material_flow, shipment_time, qtty):
        #Вызывается из материального потока
        #Кидаем товар в order_gateway
        order_name_pre = "order " + unicode(self.name) + " gen" + str(material_flow.last_order_num)
        try_to_order = material_flow.put_supplier_order_if_not_available #Заказывать ли, если нет на складе
        #Выбираем товар на основе данных в material_flow
        subst_list = material_flow.get_substitute_list()
        concrete_materials = material_flow.draw_random_materials(qtty)  #набираем случайную "руку"
        k = 1
        for con_mat_i in concrete_materials.keys():
            res = self.get_price_and_payterms(con_mat_i)
            if res is not None:
                [pr, pay_terms] = res
                vat_rate = 0.18
                #TODO: всё-таки, так собирать не дело. Надо какую-то схему придумать. А то всё ваще забыл передать.
                new_order = c_project_client_order()
                new_order.client_model = self
                new_order.devs = self.devs
                new_order.AgreementName = order_name_pre + "/" + str(k) +  ""
                k += 1
                new_order.DocDate = self.devs.nowsimtime()
                new_order.DateShipmentScheduled = shipment_time
                new_order.IsShipped = 0
                new_order.payment_terms = pay_terms
                new_order.substitute_materials = subst_list
                new_order.add_position(con_mat_i, qtty, pr, vat_rate)
                new_order.disconnected_from_session = True  #TODO: надо бы схему посимпатичней для этого придумать..
                new_order.build_order_steps(during_simulation = True)
                self.send_order_to_market(new_order, 0)
                #self.devs.sent_log(self,("new order %s, ship at %d"% ((unicode(new_order)), shipment_time)))
                s = "new order %s "%(new_order.AgreementName)
                s += "%d of %s for %d per unit "%(qtty, unicode(con_mat_i), pr)
                s += "shipment in %d days"%(round(shipment_time - self.devs.nowsimtime()))
                self.devs.sent_log(self,s)
            else:
                self.devs.sent_log(self,("failed to generate order from %s - no price available"% (unicode(self.name))))

    def get_substitute_list_for_material(self, material):
        """
        Вызывается только для тех заказов, которые уже есть в системе (при генерации то же самое делается, но в методе.
        Подбирает материальный поток, в котором есть такой материал и проверяет, взаимозаменяем ли товар.
        """
        subst_list = []
        if self.material_flows_dict.has_key(material.material_type):
            mf_i = self.material_flows_dict[material.material_type]
            if mf_i.is_material_inside(material):
                subst_list = mf_i.get_substitute_list()
        return subst_list

    def get_price_and_payterms(self, material):
        #0 - price, 1 - payterms
        #Ищем цену
        if self.sell_prices_dict.has_key(material):
            a_price_obj = self.sell_prices_dict[material]  #simulation.c_sell_price
        elif self.sell_prices_dict.has_key(material.material_type):  #пробуем найти цену для группы товаров
            a_price_obj = self.sell_prices_dict[material.material_type]
        else: #Цены нет
            a_price_obj = None
        if not(a_price_obj is None):
            pr = a_price_obj.price_value
            pay_term = a_price_obj.payterm
            return [pr, pay_term]

class c_logistic_agent_model(c_agent):
    # Логисты
    __tablename__ = 'agents_logistic'
    __mapper_args__ = {'polymorphic_identity': 'logistic'}
    rec_id = Column(Integer, ForeignKey('agents.rec_id'), primary_key=True)

    def prepare_for_simulation(self):
        pass

    def lastbreath_before_simulation(self):
        pass

class c_finance_agent_model(c_agent):
    # Логисты
    __tablename__ = 'agents_finance'
    __mapper_args__ = {'polymorphic_identity': 'financier'}
    rec_id = Column(Integer, ForeignKey('agents.rec_id'), primary_key=True)

    def prepare_for_simulation(self):
        pass

    def lastbreath_before_simulation(self):
        pass

class c_customs_agent_model(c_agent):
    # Логисты
    __tablename__ = 'agents_customs'
    __mapper_args__ = {'polymorphic_identity': 'customs'}
    rec_id = Column(Integer, ForeignKey('agents.rec_id'), primary_key=True)

    def prepare_for_simulation(self):
        pass

    def lastbreath_before_simulation(self):
        pass

class c_toller_agent_model(c_agent):
    # Логисты
    __tablename__ = 'agents_tollers'
    __mapper_args__ = {'polymorphic_identity': 'toller'}
    rec_id = Column(Integer, ForeignKey('agents.rec_id'), primary_key=True)

    def prepare_for_simulation(self):
        pass

    def lastbreath_before_simulation(self):
        pass

""" Поведение не симулируется (но с доступом к devs, как и все) """

class c_warehouse_vault(BASE, abst_key, connected_to_DEVS):
    #В понимании 1С - склад
    __tablename__ = 'warehouse_vaults'
    rec_id = Column(Integer, primary_key=True)
    account_system_code = Column(Unicode(255))
    vault_name = Column(Unicode(255))
    is_available_exw = Column(Boolean)
    warehouse_rec_id = Column(Integer, ForeignKey('warehouse.rec_id'))
    warehouse = relationship("c_warehouse", backref=backref('vaults'), foreign_keys=[warehouse_rec_id])

    def __repr__(self):
        return unicode(self.vault_name)

class c_material(BASE, abst_key, connected_to_DEVS):
    __tablename__ = 'materials'
    rec_id = Column(Integer, primary_key=True)
    account_system_code = Column(Unicode(255))
    material_name = Column(Unicode(255))
    material_type_rec_id = Column(Integer, ForeignKey('material_types.rec_id'))
    material_type = relationship("c_material_type", backref=backref('materials'), foreign_keys=[material_type_rec_id])
    material_type_acc_rec_id = Column(Integer, ForeignKey('material_types_accounting.rec_id'))
    material_type_acc = relationship("c_material_type_accounting", backref=backref('materials'), foreign_keys=[material_type_acc_rec_id])
    measure_unit = Column(Unicode(255))

    def __repr__(self):
        return unicode(self.material_name)

    def hashtag_name(self):
        return u"#" + sanitize_to_hashtext(unicode(self.material_name))

class c_material_type(BASE, abst_key, connected_to_DEVS):
    #Номенклатурная группа (папка-родитель) - её потребление и моделируем
    __tablename__ = 'material_types'
    rec_id = Column(Integer, primary_key=True)
    account_system_code = Column(Unicode(255))
    material_type_name = Column(Unicode(255))
    #Равнозначны ли материалы в группе.
    are_materials_equal = Column(Boolean)  #Надо это как-то вводить где-то.
    measure_unit = Column(Unicode(255))

    def __repr__(self):
        return unicode(self.material_type_name)

    def hashtag_name(self):
        return u"#" + sanitize_to_hashtext(unicode(self.material_type_name))

class c_material_type_accounting(BASE, abst_key, connected_to_DEVS):
    #Номенклатурная группа бухгалтерская - лишь для учета прибыли (так как только в разрезе по группе есть себестоимость).
    __tablename__ = 'material_types_accounting'
    rec_id = Column(Integer, primary_key=True)
    account_system_code = Column(Unicode(255))
    material_type_accounting_name = Column(Unicode(255))
    measure_unit = Column(Unicode(255))

    def __repr__(self):
        return unicode(self.material_type_accounting_name)

class c_payment_type(BASE, abst_key, connected_to_DEVS):
    # Статья движения ДС
    __tablename__ = 'payment_types'
    rec_id = Column(Integer, primary_key=True)
    account_system_code = Column(Unicode(255))
    name = Column(Unicode(255))

    def __repr__(self):
        return unicode(self.name)

class c_payment_terms(BASE, abst_key, connected_to_DEVS):
    __tablename__ = 'payment_terms'
    rec_id = Column(Integer, primary_key=True)
    account_system_code = Column(Unicode(255))
    payterm_name = Column(Unicode(255))
    payterm_stages = Column(PickleType)  #Mutabca надо трачить мутабельность - если только будем где-то по частям менять.
    fixation_at_shipment = Column(Boolean) # False - при платеже
    ccy_quote_rec_id = Column(Integer, ForeignKey('currencies.rec_id'))
    ccy_quote = relationship("c_currency", foreign_keys=[ccy_quote_rec_id])
    ccy_pay_rec_id = Column(Integer, ForeignKey('currencies.rec_id'))
    ccy_pay = relationship("c_currency", foreign_keys=[ccy_pay_rec_id])

    def __repr__(self):
        return unicode(self.payterm_name)

class c_payment_stages():
    def __init__(self):
        self.pay_delay = []  #На сколько относительно отгрузки оплата отстоит
        self.pay_proc = []  #Какой % платежа

    def __repr__(self):
        return " prepayments:" + str(self.get_prepayments()) + " postpayments:" + str(self.get_postpayments())

    def __eq__(self, other):
        if other is None:
            return False
        if len(self.pay_delay)<>len(other.pay_delay) or len(self.pay_proc)<>len(other.pay_proc):
            return False
        for i in range(0,len(self.pay_delay)):
            if self.pay_delay[i] <> other.pay_delay[i]:
                return False
            elif self.pay_proc[i] <> other.pay_proc[i]:
                return False
        return True

    def __ne__(self, other):
        return not(self==other)

    def add_payment_term(self, payment_delay, payment_proc):
        self.pay_delay.append(payment_delay)
        self.pay_proc.append(payment_proc)

    def get_prepayments(self):
        #Возвращает tuple предоплат
        ans = []
        for t in range(0,len(self.pay_delay)):
            if self.pay_delay[t]<=0:
                tup_i = (self.pay_delay[t],self.pay_proc[t])
                ans.append(tup_i)
        return ans

    def get_postpayments(self):
        #Возвращает tuple постоплат
        ans = []
        for t in range(0,len(self.pay_delay)):
            if self.pay_delay[t]>0:
                tup_i = (self.pay_delay[t],self.pay_proc[t])
                ans.append(tup_i)
        return ans

class c_currency(BASE, abst_key):
    __tablename__ = 'currencies'
    rec_id = Column(Integer, primary_key=True)
    account_system_code = Column(Unicode(255))
    ccy_public_code =  Column(Unicode(255))#Для синхронизации с web
    ccy_general_name = Column(Unicode(255))
    ccy_name = Column(Unicode(255))

    def __repr__(self):
        return unicode(self.ccy_general_name)

class c_material_price(BASE, abst_key, connected_to_DEVS):
    __tablename__ = 'material_prices'
    discriminator = Column(Unicode(50))
    __mapper_args__ = {'polymorphic_identity':'base_material_price', 'polymorphic_on': discriminator}
    rec_id = Column(Integer, primary_key=True)
    price_value = Column(SqliteNumeric)
    material_rec_id = Column(Integer, ForeignKey('materials.rec_id'))
    material = relationship("c_material")
    material_type_rec_id = Column(Integer, ForeignKey('material_types.rec_id'))
    material_type = relationship("c_material_type")
    #Если true, то смотрим material_type, если false, то material
    is_for_group = Column(Boolean)
    payterm_rec_id = Column(Integer, ForeignKey('payment_terms.rec_id'))
    payterm = relationship("c_payment_terms")
    trading_firm_rec_id = Column(Integer, ForeignKey('trading_firms.rec_id'))
    trading_firm = relationship("c_trading_firm", backref=backref('sell_prices'))
    is_valid_between_dates = Column(Boolean)
    date_valid_from = Column(DateTime)
    date_valid_till = Column(DateTime)
    min_order_quantity = Column(SqliteNumeric)
    min_order_sum = Column(SqliteNumeric)
    is_foreign_ccy = Column(Boolean)
    nonformal_conditions = Column(UnicodeText)
    is_agent_scheme = Column(Boolean)

    def __repr__(self):
        if self.is_for_group:
            return unicode(str(self.material_type)+"@"+str(self.price_value))
        else:
            return unicode(str(self.material)+"@"+str(self.price_value))


class c_sell_price(c_material_price):
    __tablename__ = 'sell_prices'
    __mapper_args__ = {'polymorphic_identity': 'sell_price'}
    rec_id = Column(Integer, ForeignKey('material_prices.rec_id'), primary_key=True)
    client_model_rec_id = Column(Integer, ForeignKey('agents_clients.rec_id'))
    client_model = relationship("c_client_model", backref=backref('sell_prices'))

    is_factoring = Column(Boolean)
    is_delivery = Column(Boolean)
    delivery_place = Column(Unicode(255))
    is_per_order_only = Column(Boolean) # Только под заказ - не завозим сразу на склад
    order_fulfilment_timedelta = Column(Integer)

class c_buy_price(c_material_price):
    __tablename__ = 'buy_prices'
    __mapper_args__ = {'polymorphic_identity': 'buy_price'}
    rec_id = Column(Integer, ForeignKey('material_prices.rec_id'), primary_key=True)
    supplier_model_rec_id = Column(Integer, ForeignKey('agents_suppliers.rec_id'))
    supplier_model = relationship("c_supplier_model", backref=backref('buy_prices'))

    incoterms_place = Column(Unicode(255))
    lead_time = Column(SqliteNumeric)
    is_only_for_sp_client = Column(Boolean)
    for_client_rec_id = Column(Integer, ForeignKey('agents_clients.rec_id'))
    for_client = relationship("c_client_model")

"""</SIMULATION SYSTEM>"""

""" THESE ARE NOT PRESENT IN SIMULATION """

class c_fact_shipment(BASE):
    #Вспомогательный класс - для оценки статистики потребления
    __tablename__ = 'fact_shipments'
    rec_id = Column(Integer, primary_key=True)
    ship_qtty = Column(SqliteNumeric)
    ship_date = Column(DateTime)
    material_rec_id = Column(Integer, ForeignKey('materials.rec_id'))
    material = relationship("c_material")
    client_model_rec_id = Column(Integer, ForeignKey('agents_clients.rec_id'))
    client_model = relationship("c_client_model", backref=backref('fact_shipments'))

    def __repr__(self):
        return 'A [c_fact_shipment] of ' + self.material.material_name + " qtty: " + str(self.ship_qtty)

class c_fact_payment(BASE):
    __tablename__ = 'fact_payments'
    rec_id = Column(Integer, primary_key=True)
    pay_date = Column(DateTime)
    # Возможно, стоит здесь сделать помягче - невозможно же всех агентов выгрузить..
    agent_model_rec_id = Column(Integer, ForeignKey('agents.rec_id'))
    agent_model = relationship("c_agent", backref=backref('fact_payments'))
    # Статься движения ДС
    paytype_rec_id = Column(Integer, ForeignKey('payment_types.rec_id'))
    paytype = relationship("c_payment_type")
    sum_total = Column(SqliteNumeric)
    vat_in_sum = Column(SqliteNumeric)
    ccy_pay_rec_id = Column(Integer, ForeignKey('currencies.rec_id'))
    ccy_pay = relationship("c_currency", foreign_keys=[ccy_pay_rec_id])

    def __repr__(self):
        return 'A [c_fact_payment] of type ' + self.paytype.name


class c_dummy(object):
    # Пустой объект для фиксации аттрибутов
    def __init__(self, parent_obj):
        self._parent_obj = parent_obj

    def fix_attrs(self, list_of_attr_names):
        for attr_name in list_of_attr_names:
            setattr(self, attr_name, getattr(self._parent_obj,attr_name))

the_report_filler = c_HTML_reports.c_report_filler()