# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore
import re
import html_prettify

class gui_HashtagCompleter(QtGui.QCompleter):
    def __init__(self, list_of_hashtags, parent=None):
        self.data_model = gui_hashtag_completing_model(list_of_hashtags, parent)

        self.data_model_proxy = QtGui.QSortFilterProxyModel()
        self.data_model_proxy.setSourceModel(self.data_model)
        self.data_model_proxy.setDynamicSortFilter(True)
        self.data_model_proxy.setFilterKeyColumn(0)
        self.data_model_proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.data_model_proxy.setFilterRole(55) #Не работает
        # TODO: придумать regexp для нормальной фильтрации
        #a_reg_exp = QtCore.QRegExp("", QtCore.Qt.CaseInsensitive)
        #self.data_model_proxy.setFilterRegExp(a_reg_exp)
        super(gui_HashtagCompleter, self).__init__(self.data_model_proxy, parent)

        self.setCompletionMode(QtGui.QCompleter.PopupCompletion)
        self.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.setMaxVisibleItems(20) #Надо же как-то ограничить

    # def update(self, completionText):
    #     # filtered = self.stringlist.filter(completionText,Qt.CaseInsensitive)
    #     self.model().setFilter(completionText)
    #     return self.model().rowCount()

# class gui_special_55_filter(QtGui.QSortFilterProxyModel):
#     def filterRole(self):
#         return 55

class gui_hashtag_completing_model(QtCore.QAbstractListModel):
    # Оказывается, есть стандартная модель QStringListModel
    def __init__(self, list_of_hashtags, parent = None):
        QtCore.QAbstractListModel.__init__(self, parent)
        self.my_list = list_of_hashtags

    def rowCount(self, parent):
        return len(self.my_list)

    def columnCount(self, parent):
        return 1

    def data(self, index, role):
        hashtag_text = self.my_list[index.row()]
        if role in [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole]:
            return hashtag_text
        if role == 55: #Фильтр - возвращаем ему слово без символа #, чтобы можно было проверить любое слово
            # TODO не работает поиск по слову без хештега... Роль не заходит..
            return hashtag_text[1:]

class gui_EditTextRecord(QtGui.QTextEdit):
    # Автозаполнения и предложения по вводу
    def __init__(self, parent=None):
        super(gui_EditTextRecord, self).__init__(parent)
        self.completer = None
        self.moveCursor(QtGui.QTextCursor.End)

    def refresh_hash_completion(self, list_of_hashtags):
        if self.completer is not None:  #если смена потребуется
            self.disconnect(self.completer, QtCore.SIGNAL("activated(const QString&)"), self.insert_completion)
        completer = gui_HashtagCompleter(list_of_hashtags, self)
        completer.setWidget(self) #Do I need this?
        self.completer = completer
        self.connect(self.completer, QtCore.SIGNAL("activated(const QString&)"), self.insert_completion)

    def select_last_word_or_hashtag(self):
        #Стандартный механизм игнорит символ "#" в начале слова.
        tc = self.textCursor()
        # Выделяем последнее слово + один символ слева
        tc.movePosition(QtGui.QTextCursor.StartOfWord, QtGui.QTextCursor.MoveAnchor)
        tc.movePosition(QtGui.QTextCursor.Left, QtGui.QTextCursor.MoveAnchor)
        tc.movePosition(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor)
        tc.movePosition(QtGui.QTextCursor.EndOfWord, QtGui.QTextCursor.KeepAnchor)
        a_wrd = tc.selectedText()
        if a_wrd.left(1) <> QtCore.QString("#"): #Если не хештег, то пользуемся стандартным подоходом по выделению слова
            tc.select(QtGui.QTextCursor.WordUnderCursor)
            a_wrd = tc.selectedText()
        return a_wrd, tc

    def insert_completion(self, completion):
        a_wrd, tc = self.select_last_word_or_hashtag()
        tc.insertText(completion)
        self.setTextCursor(tc)

    def get_word_context(self):
        a_wrd, tc = self.select_last_word_or_hashtag()
        return a_wrd

    def canInsertFromMimeData(self, source):
        return super(gui_EditTextRecord, self).canInsertFromMimeData(source)

    def insertFromMimeData(self, source):
        # Чистим HTML перед вставкой
        if source.hasHtml():
            desired_html = QtCore.QString(html_prettify.safe_html(source.html()))
            source = None
            new_source = QtCore.QMimeData()
            new_source.setHtml(desired_html)
            super(gui_EditTextRecord, self).insertFromMimeData(new_source)
        else:
            super(gui_EditTextRecord, self).insertFromMimeData(source)


    def focusInEvent(self, event):
        if self.completer is not None:
            self.completer.setWidget(self)
        QtGui.QTextEdit.focusInEvent(self, event)

    def keyPressEvent(self, event):
        # Каждый раз при вводе символа проверяем, не содержится ли в хештегах такое
        # Highlighter работает отдельно.. Хм..
        if self.completer is not None and self.completer.popup().isVisible():
            if event.key() in (QtCore.Qt.Key_Enter,
                               QtCore.Qt.Key_Return,
                               QtCore.Qt.Key_Escape,
                               QtCore.Qt.Key_Tab,
                               QtCore.Qt.Key_Backtab):
                event.ignore()
                return
        # ## has ctrl-E been pressed??
        isShortcut = (event.modifiers() == QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_E)
        if (self.completer is not None or not isShortcut):
           QtGui.QTextEdit.keyPressEvent(self, event)

        # ## ctrl or shift key on it's own??
        ctrlOrShift = event.modifiers() in (QtCore.Qt.ControlModifier, QtCore.Qt.ShiftModifier)
        if ctrlOrShift and event.text().isEmpty():
           # ctrl or shift key on it's own
           return
        hasModifier = ((event.modifiers() != QtCore.Qt.NoModifier) and not ctrlOrShift)

        comp_prefix = self.get_word_context()

        if comp_prefix is None:
            return
        eow = QtCore.QString(r"~!@$%^&*()_+{}|:\"<>?,./;'[]\-=") #end of word

        if not isShortcut and (hasModifier or event.text().isEmpty() or comp_prefix.length() < 2 or eow.contains(event.text().right(1))):
            self.completer.popup().hide()
            return

        if (comp_prefix != self.completer.completionPrefix()):
            self.completer.setCompletionPrefix(comp_prefix)
            popup = self.completer.popup()
            popup.setCurrentIndex(self.completer.completionModel().index(0,0))

        cr = self.cursorRect()
        cr.setWidth(self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(cr) ## popup it up!

if __name__ == "__main__":

    app = QtGui.QApplication([])
    test_hashtags = [ur"#Инкаб", u"#МКФ", u"#Фуджикура", u"#Офер", u"#Бюджет", u"#ЗВК", u"#Longvision", u"#SteelTape",
                     u"#Вяхорев", u"#Unigel", u"#Unigel500NA", u"#Unigel128FN", u"#Lantor3E5410"]
    te = gui_EditTextRecord()
    te.refresh_hash_completion(test_hashtags)
    te.show()
    app.exec_()