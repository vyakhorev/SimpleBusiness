# -*- coding: utf-8 -*-

# from PyQt4 import QtCore, QtGui
import db_main
# import sys

# readable_font = QtGui.QFont()
# readable_font.setPointSize(10)
# readable_font.setStyleHint(QtGui.QFont.Courier)

# app = QtGui.QApplication(sys.argv)
# a_textEdit = QtGui.QTextEdit()

# for rec_i in db_main.the_session_handler.get_all_objects_list_iter(db_main.c_crm_record):
#     # a_textEdit.setHtml(rec_i.long_html_text)
#     # a_textEdit.selectAll()
#     # a_textEdit.setCurrentFont(readable_font)
#     # rec_i.long_html_text = unicode(a_textEdit.toHtml())
#     if rec_i.rec_id in [1125, 1124, 1123]:  #Примеры ужасного формата и скриптов
#         bad_html = rec_i.long_html_text
#         good_html = unicode(html_prettify.safe_html(bad_html)).encode("utf-8")
#         print good_html
#         f = open('test_'+str(rec_i.rec_id)+".html", 'w')
#         f.write(good_html)
#         f.close()
#         #rec_i.long_html_text = unicode(utils.prettify_html_with_soup(rec_i.long_html_text))

from ui.manually import html_prettify

for rec_i in db_main.the_session_handler.get_all_objects_list_iter(db_main.c_crm_record):
    bad_html = rec_i.long_html_text
    good_html = unicode(html_prettify.safe_html(bad_html))
    rec_i.long_html_text = good_html
db_main.the_session_handler.commit_session()
