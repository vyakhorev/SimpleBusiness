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
conn = sqlite3.connect('__secret\\PyIn_last_before_modern.db')

do_load_crm_records = False
do_load_contacts = False

# Грузим заметки CRM (и создаем по ходу хештеги)
if do_load_crm_records:
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
        #print(tag_list)

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

# Идём дальше и перегружаем контакты.
if do_load_contacts:
    import pickle
    import logging
    #import db_crm

    logger = logging.getLogger('migrate-app')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('migrate.log')
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)

    file_to_read = open("__secret\\cont_dump.p", "rb")

    dict_with_companies = pickle.load(file_to_read)
    not_found_dict = {}

    agents = db_main.get_agent_list_by_name('NullClient')
    if len(agents)==0:
        NullClient = db_main.c_client_model(name='NullClient')
    else:
        NullClient = agents[0]

    agents = db_main.get_agent_list_by_name('NullSupplier')
    if len(agents)==0:
        NullSupplier = db_main.c_client_model(name='NullSupplier')
    else:
        NullSupplier = agents[0]


    for company_name, company_meta in dict_with_companies.iteritems():
        is_null = False
        contact_list = company_meta['contacts_list']
        agents = db_main.get_agent_list_by_name(company_name)
        if len(agents) == 0: agents = db_main.get_agent_list_by_name(company_name.lower())
        if len(agents) == 0: agents = db_main.get_agent_list_by_name(utils.sanitize_to_hashtext(company_name))
        if len(agents) == 0: agents = db_main.get_agent_list_by_name(company_meta['full_name'])
        if len(agents) == 0: agents = db_main.get_agent_list_by_inn(utils.sanitize_to_hashtext(company_meta['inn']))
        if len(agents) == 0:
            if company_meta['discriminator'] == 'supplier':
                agents = []
                agents.append(NullSupplier)
                is_null = True
            elif company_meta['discriminator'] == 'client':
                agents = []
                agents.append(NullClient)
                is_null = True
            else:
                agents = []
                agents.append(NullClient)
                is_null = True

        if len(agents) > 0:
            the_agent = agents[0]
            for cont_dict_i in contact_list:
                new_contact = db_main.c_crm_contact()
                new_contact.company = the_agent
                new_contact.from_dict(cont_dict_i)
                if is_null:
                    new_contact.name = company_name + u" : " + new_contact.name
                db_main.the_session_handler.add_object_to_session(new_contact)
                #logger.info(u'contact added to session:' + unicode(new_contact))
        else:
            cc = len(contact_list)
            logger.info(u'company with ' + str(cc) + u' contacts not found: ' + unicode(company_name))
            for cont_dict_i in contact_list:
                bad_contact = db_main.c_crm_contact()
                bad_contact.from_dict(cont_dict_i)
                #logger.info(unicode(bad_contact))
                #bad_contact = None
            not_found_dict[company_name] = contact_list

    db_main.the_session_handler.commit_and_close_session()

    #file_to_save = open("__secret\\cont_dump.p", "wb")
    #pickle.dump(not_found_dict, file_to_save)

