# -*- coding: utf-8 -*-

'''
Грузим старую базу (заметки и контакты) в новую.
'''

# Импортируем всё для новой (этой) базы
import db_main

# Старую базу прочитаем без схемы SQLAlchemy

import sqlite3
import utils
import sys
import datetime
from PyQt4 import QtGui, QtCore
conn = sqlite3.connect('__secret\\PyIn_160106.db')

# Грузим заметки CRM (и создаем по ходу хештеги)

cur = conn.cursor()
cur.execute('SELECT * FROM crm_record')

app = QtGui.QApplication(sys.argv)
HtmlParser = QtGui.QTextEdit()
HtmlParser.app = app

for r in cur:
    # Старая заметка (без ссылок на хештеги)
    text_date_added, headline, long_html_text = r[1], r[2], r[3]
    date_added = datetime.datetime.strptime(text_date_added, '%Y-%m-%d %H:%M:%S.%f')

    # # Чтобы разметить хештеги, надо сделать toPlainText методами Qt
    HtmlParser.setHtml(long_html_text)
    # Вытаскиваем текст тэгов
    tag_list = utils.parse_hashtags(unicode(HtmlParser.toPlainText()))
    print(tag_list)

    HtmlParser.clear()

    record_tags = db_main.get_hashtags_from_names(tag_list)
    found_names = [rec_i.text for rec_i in record_tags]
    not_found = [] # Это те, которых в базе нет
    for ht_i in tag_list:
        if not(ht_i in found_names):
            not_found += [ht_i]
    for ht_i in not_found:
        #Создаем новый тэг
        new_h = db_main.c_hastag(text=ht_i)
        db_main.the_session_handler.add_object_to_session(new_h)
        record_tags += [new_h]

    # Новая заметка:
    new_record = db_main.c_crm_record()
    new_record.date_added = date_added
    new_record.headline = headline
    new_record.long_html_text = long_html_text
    # Немного магии с тегами
    new_record.match_with_tags(record_tags)
    new_record.fix_hashtag_text()

    db_main.the_session_handler.add_object_to_session(new_record)

db_main.the_session_handler.commit_and_close_session()

