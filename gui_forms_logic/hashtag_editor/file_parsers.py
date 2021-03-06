# -*- coding: utf-8 -*-
'''
    Module handles file -> HTML transformation
    (applied in text editor for notes)
'''

import os
import re
import db_main # helps to autotag e-mails


def mime_file_to_html(file_qurl):
    # Read dropped file and try to convert it to HTML
    # Most useful for .eml files (e-mails from Thunderbird)
    if file_qurl.isLocalFile() and not file_qurl.isEmpty():
        file_full_path = unicode(file_qurl.toLocalFile())
        filename, file_extension = os.path.splitext(file_full_path)
        if file_extension == '.eml':
            return _do_file(eml_file_to_html, file_full_path)
        elif file_extension == '.pdf':
            return _do_file(pdf_file_to_html, file_full_path)
        elif file_extension == '.docx':
            return _do_file(docx_file_to_html, file_full_path)
        elif file_extension == '.doc':
            return _do_file(doc_file_to_html, file_full_path)
        elif file_extension == '.odt':
            return _do_file(odt_file_to_html, file_full_path)
        elif file_extension == '.txt' or file_extension == '.html':
            return _do_file(txt_file_to_html, file_full_path)


def _do_file(func, file_full_path):
    text = func(file_full_path)
    #try:
    #    text = func(file_full_path)
    #except:
    #    text = u"ОШИБКА ОБРАБОТКИ ФАЙЛА\n"
    return text

##################
# .EML
##################

def eml_file_to_html(file_path):
    import pyzmail
    #f = codecs.open(file_path, 'r', 'utf-8')
    f = open(file_path)
    msg = pyzmail.message_from_file(f)
    full_text = u''
    # Adding date / from / to
    full_text += u'Письмо:'
    full_text += u"<b>" + _clean_email_subject(msg.get_subject()) + u"</b>" + u"<br>"

    addresses_from = msg.get_addresses('from')
    addresses_to = msg.get_addresses('to')
    addresses_cc = msg.get_addresses('cc')


    all_addresses = []

    for name_alias, email_address in addresses_from:
        full_text += name_alias + u" "
        all_addresses += [email_address]
    full_text += u" -> "
    for name_alias, email_address in addresses_to:
        full_text += name_alias + u", "
        all_addresses += [email_address]
    for name_alias, email_address in addresses_cc:
        full_text += name_alias + u", "
        all_addresses += [email_address]


    full_text += u"<br><br>"

    main_mail_part = msg.text_part
    if main_mail_part is None:
        main_mail_part = msg.html_part
    payload, used_charset = pyzmail.decode_text(main_mail_part.get_payload(), main_mail_part.charset, 'utf-8')
    full_text += _slice_email(payload)

    full_text += u"<br>"
    tag_list = _tags_from_addresses(all_addresses)
    for t_i in tag_list:
        full_text += t_i + u" "

    return full_text

def _clean_email_subject(subject_text):
    # cleans "RE", "FW" e.t.c. in a simple way
    ans = re.split(r":|;|/|,", subject_text)
    return ans[len(ans)-1]

def _slice_email(email_text):
    # return the first part of some long e-mail
    exp = ur"Kind regards|Best regards|С уважением|--|Met vriendelijke|Thanks and regards|Sent from"
    ans = re.split(exp, email_text, flags=re.IGNORECASE)
    return ans[0]

def _tags_from_addresses(email_addresses):
    # search for e-mails and returns #company_name
    contacts = []
    for add_i in email_addresses:
        contacts += db_main.get_contacts_by_email(unicode(add_i))
    companies = []
    for c_i in contacts:
        cp_i = c_i.company
        if not(cp_i in companies):
            companies += [cp_i]
    tags = []
    for cp_i in companies:
        tags += [cp_i.hashtag_name()]
    return tags

##################
# .PDF
##################

def pdf_file_to_html(file_path):
    # Nice idea for images:
    # http://www.danvk.org/2015/01/09/extracting-text-from-an-image-using-ocropus.html
    # FIXME: not working with russian characters
    # from http://stackoverflow.com/questions/26748788/extraction-of-text-from-pdf-with-pdfminer-gives-multiple-copies/26766684#26766684
    from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
    from pdfminer.converter import TextConverter
    from pdfminer.layout import LAParams
    from pdfminer.pdfpage import PDFPage
    from cStringIO import StringIO
    from BeautifulSoup import BeautifulSoup

    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    fp = file(file_path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos=set()
    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages,password=password,caching=caching, check_extractable=True):

        interpreter.process_page(page)

    unicode_soup = BeautifulSoup(retstr.getvalue())
    text = unicode_soup.getString()

    fp.close()
    device.close()
    retstr.close()
    return text

##################
# .DOC .DOCX
##################

def docx_file_to_html(file_path):
    # Would it work with .doc ?
    from pydocx import PyDocX
    text = PyDocX.to_html(file_path)
    return text

def doc_file_to_html(file_path):
    # Would it work with .doc ?
    # from pydocx import PyDocX
    # text = PyDocX.to_html(file_path)
    # return text
    return "I do not yet know how to import .doc - try .docx"

##################
# .ODT
##################

def odt_file_to_html(file_path):
    return "I do not yet know how to import .odt - try .docx"

##################
# .TXT .HTML
##################

def txt_file_to_html(file_path):
    from BeautifulSoup import BeautifulSoup # splendid !
    import codecs # not sure if it works
    f = codecs.open(file_path, 'r')
    soup = BeautifulSoup(f.read())
    text = soup.getString()
    # soup.originalEncoding # in case I need it later..
    return text
