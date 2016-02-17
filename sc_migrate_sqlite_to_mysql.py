# Helps to migrate from sqlite file to mysql with SQLAlchemy
# For small DB only (loads everything to RAM)

from PyQt4 import QtCore, QtGui  # for conn string prompt
import sys
from db_handlers import create_engine, sessionmaker, c_session_handler, with_polymorphic, immediateload, make_transient
import db_main
import sc

encoding_old = 'utf-8'
encoding_new = 'utf-8'


def read_and_expunge(list_of_classes, session_handler):
    session_handler.close_session()
    session_handler.private_activate_session()
    inst_list = []
    for cls_i in list_of_classes:
        repr_cls_i = with_polymorphic(cls_i, '*')
        for inst_i in session_handler.active_session.query(repr_cls_i).options(immediateload('*')).all():
            inst_list.append(inst_i)
    session_handler.active_session.expunge_all() # That's why we try to close session on start
    for inst_i in inst_list:
        make_transient(inst_i)
    return inst_list


app = QtGui.QApplication(sys.argv)

old_conn, ok1 = QtGui.QInputDialog.getText(None, 'Input old connection string', 'old_conn:')
new_conn, ok2 = QtGui.QInputDialog.getText(None, 'Input new connection string', 'new_conn:')

logger = sc.build_migrate_logger()

# get rid of QString
old_conn = str(old_conn)
new_conn = str(new_conn)

if ok1 and ok2:

    # Read all instances

    engine_old = create_engine(old_conn, echo=0, encoding=encoding_old)
    the_session_handler_old = c_session_handler(sessionmaker(bind=engine_old))

    engine_new = create_engine(new_conn, echo=0, encoding=encoding_new)
    the_session_handler_new = c_session_handler(sessionmaker(bind=engine_new))

    dbclasses = db_main.BASE.__subclasses__()

    cloned_instances = read_and_expunge(dbclasses, the_session_handler_old)
    the_session_handler_old.close_session()

    # A problem with hashtag to crm-record link.. Print it

    # for inst_i in cloned_instances:
    #     if inst_i.__class__.__name__ == 'c_crm_record':
    #         for ht_i in inst_i.hashtags:


    # Read these instances to new DB

    cur_class_name = ''
    last_class_name = None
    c = 0

    for inst_i in cloned_instances:
        cur_class_name = inst_i.__class__.__name__
        if last_class_name is None:
            last_class_name = cur_class_name

        if cur_class_name != last_class_name:
            logger.info('mapped ' + str(c) + ' instances of ' + last_class_name)
            last_class_name = cur_class_name
            c = 0

        the_session_handler_new.merge_object_to_session(inst_i)
        c += 1

    # commit new records

    the_session_handler_new.commit_and_close_session()






