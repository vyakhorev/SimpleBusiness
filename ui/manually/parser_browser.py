# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore
import re

class gui_ParsingBrowser(QtGui.QTextBrowser):
    def setSource(self, some_url):
        # Обработка клика по ссылке
        print some_url