# -*- coding: utf-8 -*-

__author__ = 'Vyakhorev'

"""
    I do not like to employ "locale" for simple tasks like string formatting. That's why I gave birth to the module
"""
import sys

ultimate_encoding = 'utf-8'

def number2string(input_float):
    #Instead of locale.format('%.2f', number, True)
    #TODO: implement
    return str(input_float)

def string2number(input_string):
    #Вместо locale.atof(float_str)
    x = input_string
    input_string.replace(',', '.')
    ans = float(x) if '.' in x else int(x)
    return ans

def date2string(inputDateTime):
    #Instead of datetime.strftime('%d %m %y'))
    return '%d %d %d'%(inputDateTime.year, inputDateTime.month, inputDateTime.day)

