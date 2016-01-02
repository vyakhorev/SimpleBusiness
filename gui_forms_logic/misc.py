from PyQt4 import QtCore, QtGui

# import threading
#
# def send_background_email_to_group(a_subj, a_body):
#     # TODO: do I have to clean this thread?..
#     try:
#         utils.do_send_bot_email([user_group_email], a_subj, a_body)
#     except:
#         print "Unable to send e-mail to " + user_group_email
#         print gl_shared.traceback.format_exc()
#
# def try_send_email_about_new_record(new_crm_rec):
#     subj = u"[INT-news][%s] %s [Theme: %s]"%(user_name,new_crm_rec.headline, new_crm_rec.hashtags_string)
#     body = new_crm_rec.long_html_text
#     t_email = threading.Thread(target=send_background_email_to_group, args=(subj, body))
#     t_email.start()

def qtdate_unpack(a_qdate):
    return a_qdate.toPyDate()

def qtdate_pack(a_datetime):
    return QtCore.QDate(a_datetime.year, a_datetime.month, a_datetime.day)