# -*- coding: utf-8 -*-
from gl_shared import *
from urllib import quote
from urlparse import urlparse
import webbrowser
import smtplib
from email.mime.text import MIMEText
quote_u = lambda s: quote(str(s))

""" В этом модуле - разные штуки с re и письмами. Ну и распределение вероятностей c_random_dict."""


class c_random_dict(object):
    #helps to estimate and simulate random selection of materials within one material flow
    #В базе хранится лишь словарь с результатами. Эта переменная может его записать и прочитать.
    def __init__(self):
        self.randomdict = {}
        self.cdf = {}
        self.finalized = 0

    def reset_me(self):
        self.randomdict = {}
        self.cdf = {}
        self.finalized = 0

    def write_dict_with_results(self):
        #Словарь с ключем элемента и значением вероятности (не cdf)
        if not(self.finalized):
            return None
        return self.randomdict

    def read_results_from_dict(self, prob_dict):
        #Словарь с ключем элемента и значением вероятности
        self.randomdict = prob_dict
        self.finalized = 0
        self.finalize()

    def add_elem(self, elem, prob = 1):
        #you may provide a number (priority) instead of real probability.
        if self.randomdict.has_key(elem):
            self.randomdict[elem] += float(prob)
        else:
            self.randomdict[elem] = float(prob)
        self.finalized = 0

    def delete_elem(self, elem):
        if self.randomdict.has_key(elem):
            self.randomdict.pop(elem)
        self.finalized = 0

    def finalize(self):
        #Calculates cdf
        self.__normalize()
        self.cdf = {}
        sum_prob = 0
        for el, p in self.randomdict.iteritems():
            sum_prob += p
            self.cdf[el] = sum_prob #ToDo: check validity of calculations
        self.finalized = 1

    def __normalize(self):
        #normalizes pdf (prob. den function)
        s = 0
        for p in self.randomdict.itervalues():
            s+=p
        if s<>0:
            for el in self.randomdict.iterkeys():
                p = self.randomdict[el]
                self.randomdict[el] = p/s
        else:
            #If something strange happens
            n = len(self.randomdict)
            for el in self.randomdict.iterkeys():
                self.randomdict[el] = 1/n

    def choose_random(self, random_generator):
        if not(self.finalized):
            self.finalize()
        a = random_generator.random()
        n = len(self.cdf)
        k = 0
        doloop = 1
        all_items = self.cdf.items()
        while k<n-1 and doloop:
            cdf_k  = all_items[k][1]  #должно возрастать
            if a>cdf_k:
                doloop=0
            else:
                k+=1
        ans = all_items[k][0]
        return ans

class c_task(object):
    # Задача администрирования. Создать в модуле, потом импортить задачу в admin_scripts
    # А там дать менеджеру ей пользоваться.
    def __init__(self, name, schedule = None):
        # Что-нибудь придумаем с schedule ? Хотя бы повторения реализовать.
        self.name = name

    def run_task(self):
        # Yield c_msg instances here!
        raise NotImplementedError()


class c_msg(object):
    # TODO: для интерактива добавить варианты и input.
    # Цвет тоже тут добавлять.
    # A message from c_task to c_admin_tasks_manager in run_tasks
    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return self.text

def parse_hashtags(some_text):
    # TODO: lowercase! Exclude repeats!
    finder = re.compile(ur'(?i)(?<=\#)\w+', re.UNICODE)
    ans = []
    for s_i in finder.findall(some_text):
        ans += [unicode(s_i.lower())]
    return ans

def trim_whitespaces(some_text):
    ans = re.sub(r'\s+', '', some_text)
    return ans

def parse_all_words_and_clean_hashtags(some_text):
    # Из поля для ввода хештегов пытаемся понять, что хотел пользователь.
    # Разделяем слова по пропускам/запятым/точкам.. и убираем "#" если есть.
    clean_words = []
    replacer = re.compile(ur'\#', re.UNICODE)
    finder = re.compile(r'[\s*|,*|;*|.*]', re.UNICODE)
    for s_i in finder.split(some_text):
        s = sanitize_to_hashtext(replacer.sub("",s_i))
        if len(s)>0: clean_words += [s]
    return clean_words

def sanitize_to_hashtext(some_text):
    # TODO: remove special symbols
    trimmed = trim_whitespaces(some_text)
    cleaned = re.sub(ur'[?|$|.|!|,|\(|\)|-]', '', trimmed)
    return cleaned.lower()

def separate_by_semicolon(some_text):
    pattern = re.compile("^\s+|\s*;\s*|\s+$")
    ans = [x for x in pattern.split(some_text) if x]
    return ans

def separate_by_comma(some_text):
    pattern = re.compile("^\s+|\s*,\s*|\s+$")
    ans = [x for x in pattern.split(some_text) if x]
    return ans

def replace_unicode_text(long_text, string_to_find, string_to_place):
    patt = re.compile(re.escape(string_to_find), re.IGNORECASE)
    new_text = patt.sub(string_to_place, long_text)
    return new_text

def create_html_from_link(a_valid_link, link_repr = None):
    if link_repr is None:
        link_repr = a_valid_link
    return u"<a href=%s>%s</a>" % (quote_u(a_valid_link), link_repr)

def generate_mailto_link(to_list = None, cc_list = None, a_subj = "", a_body = ""):
    # TODO вот тут надо проверять формат входных адресов, чтобы html произвольный не исполнить
    to_str = ""
    if to_list is not None:
        for k, em_add in enumerate(to_list):
            to_str += em_add
            if k < len(to_list): to_str += ";"
    cc_str = ""
    if cc_list is not None:
        for k, em_add in enumerate(cc_list):
            cc_str += em_add
            if k < len(cc_list): cc_str += ","
    link_str = u"mailto:%s?cc=%s&subject=%s&body=%s" %(to_str, cc_str, quote_u(a_subj), quote_u(a_body))
    return link_str

def create_and_open_email_link(to_list = None, cc_list = None, a_subj = "", a_body = ""):
    # Если нет контекста
    a_link = generate_mailto_link(to_list, cc_list, a_subj, a_body)
    webbrowser.open(a_link)

def do_send_bot_email(to_list, a_sub, html_body):
    # Пока только на @cableprod.ru
    to_str = ""
    cleaned_to_list = []
    # Check for commas:
    for em_add in to_list:
        for add_i in separate_by_comma(em_add):
            for add_ii in separate_by_semicolon(add_i):
                cleaned_to_list += [add_ii]
    for k, em_add in enumerate(cleaned_to_list):
        if get_email_domain(em_add) <> "@cableprod.ru":
            raise BaseException("Do not send e-mails outside @cableprod.ru!")
        to_str += em_add
        if k+1 < len(cleaned_to_list): to_str += ";"
    msg = MIMEText(html_body, 'html','utf-8')
    msg['Subject'] = a_sub
    msg['To'] = to_str
    print("sending e-mail to: " + to_str)

    cnf = ConfigParser.ConfigParser()
    cnf.read('main.ini')
    smtp_server = cnf.get("MailServerConfig","smtp_server")
    login_user = cnf.get("MailServerConfig","login_user")
    login_pass = cnf.get("MailServerConfig","login_pass")
    cnf = None

    #TODO: переделать  msg['To']  -  там список должен быть для server.sendmail !

    m = re.search(r'(?:http.*://)?(?P<host>[^:/ ]+).?(?P<port>[0-9]*).*', smtp_server)
    smtp_server_host = m.group('host')
    smtp_server_port = int(m.group('port'))

    from_address = login_user

    server = smtplib.SMTP_SSL(smtp_server_host, smtp_server_port)
    print "server created"
    server.login(login_user, login_pass)
    print "server logged in"
    server.sendmail(from_address, msg['To'], msg.as_string())
    print "message sent"
    server.quit()
    print("server logged out")

def get_email_domain(em_add):
    return re.search('@.+', em_add).group()

def safe_unicode(obj, *args):
    """ return the unicode representation of obj """
    try:
        return unicode(obj, *args)
    except UnicodeDecodeError:
        # obj is byte string
        ascii_text = str(obj).encode('string_escape')
        return unicode(ascii_text)

def safe_str(obj):
    """ return the byte string representation of obj """
    try:
        return str(obj)
    except UnicodeEncodeError:
        # obj is unicode
        return unicode(obj).encode('unicode_escape')

def error_decorator(fn):
    def wrapped(*args, **kwargs):
        try:
            f = fn(*args, **kwargs)
            return f
        except:
            #Необработанная ошибка
            func_name = "[" + fn.__name__ + "]"
            raise BaseException("@" + func_name + ' - problem is here')
    return wrapped


