# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui

import db_main
import datetime
import utils

from ui.ui_DialogCrm_EditSimpleRecord import Ui_DialogCrm_EditSimpleRecord

from ui.manually.popup_text_editor import gui_EditTextRecord
from ui.manually.table import ui_EditorHtmlTableSettings
from ui.manually.tag_lighter import ui_TagHighlighter
#from ui.manually.parser_browser import

# TODO: keep ini file in one location..
import simple_locale
import gl_shared

unicode_codec = QtCore.QTextCodec.codecForName(simple_locale.ultimate_encoding)

cnf = gl_shared.ConfigParser.ConfigParser()
cnf.read('.\__secret\main.ini')
user_name = unicode(cnf.get("UserConfig", "UserName").decode("cp1251"))
is_user_admin = unicode(cnf.getboolean("UserConfig", "IsAdmin"))
user_email = cnf.get("UserConfig", "PersonalEmail").decode("cp1251")
user_group_email = cnf.get("UserConfig", "GroupEmail").decode("cp1251")
cnf = None

class gui_DialogCrm_EditSimpleRecord(QtGui.QDialog, Ui_DialogCrm_EditSimpleRecord):
    def __init__(self, parent=None):
        super(gui_DialogCrm_EditSimpleRecord, self).__init__(parent)
        self.setupUi(self) #Метод от QtDesigner
        self.textEdit_longtext = gui_EditTextRecord(self)
        self.textEdit_longtext.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.horizontalLayout_for_textedit.addWidget(self.textEdit_longtext)

        # self.textEdit_longtext = QtGui.QTextEdit(DialogCrm_EditSimpleRecord)
        # self.textEdit_longtext.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        # self.textEdit_longtext.setObjectName(_fromUtf8("textEdit_longtext"))
        # self.verticalLayout.addWidget(self.textEdit_longtext)

        self.connect(self.pushButton_bulletList, QtCore.SIGNAL("clicked()"), self.editor_bulletList)
        self.connect(self.pushButton_numberList, QtCore.SIGNAL("clicked()"), self.editor_numberList)
        self.connect(self.pushButton_bold, QtCore.SIGNAL("clicked()"), self.editor_bold)
        self.connect(self.pushButton_italic, QtCore.SIGNAL("clicked()"), self.editor_italic)
        self.connect(self.pushButton_underline, QtCore.SIGNAL("clicked()"), self.editor_underline)
        self.connect(self.pushButton_undo, QtCore.SIGNAL("clicked()"), self.textEdit_longtext.undo)
        self.connect(self.pushButton_redo, QtCore.SIGNAL("clicked()"), self.textEdit_longtext.redo)
        self.connect(self.pushButton_print, QtCore.SIGNAL("clicked()"), self.editor_print_preview)
        self.table_dialog = ui_EditorHtmlTableSettings(self, self.textEdit_longtext)
        self.connect(self.pushButton_table, QtCore.SIGNAL("clicked()"), self.table_dialog.show)
        self.highlighter = ui_TagHighlighter(self.textEdit_longtext, "Classic")
        # We need our own context menu for tables
        self.textEdit_longtext.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.textEdit_longtext.customContextMenuRequested.connect(self.context)

    def editor_bold(self):
        if self.textEdit_longtext.fontWeight() == QtGui.QFont.Bold:
            self.textEdit_longtext.setFontWeight(QtGui.QFont.Normal)
        else:
            self.textEdit_longtext.setFontWeight(QtGui.QFont.Bold)

    def editor_italic(self):
        state = self.textEdit_longtext.fontItalic()
        self.textEdit_longtext.setFontItalic(not state)

    def editor_underline(self):
        state = self.textEdit_longtext.fontUnderline()
        self.textEdit_longtext.setFontUnderline(not state)

    def editor_bulletList(self):
        cursor = self.textEdit_longtext.textCursor()
        cursor.insertList(QtGui.QTextListFormat.ListDisc)

    def editor_numberList(self):
        cursor = self.textEdit_longtext.textCursor()
        cursor.insertList(QtGui.QTextListFormat.ListDecimal)

    def editor_print_preview(self):
        preview = QtGui.QPrintPreviewDialog()
        preview.paintRequested.connect(lambda p: self.textEdit_longtext.print_(p))
        preview.exec_()

    def context(self,pos):
        cursor = self.textEdit_longtext.textCursor()
        # Grab the current table, if there is one
        table = cursor.currentTable()
        # Above will return 0 if there is no current table, in which case
        # we call the normal context menu. If there is a table, we create
        # our own context menu specific to table interaction
        if table:
            menu = QtGui.QMenu(self)
            appendRowAction = QtGui.QAction(u"Добавить строку",self)
            appendRowAction.triggered.connect(lambda: table.appendRows(1))
            appendColAction = QtGui.QAction(u"Добавить столбец",self)
            appendColAction.triggered.connect(lambda: table.appendColumns(1))
            removeRowAction = QtGui.QAction(u"Удалить строку",self)
            removeRowAction.triggered.connect(self.removeRow)
            removeColAction = QtGui.QAction(u"Удалить столбце",self)
            removeColAction.triggered.connect(self.removeCol)
            insertRowAction = QtGui.QAction(u"Вставить строку",self)
            insertRowAction.triggered.connect(self.insertRow)
            insertColAction = QtGui.QAction(u"Вставить столбец",self)
            insertColAction.triggered.connect(self.insertCol)
            mergeAction = QtGui.QAction(u"Объединить ячейки",self)
            mergeAction.triggered.connect(lambda: table.mergeCells(cursor))
            # Only allow merging if there is a selection
            if not cursor.hasSelection():
                mergeAction.setEnabled(False)
            splitAction = QtGui.QAction(u"Разделить ячейки",self)
            cell = table.cellAt(cursor)
            # Only allow splitting if the current cell is larger
            # than a normal cell
            if cell.rowSpan() > 1 or cell.columnSpan() > 1:
                splitAction.triggered.connect(lambda: table.splitCell(cell.row(),cell.column(),1,1))
            else:
                splitAction.setEnabled(False)
            menu.addAction(appendRowAction)
            menu.addAction(appendColAction)
            menu.addSeparator()
            menu.addAction(removeRowAction)
            menu.addAction(removeColAction)
            menu.addSeparator()
            menu.addAction(insertRowAction)
            menu.addAction(insertColAction)
            menu.addSeparator()
            menu.addAction(mergeAction)
            menu.addAction(splitAction)
            # Convert the widget coordinates into global coordinates
            pos = self.mapToGlobal(pos)
            # Move the menu to the new position
            menu.move(pos)
            menu.show()
        else:
            event = QtGui.QContextMenuEvent(QtGui.QContextMenuEvent.Mouse,QtCore.QPoint())
            self.textEdit_longtext.contextMenuEvent(event)

    def removeRow(self):
        # Grab the cursor
        cursor = self.textEdit_longtext.textCursor()
        # Grab the current table (we assume there is one, since
        # this is checked before calling)
        table = cursor.currentTable()
        # Get the current cell
        cell = table.cellAt(cursor)
        # Delete the cell's row
        table.removeRows(cell.row(),1)

    def removeCol(self):
        # Grab the cursor
        cursor = self.textEdit_longtext.textCursor()
        # Grab the current table (we assume there is one, since
        # this is checked before calling)
        table = cursor.currentTable()
        # Get the current cell
        cell = table.cellAt(cursor)
        # Delete the cell's column
        table.removeColumns(cell.column(),1)

    def insertRow(self):
        # Grab the cursor
        cursor = self.textEdit_longtext.textCursor()
        # Grab the current table (we assume there is one, since
        # this is checked before calling)
        table = cursor.currentTable()
        # Get the current cell
        cell = table.cellAt(cursor)
        # Insert a new row at the cell's position
        table.insertRows(cell.row(),1)

    def insertCol(self):
        # Grab the cursor
        cursor = self.textEdit_longtext.textCursor()
        # Grab the current table (we assume there is one, since
        # this is checked before calling)
        table = cursor.currentTable()
        # Get the current cell
        cell = table.cellAt(cursor)
        # Insert a new row at the cell's position
        table.insertColumns(cell.column(),1)

    def clear_fonts(self):
        # TODO: тут нужно всё поправить + поднимать вызов по событию "вставка" в браузер.
        readable_font = QtGui.QFont()
        readable_font.setPointSize(10)
        readable_font.setStyleHint(QtGui.QFont.Courier)
        self.textEdit_longtext.selectAll()
        self.textEdit_longtext.setCurrentFont(readable_font)

    def set_state_to_add_new(self, suggested_tags = None, text_template = "", header = ""):
        # self.record_entity создается перед закрытием с кнопкой "ОК"
        self.setWindowTitle(unicode(u"Создание заметки"))
        existing_hashtags = db_main.get_hashtags_text_list()
        self.highlighter.update_keywords(existing_hashtags)
        self.textEdit_longtext.refresh_hash_completion(existing_hashtags)
        self.my_mode = 0
        self.record_entity = None
        self.preset_tags = []
        self.label_date_added.setText(datetime.date.today().strftime("%Y %B %d (%A)")) # перед "ОК" всё равно меняется
        self.lineEdit_headline.setText(header)
        s = ""
        if suggested_tags is None:
            suggested_tags = []
        suggested_tags.append(user_name)
        for h_i in suggested_tags:
            s += "#" + h_i + ", "
        if len(suggested_tags) > 0: s += "<br><br>"
        s += text_template
        self.textEdit_longtext.setHtml(s)
        self.clear_fonts()

    def set_state_to_edit(self, record_entity):
        # self.record_entity используется только для заполнения формы и меняется только перед закрытием если "ОК"
        self.setWindowTitle(unicode(u"Изменение заметки"))
        self.clear_fonts()
        existing_hashtags = db_main.get_hashtags_text_list()
        self.highlighter.update_keywords(existing_hashtags)
        self.textEdit_longtext.refresh_hash_completion(existing_hashtags)
        self.my_mode = 1
        self.record_entity = record_entity
        self.preset_tags = self.record_entity.get_tags_text()
        self.label_date_added.setText(self.record_entity.date_added.strftime("%Y.%m.%d"))
        self.lineEdit_headline.setText(self.record_entity.headline)
        self.textEdit_longtext.setHtml(self.record_entity.long_html_text)
        self.clear_fonts()

    def accept(self):
        self.clear_fonts()
        is_ok = True
        if is_ok:
            if self.lineEdit_headline.text() == "":
                QtGui.QMessageBox.information(self,unicode(u"Ошибка ввода"),
                                              unicode(u"Добавьте заголовок"))
                self.lineEdit_headline.setFocus()
                is_ok = False
        tag_list = utils.parse_hashtags(unicode(self.textEdit_longtext.toPlainText()))
        if is_ok:  #Проверяем те тэги, что были предначертаны - от них можно отказаться
            for ht_i in self.preset_tags:
                if not(ht_i in tag_list):
                    ans = QtGui.QMessageBox.question(self,unicode(u"Пропущен хэш-тэг"), unicode(u'Добавить #' + ht_i + u" ?"),
                                                     QtGui.QMessageBox.Yes, QtGui.QMessageBox.No,QtGui.QMessageBox.Cancel)
                    if ans == QtGui.QMessageBox.Yes:
                        self.textEdit_longtext.insertHtml(ht_i)
                        tag_list += [ht_i]
                    elif ans == QtGui.QMessageBox.No: #Ну нет так нет. Значит, лишний был.
                        pass
                    elif ans == QtGui.QMessageBox.Cancel:
                        is_ok = False
                        break
        if is_ok:  #Но всё-таки что-нибудь да должно быть
            if len(tag_list) == 0:
                is_ok = False
                QtGui.QMessageBox.information(self,unicode(u"Ошибка ввода"),
                                              unicode(u"В тексте нет ни одного хэш-тэга - добавьте"))
        if is_ok:  #Проверяем теги на существование в базе
            record_tags = db_main.get_hashtags_from_names(tag_list)
            #print record_tags  #TODO: проверить что тут none нету
            found_names = [rec_i.text for rec_i in record_tags]
            not_found = []
            for ht_i in tag_list:
                if not(ht_i in found_names):
                    not_found += [ht_i]
            for ht_i in not_found:
                msg = unicode(u'Впервые вижу тэг #' + ht_i + u' - уверены, что не опечатались?')
                ans = QtGui.QMessageBox.question(self,unicode(u'Новый хэш-тэг'), unicode(msg),
                                                 QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
                if ans == QtGui.QMessageBox.Yes:
                    #Создаем новый тэг
                    new_h = db_main.c_hastag(text = ht_i)
                    record_tags += [new_h]
                elif ans == QtGui.QMessageBox.No:
                    is_ok = False
                    break
        if is_ok:
            # Собираем переменную и в базу
            if self.my_mode == 0: #Новый
                self.record_entity = db_main.c_crm_record()
                self.record_entity.date_added = datetime.date.today()
            self.record_entity.match_with_tags(record_tags)
            self.record_entity.fix_hashtag_text() #подобранные тэги записываются в строку для быстрого доступа
            self.record_entity.long_html_text = unicode(self.textEdit_longtext.toHtml(),encoding='utf-8')
            self.record_entity.headline = unicode(self.lineEdit_headline.text(),encoding='utf-8')
            super(gui_DialogCrm_EditSimpleRecord, self).accept()

    def reject(self):
        super(gui_DialogCrm_EditSimpleRecord, self).reject()

    def run_dialog(self):
        user_decision = self.exec_()  #0 или 1
        if user_decision == QtGui.QDialog.Accepted:
            return [user_decision, self.record_entity]
        elif user_decision == QtGui.QDialog.Rejected:
            return [user_decision, None]
