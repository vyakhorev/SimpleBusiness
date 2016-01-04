# -*- coding: utf-8 -*-

"""
Created on Fri May 30 15:24:29 2014

В этом модуле вынесен код для запуска SQL Alchemy. Несколько модулей обращается к к этим
переменным. the_session_handler - одиночка, который обеспечивает активность и единствненость сессии.

@author: Vyakhorev
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import make_transient
from sqlalchemy.orm import subqueryload, immediateload, joinedload
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from simple_locale import ultimate_encoding
from sqlalchemy.orm import with_polymorphic
import traceback
import gl_shared


#################################
#   Внутренняя кухня
################################# 

#################################
#Ошибки - для синхронизации

class SynchUnknownError(Exception):
    #Вызывается при ошибке при чтении xml-ноды
    def __init__(self, xml_node,func_name):
        print("*****************************")
        print("Clues to solve unknown error:")
        self.xml_node = xml_node
        self.func_name = func_name
        import traceback
        traceback.print_exc()

    def __str__(self):
        return "Unknown error with synchronising: \n \t @" + self.func_name + " \n \t node: \n \t " + self.xml_node

class SynchFindingListError(Exception):
    # TODO: kill
    #Вызывается, когда не нашли элемент справочника
    def __init__(self, acc_code, item_class_name):
        self.acc_code = acc_code
        self.item_class_name = item_class_name
        import traceback
        traceback.print_exc()

    def __str__(self):
        return "An item not found in the database: \n \t item_type:" + self.item_class_name + "\n \t code: " + self.acc_code

class SynchWrongClass(Exception):
    # TODO: kill (?)
    def __init__(self, object_type_name):
        self.object_type_name = object_type_name
        import traceback
        traceback.print_exc()

    def __str__(self):
        return "Object of a type " + self.object_type_name + " do not have account_system_code attribute!"

class SynchDoubledAccountSystemKey(Exception):
    # TODO: kill
    #Вызывается, если при синхронизации обнаружили задвоение ключей
    #в нашей базе (ключи - account_system_code)
    #можно здесь сделать попытку "вылечить"
    def __init__(self, object_type_name, account_system_code):
        self.object_type_name = object_type_name
        self.account_system_code = account_system_code
        import traceback
        traceback.print_exc()

    def __str__(self):
        return "Doubled account_system_code found in the database \n \t object:" + self.object_type_name + " \n \t code: " + self.account_system_code

class DoubledSigletonInDB(Exception):
    def __init__(self, object_type_name):
        self.object_type_name = object_type_name
        import traceback
        traceback.print_exc()

    def __str__(self):
        return "There can be only one \n \t object:" + self.object_type_name

##################################################################################
#           Самый главный класс в модуле
##################################################################################

class c_session_handler():
    #Отвечает за уникальность сессии и заодно по хозяйству.
    #Здесь надо обработчки ошибок обязательно - с базой не шутки.
    def __init__(self, session_generator):
        self.session_generator = session_generator
        self.active_session = None

    def private_activate_session(self):
        if self.active_session is None:
            self.active_session = self.session_generator()

    def merge_object_to_session(self, *args):
        self.private_activate_session()
        for a in args:
            self.active_session.merge(a)

    def add_object_to_session(self, obj):
        self.private_activate_session()
        #Можно вставить проверку, есть ли объект уже в сессии,
        #поругаться и добавить.
        self.active_session.add(obj)

    def get_active_session(self):
        #когда иначе никак
        self.private_activate_session()
        return self.active_session

    def get_all_objects_list(self, obj_class):
        self.private_activate_session()
        obj_list = []
        for obj_i in self.active_session.query(obj_class).all():
            obj_list.append(obj_i)
        return obj_list

    def get_all_objects_list_iter(self, obj_class):
        self.private_activate_session()
        for obj_i in self.active_session.query(obj_class).all():
            yield obj_i

    def get_singleton_object(self, obj_class):
        self.private_activate_session()
        c = self.active_session.query(obj_class).count()
        if c == 0:
            #Впервые обращаемся к объекту
            print(u"Впервые обращаемся к объекту")
            the_obj = obj_class()
            self.add_object_to_session(the_obj)
            return the_obj
        elif c == 1:
            the_obj = self.active_session.query(obj_class).one()
            return the_obj
        else:
            raise DoubledSigletonInDB(obj_class.__name__)

    def delete_all_objects(self, obj_class):
        self.private_activate_session()
        self.active_session.query(obj_class).delete()
   
    def delete_concrete_object(self, an_object):
        self.private_activate_session()
        self.active_session.delete(an_object)
        self.active_session.commit()
   
    def commit_session(self):
        self.private_activate_session()
        try:
            self.active_session.commit()
        except:
            print "Error with commiting the session"
            print traceback.format_exc()
            self.close_session()

    def close_session(self):
        self.private_activate_session()
        self.active_session.close()
        self.active_session = None

    def commit_and_close_session(self):
        self.commit_session()
        self.close_session()

    def flush_active_session(self):
        #метод дает ключи всем добавленным объектам
        self.private_activate_session()
        self.active_session.flush()
   
    def get_account_system_object(self, object_class, system_code, do_raise_err = 1):
        #Достаем из базы объект 1С
        if hasattr(object_class, "account_system_code"):
            try:
                return self.get_active_session().query(object_class).filter_by(account_system_code = system_code).one()
            except NoResultFound:
                print (u"There is no %s in %s"%(system_code, object_class.__name__))
                if do_raise_err: raise SynchFindingListError(system_code, object_class.__name__)
                return None
            except MultipleResultsFound:
                print (u"There are multiple %s in %s"%(system_code, object_class.__name__))
                if do_raise_err: SynchFindingListError(system_code, object_class.__name__)
                return None
            except:
                raise SynchWrongClass(object_class.__name__)
        else:
            raise SynchWrongClass(object_class.__name__)

    def check_existance_of_account_object(self, object_class, system_code):
        if hasattr(object_class, "account_system_code"):
            c = self.get_active_session().query(object_class).filter_by(account_system_code = system_code).count()
            if c>1:
                raise SynchDoubledAccountSystemKey(object_class.__name__, system_code)
            elif c == 0:
                return False
            elif c == 1:
                return True
        else:
            raise SynchWrongClass(object_class.__name__)

    def recieve_account_system_object(self, object_class, system_code):
        #То же, что и выше, но создает новый объект, если нету, и ругается, если задублирован
        if hasattr(object_class, "account_system_code"):
            do_exist = self.check_existance_of_account_object(object_class, system_code)
            if do_exist == False:
                #добавляем новую запись
                new_obj = object_class(account_system_code = system_code)
                #Пока у нас все конструируются без аргументов - если не хватит, то можно и аргументы передать как-нибудь
                #Только тогда это будет уже не "recieve", а refresh..
                self.add_object_to_session(new_obj)
                return new_obj
            else:
                #Достаем запись
                old_obj = self.get_active_session().query(object_class).filter_by(account_system_code = system_code).one()
                return old_obj
        else:
            raise SynchWrongClass(object_class.__name__)

    def cash_instances_to_dict(self, list_of_classes, do_make_transient = False):
        #Закрываем сессию. Открываем новую и считываем в нее все классы. Отвязываем их от сессии.
        #Возвращаем список инстансов в виде словаря. Надеюсь, это поможет работать с ними сколь угодно много..
        #Была идея оставить возможность не закрывать сесиию - отказался. В худшем случае, можно отдельную сессию создавать.
        #Но две одновременные сессии - тоже опасно.
        self.close_session()
        self.private_activate_session()
        dict_with_instances = dict()
        for cls_i in list_of_classes:  #Интересно, нужно ли как-то особо считывать взаимосвязи
            repr_cls_i = with_polymorphic(cls_i, '*')
            inst_list = []
            for inst_i in self.active_session.query(repr_cls_i).options(immediateload('*')).all():
                #if not(inst_i in inst_list):
                inst_list.append(inst_i)
            dict_with_instances[cls_i.__name__] = inst_list
        self.active_session.expunge_all() #именно поэтому закрываем сессию до запуска
        for inst_list in dict_with_instances.itervalues():
            for inst_i in inst_list:
                if hasattr(inst_i, "disconnected_from_session"):
                    raise BaseException("[c_session_handler][cash_instances_to_dict] you cannot use 'disconnected_from_session' attribute in a class here")
                inst_i.disconnected_from_session = True
                if do_make_transient:  #Без этого может пытаться обратиться к базе данных
                    make_transient(inst_i)
        self.close_session()
        return dict_with_instances

#-----------------
#Общие штуки для общения и подключения к базе данных

from cnf import db_type, db_conn_str, db_do_echo, db_is_prod

if db_type == "SQLite":
    engine = create_engine(db_conn_str, echo=db_do_echo, encoding=ultimate_encoding)
elif db_type == "MySQL":
    engine = create_engine(db_conn_str, echo=db_do_echo, encoding=ultimate_encoding)
else:
    raise BaseException("Unknown database type in main.ini")

if db_is_prod:
    print("THIS IS A PRODUCTION DATABASE !!!")
else:
    print("running a testing database")

cnf = None

the_session = sessionmaker(bind=engine)
#Вот этот для нас - чтобы сессия не терялася:
the_session_handler = c_session_handler(the_session)