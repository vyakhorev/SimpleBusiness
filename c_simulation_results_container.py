# -*- coding: utf-8 -*-

"""
Created on Sat Apr 19 17:01:54 2014

@author: Vyakhorev
"""
from db_handlers import the_session_handler
from db_simulation import cb_simul_dataframe, cb_epoh_data, the_report_filler
from db_main import the_settings_manager

from random import *
from itertools import * 
from statistics import *
from gl_shared import *

class c_simulation_results_container():
    #Одна на эпоху - быстрый лог данных с последующим преобразованием в dataframe
    def __init__(self):
        self.ts_dict = dict()
    
    def __repr__(self):
        s = "c_simulation_results_container:" + "\n"
        for k_obs_i in self.ts_dict.iterkeys():
            s += "--data from " + k_obs_i + "\n"
            ts_i = self.ts_dict[k_obs_i]
            for k_ts_i in ts_i.iterkeys():
                s += "----data of " + k_ts_i + "\n"
                s += ts_i[k_ts_i].__repr__()
        return s
    
    def add_ts_point(self, observer_name, ts_name, timestamp, value):
        # Точка входа для Observer - единственный способ добавить данные об эпохе
        #Это может быть долгим
        observer_name = unicode(observer_name)
        ts_name = unicode(ts_name)
        if not(self.ts_dict.has_key(observer_name)):
            self.ts_dict[observer_name] = dict()
        if not(self.ts_dict[observer_name].has_key(ts_name)):
            self.ts_dict[observer_name][ts_name] = c_fast_ts()
        self.ts_dict[observer_name][ts_name].add_obs(timestamp, value)
        
    def get_sim_results(self,observer_name,ts_name):
        try: 
            return self.ts_dict[observer_name][ts_name]
        except KeyError:
            return None
    
    def get_available_names(self):
        my_keys = []
        for k1 in self.ts_dict.keys():
            for k2 in self.ts_dict[k1]:
                my_keys.append([k1,k2])
        return my_keys
    
    def get_dataframe_for_epochvar(self,observer_name,variable_name):
        #Это для формы с результатом по эпохе
        datas_4_pandas = dict()
        datas_4_pandas[variable_name] = self.get_sim_results(observer_name,variable_name).return_series()
        df = pd.DataFrame(datas_4_pandas)
        return df


def finalize_epoch_data():
    #Занимается финализацией cb_epoh_data -> cb_simul_dataframe,
    #Здесь реализована логика, что пишется в data_frame
    #Также отвечает за некоторые штучки с интерфейсом.
    #Строим много dataframe и вкладываем их в cb_simul_dataframe.
    #Каждая симуляция - это эпоха, сид и c_simulation_results_container
    print("[c_simul_dataframe_manager][finalize_epoch_data] processing...")
    the_session_handler.delete_all_objects(cb_simul_dataframe)
    the_session_handler.commit_session()
    synch_date = the_settings_manager.get_param_value("initial_data_date")
    #Собираем имена
    all_names = []
    for epoh_i in the_session_handler.get_all_objects_list_iter(cb_epoh_data):
        names_i = epoh_i.simulation_results.get_available_names()  #Перекроить метод get_available_names - будут адреса
        all_names += names_i
    all_names = __uniq(all_names)
    #Для каждой пары имен строим dataframe - опять-таки по эпохам. Если не вмоготу, тут можно эти два цикла слить и оптимизировать.
    for observer_name, ts_name in all_names:
        #Dataframe по эпохам (куча линий)
        datas_4_pandas_i = dict()
        for epoh_i in the_session_handler.get_all_objects_list_iter(cb_epoh_data):
            ts_i = epoh_i.simulation_results.get_sim_results(observer_name,ts_name)
            if not(ts_i is None):  #Надо потом подумать над этим
                datas_4_pandas_i[str(epoh_i.epoh_num)] = ts_i.return_series(synch_date)
        df_byepoch_i = pd.DataFrame(datas_4_pandas_i)
#        b_df_byepoch_i = cb_simul_dataframe(data_frame = df_byepoch_i, var_name = ts_name,observer_name = observer_name, data_frame_type = "by_epoch")
#        the_session_handler.add_object_to_session(b_df_byepoch_i)
        #Dataframe со средними и квантилями
        means = pd.DataFrame(df_byepoch_i.mean(axis = 1))
        l_qnt = pd.DataFrame(df_byepoch_i.quantile(0.1,axis = 1))
        u_qnt = pd.DataFrame(df_byepoch_i.quantile(0.9,axis = 1))
        my_data = pd.concat([l_qnt, means, u_qnt], axis=1, join='outer')
        my_data.columns = ['min', 'expectation','max']
        b_df_means_i = cb_simul_dataframe(data_frame = my_data, var_name = ts_name,observer_name = observer_name, data_frame_type = "mean")
#        b_df_l_qnt_i = cb_simul_dataframe(data_frame = df_byepoch_i.quantile(0.1,axis = 1), var_name = ts_name,observer_name = observer_name, data_frame_type = "l_qnt")
#        b_df_u_qnt_i = cb_simul_dataframe(data_frame = df_byepoch_i.quantile(0.9,axis = 1), var_name = ts_name,observer_name = observer_name, data_frame_type = "u_qnt")
        the_session_handler.add_object_to_session(b_df_means_i)
#        the_session_handler.add_object_to_session(b_df_l_qnt_i)
#        the_session_handler.add_object_to_session(b_df_u_qnt_i)
        the_session_handler.commit_session()
    the_session_handler.close_session()
    print("[c_simul_dataframe_manager][finalize_epoch_data] finished!")
             
def iter_dataframe_reports():
    #Возвращает итератор по репортам - по нему интерфейс строим.
    #Для начала сделаем линейный тупой итератор. Без адресов
    for df_i in the_session_handler.get_all_objects_list_iter(cb_simul_dataframe):
        rep_i = the_report_filler.get_report_for_object(df_i)
        tree_address = rep_i.get_name()
        yield([tree_address, rep_i])
        
def __uniq(input): #Ы?
    output = []
    for x in input:
        if x not in output:
            output.append(x)
    return output        
