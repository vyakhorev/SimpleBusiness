# -*- coding: utf-8 -*-

from db_exec import BASE
from db_shared import *

class abst_key(object):
    def __repr__(self):
        return self.string_key()

    def __my_key(self):
        return (self.__tablename__, self.rec_id)

    def string_key(self):
        s_r = ""
        for s in self.__my_key():
            s_r += str(s)
        return s_r

    def __eq__(x, y):
        return x.__my_key() == y.__my_key()

    def __hash__(self):
        return hash(self.__my_key())

class SqliteNumeric(TypeDecorator):
    # We do not need for MySQL...
    impl = BigInteger
    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(self.impl)

    def process_bind_param(self, value, dialect):
        if value is not None:
            return value * 100000
        else:
            return None

    def process_result_value(self, value, dialect):
        if value is not None:
            return float(value)/100000
        else:
            return None

# class cb_base_settings(BASE):
#     __tablename__ = "base_settings"
#     param_name = Column(String(255), primary_key=True)
#     param_data = Column(PickleType)   #Mutabca надо трачить мутабельность