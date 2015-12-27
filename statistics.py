# -*- coding: utf-8 -*-

import pandas as pd
from gl_shared import *


class c_event_predictive_ts():
    #TODO: придумать что-нибудь
    # Используются для простых предсказаний событий.
    # Когда, сколько, с.к.о. когда, с.к.о. сколько.
    def __init__(self):
        self.data_ts = c_fast_ts()
        self.prediction_value_expectation = 0
        self.prediction_value_std = 0
        self.prediction_timedelta_expectaion = 0
        self.prediction_timedelta_std = 0
        self.last_event_date = None

    def __repr__(self):
        return unicode(self.data_ts.return_series())

    def add_point(self, timestamp, value):
        self.data_ts.add_obs(timestamp, float(value))

    def run_estimations(self):
        ts = self.data_ts.return_series()
        if len(ts) >= 3:  #Минимум три наблюдений в разные даты
            self.prediction_value_expectation = round(numpy.average(ts.values))
            self.prediction_value_std = round(numpy.std(ts.values))
            ts_d = []
            ts_td = numpy.diff(ts.keys().tolist())
            for td in ts_td:
                ts_d += [td.days]
            self.prediction_timedelta_expectaion = round(numpy.mean(ts_d))
            self.prediction_timedelta_std = round(numpy.std(ts_d))
            self.last_event_date = max(self.data_ts.timestamps)

class c_fast_ts():
    # Используется во время симуляции для сбора данных
    def __init__(self):
        self.timestamps = []
        self.values = []

    def __repr__(self):
        s = "c_fast_ts:" + "\n"
        for k in range(0,len(self.timestamps)):
            s += str(self.timestamps[k]) + " : " + str(self.values[k]) + "\n"
        return s

    def __len__(self):
        return len(self.timestamps)

    def add_obs(self, timestamp, value):
        self.timestamps.append(timestamp)
        self.values.append(value)

    def return_series(self, start_date = 0):
        #start_date может быть DateTime
        tempdict = dict()
        for k in range(0,len(self.values)):
            # В режиме симуляции мы храним отсчет в днях и при финальной обработке переводим в даты
            # Однако в иных случаях используем класс просто с временными метками (обычно дата)
            if start_date == 0:
                d = self.timestamps[k]
            else:  #д.б. datetime
                d = start_date + datetime.timedelta(days=self.timestamps[k])
            if tempdict.has_key(d):
                tempdict[d] += self.values[k]
            else:
                tempdict[d] = self.values[k]
        Panda_Series = pd.Series(tempdict)
        return Panda_Series