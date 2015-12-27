# -*- coding: utf-8 -*-
"""
Created on Sat Feb 22 19:41:32 2014

В этом классе запускается сборка системы для симуляции и запускаются симуляции.

@author: Vyakhorev
"""
import simpy
import datetime
import random
import db_main
from c_simulation_results_container import c_simulation_results_container, finalize_epoch_data

class c_planner():

    def initiate_system(self,simpy_env, seed):
        # TODO: пиклить в файл после первого считывания из базы.
        start_date = db_main.the_settings_manager.get_param_value("initial_data_date")
        the_devs = db_main.c_discrete_event_system(simpy_env, start_date)
        the_devs.set_seed(seed)
        db_main.init_system_from_database(the_devs) # вот тут вся база данных считывается прямо в оперативную память
        the_devs.lastbreath_before_simulation()  # дополнительная инициализация
        self.system = the_devs

    def run_and_return_log(self, seed = 0):
        import sys
        log_str = []
        if seed == 0:
            seed = random.randint(0, sys.maxint)
        sim_results = c_simulation_results_container()
        log_list = []
        self.run_epoch(360, seed, sim_results, print_console = False, print_to_list = log_list)
        return dict(log_list = log_list, sim_results = sim_results)

    def run_observed_simulation(self, epoch_num = 50, sim_until = 360):
        #Генерируем сиды - после каждой симуляции записываем сид и основные результаты
        #TimeSeries генерируем по сиду.
        import sys
        db_main.clear_epoch_data()
        sim_times = []  #Статистика, сколько времени заняла каждая симуляция
        write_db_times = [] #Статистика, сколько времнеи заняла каждая запись в базу
        for k in range(0,epoch_num):
            sim_results = c_simulation_results_container()
            print("%s Simulating epoch number %d of %d ..."% (str(datetime.datetime.now()), k+1, epoch_num))
            t0 = datetime.datetime.now()
            seed_i = random.randint(0, sys.maxint)  #Обрати внимание, когда на разных 32/64 запускаешь!
            #self.run_epoch(sim_until, seed_i, sim_results)
            self.run_epoch(sim_until, seed_i, sim_results, print_console = False)  #investigations
            t1 = datetime.datetime.now()
            print("%s writing results of %d epoch to database ..."% (str(t1), k+1))
            db_main.add_epoch_data(k,seed_i,sim_results)
            t2 = datetime.datetime.now()
            delt1 = t1-t0
            sim_times.append(delt1.microseconds)
            delt2 = t2-t1
            write_db_times.append(delt2.microseconds)
        print("Simulation is finished!")
        av_sim = sum(sim_times)/len(sim_times)
        print("Average epoch simulation time is %d microseconds, total simulation is %d microseonds"% (av_sim, sum(sim_times)))
        av_write = sum(write_db_times)/len(write_db_times)
        print("Average epoch results write to database time is %d microseconds, total writing is %d microseconds"% (av_write, sum(write_db_times)))
        finalize_epoch_data()
        print("Recalc budget..")
        self.publish_stats()  #Запись в базу статистики - в явном виде. Пока только бюджет продаж.
        print("Published!")

    def run_epoch(self, sim_until, seed = 0, sim_results = None, print_console = False, print_to_list = None):
        # Создаем рабочую среду для системы
        self.simpy_env = simpy.Environment()
        self.initiate_system(self.simpy_env, seed)  #new instanse of the whole system with all sublements - quite costy
        self.simpy_env.process(self.system.my_generator())
        if sim_results is not None:
            self.add_observers(sim_results)   #Добавляем обсерверов в енвайронмент - они не видны в системе, но им видна система
        if print_console:
            self.system.add_printer(db_main.console_log_printer())
        if print_to_list is not None:
            self.system.add_printer(db_main.list_log_printer(print_to_list))
        # Система собрана - запускаем!
        self.simpy_env.run(until = sim_until)

    def add_observers(self,sim_results):
        observers = []
        observers += [c_ccyrate_observer(u"КУРСЫ",self.system, sim_results, 5)]
        observers += [c_warehouse_observer(u"СКЛАД", self.system, sim_results, 5)]
        observers += [c_money_observer(u"БАНК", self.system, sim_results, 5)]
        observers += [c_client_demand_observer(u"СПРОС", self.system, sim_results, 5)]
        for obs_i in observers:
            obs_i.activate_in_env()

    def publish_stats(self):
        # Записываем в базу бюджет продаж - график ожидаемых значений.
        # Это не зависит от симуляции, мы выгружаем только ожидаемые значения.
        db_main.fix_sales_budget()

"""Observers"""

class c_abst_observer(object):
    # Helps to observe and record statistics from the system
    def __init__(self, obs_name, system, sim_results, period = 1):
        self.obs_name = obs_name
        self.system = system
        self.sim_results = sim_results
        self.period = period

    def full_obs_name(self):
        return "[each %d days] %s"% (self.period, self.obs_name)

    def my_generator(self):
        while True:
            self.cur_date = self.system.simpy_env.now
            self.observe_data()
            yield self.system.simpy_env.timeout(self.period)

    def observe_data(self):
        # Reimplement - you may record multiple ts
        ts_name = "abstract"
        ts_value = 0
        self.record_data(ts_name, ts_value)

    def record_data(self, ts_name, ts_value):
        # Do not record the same data twice - they are aggregated in pandas, though.. Never tested.
        self.sim_results.add_ts_point(self.full_obs_name(), ts_name, self.cur_date, ts_value)

    def activate_in_env(self):
        self.system.simpy_env.process(self.my_generator())

class c_ccyrate_observer(c_abst_observer):
    def observe_data(self):
        for ccy_i in self.system.macro_market.get_ccy_list():
            quote = self.system.macro_market.get_ccy_quote(ccy_i)
            if ccy_i.ccy_general_name <> "RUB":
                self.record_data(str("RUB -> ") + str(ccy_i), quote)

class c_warehouse_observer(c_abst_observer):
    def observe_data(self):
        total_cost = 0
        qtty_by_group = dict()
        for key_i, dict_with_data in self.system.trading_firm.warehouse.inventory.iteritems():
            material_group = str(key_i[0].material_type)  #Ключ составной: материал + склад + доступен ли
            qtty = dict_with_data["qtty"]
            if qtty_by_group.has_key(material_group):
                qtty_by_group[material_group] += qtty
            else:
                qtty_by_group[material_group] = qtty
        for m_gr_i, qtty_i in qtty_by_group.iteritems():
            self.record_data(u"КОЛИЧЕСТВО  " + unicode(m_gr_i), qtty_i)

class c_money_observer(c_abst_observer):
    def observe_data(self):
        for key_i, dict_with_data in self.system.trading_firm.bank_account.money.iteritems():
            ccy_i = str(key_i)
            amount = dict_with_data["amount"]
            self.record_data(ccy_i, amount)
        totals = self.system.trading_firm.bank_account.get_rouble_m2m_level()
        self.record_data("m2m RUB", totals)

class c_client_demand_observer(c_abst_observer):
    def observe_data(self):
        for cl_i in self.system.clients_list:
            total_sum = 0
            for k_i, v_i in cl_i.order_stats_by_material_group_qtty.iteritems():
                s = (u"КОЛИЧЕСТВО %s -> %s"%(str(k_i),str(cl_i)))
                self.record_data(s, v_i)
            for k_i, v_i in cl_i.order_stats_by_material_group_sum.iteritems():
                s = (u"СУММА %s -> %s"%(str(k_i),str(cl_i)))
                self.record_data(s, v_i)
                total_sum += v_i
            self.record_data(u"СУММА всего %s"%(str(cl_i)),total_sum)
