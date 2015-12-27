# -*- coding: utf-8 -*-

"""
Created on Sat Feb 15 19:46:57 2014

@author: vyakhorev
"""

import datetime
import time
import simple_locale

def convert(a_string):
    #Это использую для общения с 1С
    a_string = ''.join(a_string.split())
    a_string = float(a_string.replace(',','.'))
    return a_string

def convert_formated_str_2_float(float_str):
    #Это использую для общения с GUI
    if float_str.__class__.__name__ == "QVariant":
        float_str = str(float_str.toString())
    return simple_locale.string2number(float_str)

def convert_str_2_date(date_str):
    try:
        date_mask = "%d.%m.%Y %H:%M:%S"
        ans = datetime.datetime(*time.strptime(date_str, date_mask)[0:5])
        return ans
    except:
        return None